"""
SkillPack — First Run Pipeline
Usage:
  python3 run_crawl.py          # full crawl
  python3 run_crawl.py --test   # quick test (skills.sh only, no GitHub)
  python3 run_crawl.py bundles  # regenerate bundles only
"""

import asyncio
import sys
import time
from datetime import datetime
from rich import print
from rich.console import Console
from rich.rule import Rule

console = Console()

def ts():
    return datetime.now().strftime("%H:%M:%S")

def step(n, total, label):
    console.rule(f"[bold cyan][{ts()}] Step {n}/{total}: {label}[/bold cyan]")


async def run_skills_sh():
    from crawlers.skills_sh import SkillsShCrawler
    from pipeline.tagger import SkillTagger
    from db.ingestion import ingest_crawl_results
    from db.database import SyncSessionLocal
    from config import get_settings
    settings = get_settings()

    print(f"[dim]{ts()}[/dim] Fetching skills.sh leaderboard...", flush=True)
    crawler = SkillsShCrawler(
        github_token=settings.github_token,
        tier1_min_installs=settings.tier1_min_installs,
    )
    tier1_raw, tier2_raw = await crawler.run()
    print(f"[dim]{ts()}[/dim] Leaderboard done — [green]{len(tier1_raw)} tier-1[/green], [yellow]{len(tier2_raw)} tier-2[/yellow]")

    print(f"[dim]{ts()}[/dim] Tagging {len(tier1_raw)} skills with keyword matching...")
    tagger = SkillTagger()
    tier1_tagged = tagger.tag_batch_fast(tier1_raw)
    print(f"[dim]{ts()}[/dim] Tagging done")

    print(f"[dim]{ts()}[/dim] Saving to database...")
    db = SyncSessionLocal()
    try:
        stats = ingest_crawl_results(db, tier1_tagged, tier2_raw, "skills_sh")
    finally:
        db.close()
    print(f"[dim]{ts()}[/dim] [green]Saved — inserted:{stats['inserted']} updated:{stats['updated']} skipped:{stats['skipped']}[/green]")
    return stats


async def run_github():
    from crawlers.github_crawler import GitHubCrawler
    from pipeline.tagger import SkillTagger
    from db.ingestion import ingest_crawl_results
    from db.database import SyncSessionLocal
    from db.models import Skill, SkillIndex
    from config import get_settings
    settings = get_settings()

    # Load existing slugs to skip duplicates
    db = SyncSessionLocal()
    try:
        existing_slugs = set(r[0] for r in db.query(Skill.slug).all()) \
                       | set(r[0] for r in db.query(SkillIndex.slug).all())
    finally:
        db.close()
    print(f"[dim]{ts()}[/dim] {len(existing_slugs)} slugs already in DB, will skip duplicates")

    tokens = [settings.github_token]
    if settings.github_token_2:
        tokens.append(settings.github_token_2)

    print(f"[dim]{ts()}[/dim] Starting GitHub Search API crawl (6 queries × up to 10 pages)")
    print(f"[dim]{ts()}[/dim] [yellow]GitHub rate limit = 30 req/min — expect ~10-15 min[/yellow]")

    crawler = GitHubCrawler(tokens=tokens)
    skills = await crawler.run(existing_slugs=existing_slugs)
    print(f"[dim]{ts()}[/dim] GitHub crawl done — [green]{len(skills)} new skills[/green]")

    print(f"[dim]{ts()}[/dim] Tagging {len(skills)} skills...")
    tagger = SkillTagger()
    tagged = tagger.tag_batch_fast(skills)

    tier1 = [s for s in tagged if s.get("quality_score", 0) >= 4 and s.get("raw_content")]
    tier2 = [s for s in tagged if s.get("quality_score", 0) < 4 or not s.get("raw_content")]
    print(f"[dim]{ts()}[/dim] Split — [green]{len(tier1)} tier-1[/green] / [yellow]{len(tier2)} tier-2[/yellow]")

    print(f"[dim]{ts()}[/dim] Saving to database...")
    db = SyncSessionLocal()
    try:
        stats = ingest_crawl_results(db, tier1, tier2, "github")
    finally:
        db.close()
    print(f"[dim]{ts()}[/dim] [green]Saved — inserted:{stats['inserted']} updated:{stats['updated']} skipped:{stats['skipped']}[/green]")
    return stats


def run_bundles():
    from pipeline.bundle_generator import BundleGenerator
    from db.database import SyncSessionLocal

    print(f"[dim]{ts()}[/dim] Generating bundles...")
    db = SyncSessionLocal()
    try:
        gen = BundleGenerator(db)
        gen.generate_all()
    finally:
        db.close()
    print(f"[dim]{ts()}[/dim] [green]Bundles ready[/green]")


async def main():
    args = sys.argv[1:]
    test_mode = "--test" in args
    bundles_only = "bundles" in args

    console.rule("[bold magenta]SkillPack — First Run Pipeline[/bold magenta]")
    if test_mode:
        print("[yellow]TEST MODE — skills.sh only, skipping GitHub crawl[/yellow]")

    t_start = time.time()

    if bundles_only:
        step(1, 1, "Regenerate bundles")
        run_bundles()
    else:
        total_steps = 2 if test_mode else 3

        step(1, total_steps, "Crawl skills.sh")
        await run_skills_sh()

        if not test_mode:
            step(2, total_steps, "Crawl GitHub")
            await run_github()

        step(total_steps, total_steps, "Generate bundles")
        run_bundles()

    elapsed = int(time.time() - t_start)
    console.rule(f"[bold green]Done in {elapsed}s[/bold green]")
    print("\n[bold]Next steps:[/bold]")
    print("  Start API:      [cyan]uvicorn api.main:app --reload --port 8000[/cyan]")
    print("  Start frontend: [cyan]cd ../frontend && npm run dev[/cyan]")


if __name__ == "__main__":
    asyncio.run(main())
