"""
SkillPack Scheduler
Runs background cron jobs using APScheduler.

Jobs:
  - Every 3h : AI bundle curator  - reviews every bundle, removes irrelevant skills,
                                    adds better-matching ones using Groq LLM
  - Every 1h : Skill discovery    - targeted GitHub search for new SKILL.md files
  - Every 6h : skills.sh refresh  - top-N leaderboard re-crawl
  - Daily 3am: Full crawl         - skills.sh + GitHub + bundle regen
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from rich import print

logger = logging.getLogger("skillpack.scheduler")

# ── Rotating GitHub queries for hourly discovery ──────────────────────────────
_HOURLY_QUERIES = [
    "filename:SKILL.md",
    "filename:skill.md path:.claude/skills",
    "topic:agent-skills",
    "topic:claude-skills",
    "filename:SKILL.md path:.claude",
    "filename:SKILL.md language:Markdown",
    "topic:claude-code-skills",
    "topic:ai-skills",
    "path:.claude/skills extension:md",
    "filename:SKILL.md stars:>5",
    "topic:cursor-rules filename:.cursorrules",
    "filename:SKILL.md topic:mcp",
]
_query_rotation_idx = 0   # advances each hourly run


# ═══════════════════════════════════════════════════════════════════════════════
# JOB 1 - AI Bundle Curator (every 3 hours)
# ═══════════════════════════════════════════════════════════════════════════════

async def job_ai_bundle_curator():
    """
    For every bundle in the DB:
      1. Load current skills + candidate skills (same category, not yet in bundle)
      2. Ask Groq LLM which to keep, which to remove, which candidates to add
      3. Update the bundle and regenerate its install commands
    """
    print("[bold blue]⏰ [AI Bundle Curator] Starting...[/bold blue]")
    try:
        from db.database import SyncSessionLocal
        from db.models import Bundle, Skill, BundleCommand
        from pipeline.install_generator import InstallGenerator
        from config import get_settings
        import httpx

        settings = get_settings()
        db = SyncSessionLocal()
        install_gen = InstallGenerator()

        try:
            bundles = db.query(Bundle).all()
            print(f"[blue]  Curating {len(bundles)} bundles with AI...[/blue]")
            updated_total = 0

            for bundle in bundles:
                try:
                    updated = await _curate_bundle_with_ai(
                        db, bundle, install_gen, settings, httpx
                    )
                    if updated:
                        updated_total += 1
                except Exception as e:
                    print(f"[yellow]  Bundle '{bundle.slug}' curation error: {e}[/yellow]")
                    continue

            print(f"[bold green]⏰ [AI Bundle Curator] Done - {updated_total}/{len(bundles)} bundles updated.[/bold green]")
        finally:
            db.close()

    except Exception as e:
        print(f"[red]⏰ [AI Bundle Curator] Fatal error: {e}[/red]")
        traceback.print_exc()


async def _curate_bundle_with_ai(db, bundle, install_gen, settings, httpx) -> bool:
    """
    AI-curate a single bundle. Returns True if the bundle was modified.
    """
    from db.models import Skill, BundleCommand
    from sqlalchemy import func, or_

    # ── Current skills ────────────────────────────────────────────────────────
    current_skills: list[Skill] = []
    if bundle.skill_ids:
        current_skills = (
            db.query(Skill)
            .filter(Skill.id.in_(bundle.skill_ids), Skill.is_active == True)
            .all()
        )

    if not current_skills:
        return False

    # ── Candidate skills (same category, NOT already in bundle, quality ≥ 3) ─
    current_ids = {s.id for s in current_skills}

    if bundle.category in ("other", "api-design", "fullstack"):
        cat_filter = None
    elif bundle.category == "fullstack":
        cat_filter = Skill.primary_category.in_(["frontend", "backend", "database", "fullstack"])
    else:
        cat_filter = Skill.primary_category == bundle.category

    cand_query = db.query(Skill).filter(
        Skill.is_active == True,
        Skill.tier == 1,
        Skill.quality_score >= 3,
        ~Skill.id.in_(current_ids),
    )
    if cat_filter is not None:
        cand_query = cand_query.filter(cat_filter)

    candidates: list[Skill] = (
        cand_query
        .order_by((Skill.quality_score * 0.6 + Skill.popularity_score * 0.4).desc())
        .limit(40)
        .all()
    )

    # ── Build prompt ──────────────────────────────────────────────────────────
    def skill_summary(s: Skill) -> dict:
        return {
            "slug": s.slug,
            "name": s.name,
            "description": (s.description or "")[:120],
            "quality": round(s.quality_score, 1),
            "tags": s.tags[:8] if s.tags else [],
        }

    prompt = f"""You are a senior engineer curating an AI agent skill bundle.

Bundle: "{bundle.name}"
Description: {bundle.description}
Category: {bundle.category}

CURRENT SKILLS ({len(current_skills)}):
{json.dumps([skill_summary(s) for s in current_skills], indent=2)}

CANDIDATE NEW SKILLS ({len(candidates)}) - not yet in bundle:
{json.dumps([skill_summary(s) for s in candidates], indent=2)}

Task: Return JSON with exactly these keys:
- "keep": list of slugs from CURRENT SKILLS that belong in this bundle
- "remove": list of slugs from CURRENT SKILLS that do NOT belong (wrong category, irrelevant, duplicate purpose)
- "add": list of slugs from CANDIDATE NEW SKILLS that should be added (max 10)

Rules:
- Bundle should have 20-30 skills total after changes
- Only remove skills that are clearly wrong category or irrelevant
- Only add candidates that genuinely fit this bundle's purpose
- Prefer higher quality_score skills
- Return ONLY valid JSON, no explanation

JSON:"""

    # ── Call Groq ─────────────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.groq_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.1,
                },
            )
            if resp.status_code != 200:
                return False

            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Extract JSON from response
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)

    except Exception as e:
        logger.debug(f"Groq call failed for bundle '{bundle.slug}': {e}")
        return False

    keep_slugs = set(result.get("keep", []))
    remove_slugs = set(result.get("remove", []))
    add_slugs = set(result.get("add", []))

    # ── Apply changes ─────────────────────────────────────────────────────────
    # Build slug→skill maps
    current_by_slug = {s.slug: s for s in current_skills}
    cand_by_slug    = {s.slug: s for s in candidates}

    new_skills: list[Skill] = []

    # Keep skills AI said to keep (or didn't explicitly remove)
    for s in current_skills:
        if s.slug in keep_slugs or s.slug not in remove_slugs:
            new_skills.append(s)

    # Add new candidates AI selected
    for slug in add_slugs:
        if slug in cand_by_slug and cand_by_slug[slug] not in new_skills:
            new_skills.append(cand_by_slug[slug])

    # Cap at 30
    new_skills = new_skills[:30]
    new_ids = [s.id for s in new_skills]

    # Check if anything changed
    if set(new_ids) == set(bundle.skill_ids or []):
        return False

    # Update bundle
    bundle.skill_ids   = new_ids
    bundle.skill_count = len(new_ids)
    bundle.updated_at  = datetime.now(timezone.utc)
    db.commit()

    # Regenerate commands
    db.query(BundleCommand).filter_by(bundle_id=bundle.id).delete()
    db.commit()
    platforms = ["claude_code", "cursor", "copilot", "continue", "universal"]
    for platform in platforms:
        cmd = install_gen.generate(new_skills, platform, bundle.slug)
        db.add(BundleCommand(bundle_id=bundle.id, platform=platform, command=cmd))
    db.commit()

    removed = len(remove_slugs & set(current_by_slug.keys()))
    added   = len(add_slugs & set(cand_by_slug.keys()))
    print(f"[green]  ✓ '{bundle.slug}': -{removed} +{added} → {len(new_ids)} skills[/green]")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# JOB 2 - Hourly Skill Discovery
# ═══════════════════════════════════════════════════════════════════════════════

async def job_hourly_skill_discovery():
    """Targeted GitHub search for new SKILL.md files (2-3 rotating queries per run)."""
    global _query_rotation_idx
    print("[bold blue]⏰ [Hourly Discovery] Starting...[/bold blue]")

    try:
        from db.database import SyncSessionLocal
        from db.models import Skill, SkillIndex
        from crawlers.github_crawler import GitHubCrawler
        from pipeline.tagger import SkillTagger
        from db.ingestion import ingest_crawl_results
        from config import get_settings
        import httpx

        settings = get_settings()
        db = SyncSessionLocal()
        try:
            existing_slugs = (
                set(r[0] for r in db.query(Skill.slug).all()) |
                set(r[0] for r in db.query(SkillIndex.slug).all())
            )
        finally:
            db.close()

        # Pick 3 rotating queries
        queries = [
            _HOURLY_QUERIES[(_query_rotation_idx + i) % len(_HOURLY_QUERIES)]
            for i in range(3)
        ]
        _query_rotation_idx = (_query_rotation_idx + 3) % len(_HOURLY_QUERIES)

        tokens = [settings.github_token]
        if settings.github_token_2:
            tokens.append(settings.github_token_2)

        crawler = GitHubCrawler(tokens=tokens)
        all_skills = []

        async with httpx.AsyncClient() as client:
            for query in queries:
                print(f"[blue]  Searching: {query}[/blue]")
                skills = await crawler.crawl_query(client, query, existing_slugs, max_pages=3)
                all_skills.extend(skills)

        if not all_skills:
            print("[yellow]⏰ [Hourly Discovery] No new skills found.[/yellow]")
            return

        # Fetch content
        enriched = await crawler.fetch_skill_contents(all_skills, existing_slugs)
        valid = [s for s in enriched if s.get("raw_content")]

        if not valid:
            print("[yellow]⏰ [Hourly Discovery] No skills with content.[/yellow]")
            return

        # Tag + ingest
        tagger = SkillTagger()
        tagged = tagger.tag_batch_fast(valid)
        tier1 = [s for s in tagged if s.get("quality_score", 0) >= 4 and s.get("raw_content")]
        tier2 = [s for s in tagged if not (s.get("quality_score", 0) >= 4 and s.get("raw_content"))]

        db = SyncSessionLocal()
        try:
            stats = ingest_crawl_results(db, tier1, tier2, "github")
        finally:
            db.close()

        print(f"[bold green]⏰ [Hourly Discovery] Done - +{stats['inserted']} new skills inserted.[/bold green]")

    except Exception as e:
        print(f"[red]⏰ [Hourly Discovery] Error: {e}[/red]")
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════════
# JOB 3 - Daily Full Crawl (3am UTC)
# ═══════════════════════════════════════════════════════════════════════════════

async def job_daily_full_crawl():
    """Full pipeline: skills.sh (top 5000) + GitHub (all queries) + bundle regen."""
    print("[bold blue]⏰ [Daily Full Crawl] Starting...[/bold blue]")
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from run_crawl import run_skills_sh, run_github, run_bundles
        await run_skills_sh()
        await run_github()
        run_bundles()
        print("[bold green]⏰ [Daily Full Crawl] Done.[/bold green]")
    except Exception as e:
        print(f"[red]⏰ [Daily Full Crawl] Error: {e}[/red]")
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduler bootstrap
# ═══════════════════════════════════════════════════════════════════════════════

_scheduler: AsyncIOScheduler | None = None


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # AI Bundle Curator - every 3 hours
    scheduler.add_job(
        job_ai_bundle_curator,
        trigger=IntervalTrigger(hours=3),
        id="ai_bundle_curator",
        name="AI Bundle Curator",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Hourly Skill Discovery
    scheduler.add_job(
        job_hourly_skill_discovery,
        trigger=IntervalTrigger(hours=1),
        id="hourly_discovery",
        name="Hourly Skill Discovery",
        replace_existing=True,
        misfire_grace_time=120,
    )

    # Daily Full Crawl at 3am UTC
    scheduler.add_job(
        job_daily_full_crawl,
        trigger=CronTrigger(hour=3, minute=0, timezone="UTC"),
        id="daily_full_crawl",
        name="Daily Full Crawl",
        replace_existing=True,
        misfire_grace_time=600,
    )

    return scheduler


def start_scheduler():
    global _scheduler
    _scheduler = create_scheduler()
    _scheduler.start()
    print("[bold green]Scheduler started:[/bold green]")
    for job in _scheduler.get_jobs():
        print(f"  • {job.name} - next run: {job.next_run_time}")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[yellow]Scheduler stopped.[/yellow]")


def get_scheduler_status() -> dict:
    """Return current scheduler status for the API."""
    if not _scheduler:
        return {"running": False, "jobs": []}
    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in _scheduler.get_jobs()
        ],
    }
