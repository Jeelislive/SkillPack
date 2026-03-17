"""
Saves crawled + tagged skills into the database.
Handles upserts (insert new, update changed, skip unchanged).
Uses bulk operations - one commit per batch, not per skill.
"""

import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from rich import print
from db.models import Skill, SkillIndex, Source, CrawlJob


def get_or_create_source(db: Session, name: str) -> Source:
    source = db.query(Source).filter_by(name=name).first()
    if not source:
        source = Source(name=name, display_name=name.replace("_", " ").title(), crawl_strategy="scrape")
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def compute_install_command(slug: str, platforms: list[str]) -> str:
    """Generate install command based on primary platform."""
    if "cursor" in platforms:
        return f"# Add to .cursorrules from https://github.com/{slug}"
    return f"npx skills add {slug}"


def ingest_crawl_results(
    db: Session,
    tier1_skills: list[dict],
    tier2_skills: list[dict],
    source_name: str,
    job: CrawlJob | None = None,
) -> dict:
    """
    Persist all crawl results in bulk.
    Fetches existing slugs once, then inserts/updates in batches.
    Returns summary stats.
    """
    source = get_or_create_source(db, source_name)
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    print(f"[blue]Ingesting {len(tier1_skills)} tier-1 and {len(tier2_skills)} tier-2 skills...[/blue]")

    # ── Tier 1 ────────────────────────────────────────────────────────────────
    # Load all existing slugs + content hashes in one query
    existing_t1: dict[str, str] = {
        row[0]: row[1]
        for row in db.query(Skill.slug, Skill.content_hash).all()
    }

    to_insert_t1 = []
    to_update_t1 = []

    for skill in tier1_skills:
        slug = skill.get("slug", "")
        if not slug:
            stats["skipped"] += 1
            continue

        content_hash = skill.get("content_hash") or hashlib.md5(
            (skill.get("raw_content") or "").encode()
        ).hexdigest()
        install_cmd = compute_install_command(slug, skill.get("platforms", ["claude_code"]))

        if slug in existing_t1:
            if existing_t1[slug] == content_hash:
                stats["skipped"] += 1
                continue
            to_update_t1.append((skill, content_hash, install_cmd))
        else:
            to_insert_t1.append((skill, content_hash, install_cmd))

    # Bulk insert new skills
    if to_insert_t1:
        db.bulk_insert_mappings(Skill, [
            dict(
                source_id        = source.id,
                owner            = s.get("owner", ""),
                repo             = s.get("repo", ""),
                slug             = s.get("slug"),
                name             = s.get("name", s.get("slug", "").split("/")[-1]),
                description      = s.get("description", ""),
                raw_content      = s.get("raw_content"),
                content_hash     = ch,
                content_length   = s.get("content_length", 0),
                primary_category = s.get("primary_category", "other"),
                sub_categories   = s.get("sub_categories", []),
                tags             = s.get("tags", []),
                role_keywords    = s.get("role_keywords", []),
                task_keywords    = s.get("task_keywords", []),
                platforms        = s.get("platforms", ["claude_code"]),
                install_command  = cmd,
                quality_score    = s.get("quality_score", 0),
                popularity_score = s.get("popularity_score", 0),
                install_count    = s.get("install_count", 0),
                github_stars     = s.get("github_stars", 0),
                tier             = 1,
                source_url       = s.get("source_url", ""),
                raw_url          = s.get("raw_url", ""),
            )
            for s, ch, cmd in to_insert_t1
        ])
        stats["inserted"] += len(to_insert_t1)

    # Update changed skills (fetch and update ORM objects in one query)
    if to_update_t1:
        slugs_to_update = {s.get("slug") for s, _, _ in to_update_t1}
        existing_objs = {
            obj.slug: obj
            for obj in db.query(Skill).filter(Skill.slug.in_(slugs_to_update)).all()
        }
        for skill, content_hash, install_cmd in to_update_t1:
            obj = existing_objs.get(skill.get("slug"))
            if obj:
                obj.raw_content      = skill.get("raw_content")
                obj.content_hash     = content_hash
                obj.content_length   = skill.get("content_length", 0)
                obj.description      = skill.get("description") or obj.description
                obj.primary_category = skill.get("primary_category", "other")
                obj.sub_categories   = skill.get("sub_categories", [])
                obj.tags             = skill.get("tags", [])
                obj.role_keywords    = skill.get("role_keywords", [])
                obj.task_keywords    = skill.get("task_keywords", [])
                obj.platforms        = skill.get("platforms", ["claude_code"])
                obj.install_command  = install_cmd
                obj.quality_score    = skill.get("quality_score", 0)
                obj.popularity_score = skill.get("popularity_score", 0)
                obj.install_count    = skill.get("install_count", obj.install_count)
                obj.github_stars     = skill.get("github_stars", obj.github_stars)
                obj.last_crawled_at  = datetime.now(timezone.utc)
        stats["updated"] += len(to_update_t1)

    db.commit()  # Single commit for all tier-1

    # ── Tier 2 ────────────────────────────────────────────────────────────────
    existing_t2: set[str] = {
        row[0] for row in db.query(SkillIndex.slug).all()
    }

    to_insert_t2 = []
    to_update_slugs_t2 = []

    for skill in tier2_skills:
        slug = skill.get("slug", "")
        if not slug:
            continue
        if slug in existing_t2:
            to_update_slugs_t2.append(skill)
        else:
            to_insert_t2.append(skill)

    if to_insert_t2:
        db.bulk_insert_mappings(SkillIndex, [
            dict(
                source_id       = source.id,
                slug            = s.get("slug"),
                name            = s.get("name", ""),
                description     = s.get("description", ""),
                raw_url         = s.get("raw_url", ""),
                install_command = compute_install_command(s.get("slug", ""), s.get("platforms", ["claude_code"])),
                platforms       = s.get("platforms", ["claude_code"]),
                install_count   = s.get("install_count", 0),
                github_stars    = s.get("github_stars", 0),
            )
            for s in to_insert_t2
        ])
        stats["inserted"] += len(to_insert_t2)

    if to_update_slugs_t2:
        slugs_t2 = {s.get("slug") for s in to_update_slugs_t2}
        existing_t2_objs = {
            obj.slug: obj
            for obj in db.query(SkillIndex).filter(SkillIndex.slug.in_(slugs_t2)).all()
        }
        skill_map = {s.get("slug"): s for s in to_update_slugs_t2}
        for slug, obj in existing_t2_objs.items():
            s = skill_map.get(slug, {})
            obj.install_count = max(obj.install_count, s.get("install_count", 0))
            obj.github_stars  = max(obj.github_stars, s.get("github_stars", 0))
            obj.last_seen_at  = datetime.now(timezone.utc)
        stats["updated"] += len(to_update_slugs_t2)

    db.commit()  # Single commit for all tier-2

    # Update source stats
    source.total_skills    = db.query(Skill).filter_by(source_id=source.id).count()
    source.last_crawled_at = datetime.now(timezone.utc)
    source.last_success_at = datetime.now(timezone.utc)
    db.commit()

    if job:
        job.skills_found   = len(tier1_skills) + len(tier2_skills)
        job.skills_added   = stats["inserted"]
        job.skills_updated = stats["updated"]
        job.errors         = stats["errors"][:50]
        job.status         = "done"
        job.finished_at    = datetime.now(timezone.utc)
        db.commit()

    print(f"[bold green]Ingestion done: inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']}[/bold green]")
    return stats
