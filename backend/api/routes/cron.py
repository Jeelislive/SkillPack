"""
Vercel Cron Job handlers.

Secured with CRON_SECRET env var.
Vercel automatically sends: Authorization: Bearer <CRON_SECRET>

Jobs:
  GET /api/cron/skill-discovery  - every 1h: fetch & ingest new unique skills from GitHub
  GET /api/cron/bundle-curator   - every 3h: AI-curate 10 bundles (least-recently-updated first)
"""

import json
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException
from config import get_settings

router = APIRouter()

# Rotating GitHub queries - advances each hour via UTC hour mod
_QUERIES = [
    "filename:SKILL.md",
    "filename:skill.md path:.claude/skills",
    "topic:agent-skills",
    "topic:claude-skills",
    "filename:SKILL.md path:.claude",
    "filename:SKILL.md language:Markdown",
    "topic:claude-code-skills",
    "filename:SKILL.md stars:>5",
    "path:.claude/skills extension:md",
    "topic:ai-skills",
    "filename:SKILL.md topic:mcp",
    "topic:cursor-rules",
]


def _verify(authorization: str | None):
    settings = get_settings()
    secret = settings.cron_secret
    if secret and authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── CRON 1: Hourly Skill Discovery ──────────────────────────────────────────

@router.get("/skill-discovery")
async def cron_skill_discovery(authorization: str | None = Header(None)):
    """Fetch new unique skills from GitHub and ingest them."""
    _verify(authorization)
    start = datetime.now(timezone.utc)

    try:
        from db.database import SyncSessionLocal
        from db.models import Skill, SkillIndex
        from crawlers.github_crawler import GitHubCrawler
        from pipeline.tagger import SkillTagger
        from db.ingestion import ingest_crawl_results
        import httpx

        settings = get_settings()

        # Load all existing slugs for dedup
        db = SyncSessionLocal()
        try:
            existing_slugs = (
                set(r[0] for r in db.query(Skill.slug).all()) |
                set(r[0] for r in db.query(SkillIndex.slug).all())
            )
        finally:
            db.close()

        # Rotate query by UTC hour so each run tries a different search
        query = _QUERIES[datetime.now(timezone.utc).hour % len(_QUERIES)]

        tokens = [settings.github_token]
        if settings.github_token_2:
            tokens.append(settings.github_token_2)

        crawler = GitHubCrawler(tokens=tokens)

        async with httpx.AsyncClient(timeout=30) as client:
            raw = await crawler.crawl_query(client, query, existing_slugs, max_pages=2)

        if not raw:
            return {
                "status": "ok", "query": query,
                "found": 0, "inserted": 0,
                "elapsed_s": _elapsed(start),
            }

        enriched = await crawler.fetch_skill_contents(raw, existing_slugs)
        valid = [s for s in enriched if s.get("raw_content")]

        if not valid:
            return {
                "status": "ok", "query": query,
                "found": len(raw), "with_content": 0, "inserted": 0,
                "elapsed_s": _elapsed(start),
            }

        tagger = SkillTagger()
        tagged = tagger.tag_batch_fast(valid)
        tier1 = [s for s in tagged if s.get("quality_score", 0) >= 4 and s.get("raw_content")]
        tier2 = [s for s in tagged if not (s.get("quality_score", 0) >= 4 and s.get("raw_content"))]

        db = SyncSessionLocal()
        try:
            stats = ingest_crawl_results(db, tier1, tier2, "github")
        finally:
            db.close()

        return {
            "status": "ok",
            "query": query,
            "found": len(raw),
            "with_content": len(valid),
            "tier1": len(tier1),
            "tier2": len(tier2),
            "inserted": stats.get("inserted", 0),
            "elapsed_s": _elapsed(start),
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "error": str(e), "elapsed_s": _elapsed(start)}


# ── CRON 2: 3-Hour Bundle Curator ───────────────────────────────────────────

@router.get("/bundle-curator")
async def cron_bundle_curator(authorization: str | None = Header(None)):
    """AI-curate the 10 least-recently-updated bundles."""
    _verify(authorization)
    start = datetime.now(timezone.utc)

    try:
        from db.database import SyncSessionLocal
        from db.models import Bundle

        settings = get_settings()
        db = SyncSessionLocal()

        try:
            # Always process the 10 bundles that were updated least recently
            bundles = (
                db.query(Bundle)
                .filter(Bundle.is_active == True)
                .order_by(Bundle.updated_at.asc())
                .limit(10)
                .all()
            )
            bundle_count = len(bundles)
        finally:
            db.close()

        updated_total = 0
        for bundle in bundles:
            try:
                db = SyncSessionLocal()
                try:
                    b = db.query(Bundle).filter_by(id=bundle.id).first()
                    if b:
                        updated = await _curate_bundle(db, b, settings)
                        if updated:
                            updated_total += 1
                finally:
                    db.close()
            except Exception as e:
                print(f"[cron] Bundle '{bundle.slug}' error: {e}")
                continue

        return {
            "status": "ok",
            "processed": bundle_count,
            "updated": updated_total,
            "elapsed_s": _elapsed(start),
        }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "error": str(e), "elapsed_s": _elapsed(start)}


async def _curate_bundle(db, bundle, settings) -> bool:
    from db.models import Skill, BundleCommand
    from pipeline.install_generator import InstallGenerator
    import httpx

    install_gen = InstallGenerator()

    # Load current skills
    current_skills = []
    if bundle.skill_ids:
        current_skills = (
            db.query(Skill)
            .filter(Skill.id.in_(bundle.skill_ids), Skill.is_active == True)
            .all()
        )

    if not current_skills:
        bundle.updated_at = datetime.now(timezone.utc)
        db.commit()
        return False

    current_ids = {s.id for s in current_skills}

    # Category filter for candidates
    if bundle.category == "fullstack":
        cat_filter = Skill.primary_category.in_(["frontend", "backend", "database", "fullstack"])
    elif bundle.category in ("other", "api-design"):
        cat_filter = None
    else:
        cat_filter = Skill.primary_category == bundle.category

    cand_q = db.query(Skill).filter(
        Skill.is_active == True,
        Skill.tier == 1,
        Skill.quality_score >= 3,
        ~Skill.id.in_(current_ids),
    )
    if cat_filter is not None:
        cand_q = cand_q.filter(cat_filter)

    candidates = (
        cand_q
        .order_by((Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc())
        .limit(30)
        .all()
    )

    def _s(skill):
        return {
            "slug": skill.slug,
            "name": skill.name,
            "description": (skill.description or "")[:100],
            "quality": round(float(skill.quality_score), 1),
            "tags": (skill.tags or [])[:6],
        }

    prompt = (
        f'Curate this AI agent skill bundle.\n\n'
        f'Bundle: "{bundle.name}" | Category: {bundle.category}\n'
        f'Description: {bundle.description}\n\n'
        f'CURRENT SKILLS ({len(current_skills)}):\n'
        f'{json.dumps([_s(s) for s in current_skills], indent=2)}\n\n'
        f'CANDIDATE NEW SKILLS ({len(candidates)}):\n'
        f'{json.dumps([_s(s) for s in candidates], indent=2)}\n\n'
        f'Return ONLY JSON:\n'
        f'{{"keep":[...slugs...],"remove":[...slugs...],"add":[...max 8 slugs...]}}\n'
        f'Rules: 20-30 skills total. Remove only clearly irrelevant. Add only genuine fits.'
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{settings.groq_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.1,
                },
            )
            if resp.status_code != 200:
                bundle.updated_at = datetime.now(timezone.utc)
                db.commit()
                return False

            content = resp.json()["choices"][0]["message"]["content"].strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)

    except Exception:
        bundle.updated_at = datetime.now(timezone.utc)
        db.commit()
        return False

    keep_slugs = set(result.get("keep", []))
    remove_slugs = set(result.get("remove", []))
    add_slugs = set(result.get("add", []))

    cand_by_slug = {s.slug: s for s in candidates}

    new_skills = [s for s in current_skills if s.slug in keep_slugs or s.slug not in remove_slugs]
    for slug in add_slugs:
        if slug in cand_by_slug and cand_by_slug[slug] not in new_skills:
            new_skills.append(cand_by_slug[slug])
    new_skills = new_skills[:30]
    new_ids = [s.id for s in new_skills]

    # Always update updated_at so this bundle moves to back of queue
    bundle.updated_at = datetime.now(timezone.utc)

    if set(new_ids) == set(bundle.skill_ids or []):
        db.commit()
        return False

    bundle.skill_ids = new_ids
    bundle.skill_count = len(new_ids)
    db.commit()

    db.query(BundleCommand).filter_by(bundle_id=bundle.id).delete()
    db.commit()
    for platform in ["claude_code", "cursor", "copilot", "continue", "universal"]:
        cmd = install_gen.generate(new_skills, platform, bundle.slug)
        db.add(BundleCommand(bundle_id=bundle.id, platform=platform, command=cmd))
    db.commit()

    return True


def _elapsed(start: datetime) -> float:
    return round((datetime.now(timezone.utc) - start).total_seconds(), 1)
