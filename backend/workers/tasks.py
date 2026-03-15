"""
Celery tasks for crawling, tagging, and bundle generation.
"""

import asyncio
from datetime import datetime, timezone
from rich import print
from workers.celery_app import celery_app
from config import get_settings
from db.database import SyncSessionLocal
from db.models import CrawlJob, Source
from db.ingestion import ingest_crawl_results
from crawlers.skills_sh import SkillsShCrawler
from crawlers.github_crawler import GitHubCrawler
from pipeline.tagger import SkillTagger
from pipeline.bundle_generator import BundleGenerator
from db.models import Skill, SkillIndex

settings = get_settings()


def _run_async(coro):
    """Run async coroutine from sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(bind=True, name="workers.tasks.crawl_skills_sh")
def crawl_skills_sh(self):
    """Crawl skills.sh and store results."""
    print("[bold blue]Task: crawl_skills_sh started[/bold blue]")
    db = next(SyncSessionLocal().__enter__() for _ in [None])

    try:
        source = db.query(Source).filter_by(name="skills_sh").first()
        job = CrawlJob(
            source_id  = source.id if source else None,
            status     = "running",
            started_at = datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()

        crawler = SkillsShCrawler(
            github_token       = settings.github_token,
            tier1_min_installs = settings.tier1_min_installs,
        )

        tier1_raw, tier2_raw = _run_async(crawler.run())

        tagger = SkillTagger()
        tier1_tagged = tagger.tag_batch_fast(tier1_raw)

        stats = ingest_crawl_results(
            db, tier1_tagged, tier2_raw, "skills_sh", job
        )
        print(f"[green]crawl_skills_sh done: {stats}[/green]")
        return stats

    except Exception as e:
        print(f"[red]crawl_skills_sh failed: {e}[/red]")
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(bind=True, name="workers.tasks.crawl_github")
def crawl_github(self):
    """Crawl GitHub for SKILL.md files not on skills.sh."""
    print("[bold blue]Task: crawl_github started[/bold blue]")
    db = SyncSessionLocal()

    try:
        source = db.query(Source).filter_by(name="github").first()
        job = CrawlJob(
            source_id  = source.id if source else None,
            status     = "running",
            started_at = datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()

        # Get all existing slugs to avoid duplicates
        existing_slugs = set(
            r[0] for r in db.query(Skill.slug).all()
        ) | set(
            r[0] for r in db.query(SkillIndex.slug).all()
        )

        tokens = [settings.github_token]
        if settings.github_token_2:
            tokens.append(settings.github_token_2)

        crawler = GitHubCrawler(tokens=tokens)
        skills = _run_async(crawler.run(existing_slugs=existing_slugs))

        # All GitHub skills start as tier 1 if they have content + quality
        tagger = SkillTagger()
        tagged = tagger.tag_batch_fast(skills)

        tier1 = [s for s in tagged if s.get("quality_score", 0) >= 4 and s.get("raw_content")]
        tier2 = [s for s in tagged if s.get("quality_score", 0) < 4 or not s.get("raw_content")]

        stats = ingest_crawl_results(db, tier1, tier2, "github", job)
        print(f"[green]crawl_github done: {stats}[/green]")
        return stats

    except Exception as e:
        print(f"[red]crawl_github failed: {e}[/red]")
        raise self.retry(exc=e, countdown=600, max_retries=2)
    finally:
        db.close()


@celery_app.task(name="workers.tasks.regenerate_bundles")
def regenerate_bundles():
    """Regenerate all bundles from current DB skills."""
    print("[bold blue]Task: regenerate_bundles started[/bold blue]")
    db = SyncSessionLocal()
    try:
        generator = BundleGenerator(db)
        generator.generate_all()
        print("[bold green]Bundles regenerated.[/bold green]")
        return {"status": "done"}
    finally:
        db.close()


@celery_app.task(name="workers.tasks.run_full_crawl")
def run_full_crawl():
    """Orchestrate: crawl all sources then regenerate bundles."""
    print("[bold blue]Task: run_full_crawl started[/bold blue]")
    # Chain: skills_sh → github → bundles
    from celery import chain
    workflow = chain(
        crawl_skills_sh.s(),
        crawl_github.s(),
        regenerate_bundles.s(),
    )
    workflow.apply_async()
    return {"status": "scheduled"}
