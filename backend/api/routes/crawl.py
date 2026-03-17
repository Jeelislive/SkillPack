"""
Crawl management routes - trigger crawls, check job status.
Admin-use only (protect with env-based token in production).
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.database import get_db
from db.models import CrawlJob, Source, Skill, SkillIndex
from workers.tasks import crawl_skills_sh, crawl_github, regenerate_bundles, run_full_crawl
from config import get_settings

router = APIRouter()
settings = get_settings()


def _require_admin(x_admin_token: str = Header(default="")):
    """Simple token-based admin gate."""
    expected = getattr(settings, "admin_token", "changeme")
    if x_admin_token != expected:
        raise HTTPException(status_code=403, detail="Admin token required")


@router.post("/trigger/full")
async def trigger_full_crawl(_=Depends(_require_admin)):
    task = run_full_crawl.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/trigger/skills-sh")
async def trigger_skills_sh(_=Depends(_require_admin)):
    task = crawl_skills_sh.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/trigger/github")
async def trigger_github(_=Depends(_require_admin)):
    task = crawl_github.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/trigger/bundles")
async def trigger_bundles(_=Depends(_require_admin)):
    task = regenerate_bundles.delay()
    return {"task_id": task.id, "status": "queued"}


@router.get("/jobs")
async def list_jobs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CrawlJob).order_by(desc(CrawlJob.created_at)).limit(limit)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "source_id": j.source_id,
            "status": j.status,
            "skills_found": j.skills_found,
            "skills_added": j.skills_added,
            "skills_updated": j.skills_updated,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        }
        for j in jobs
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    tier1_count = await db.execute(select(func.count(Skill.id)).where(Skill.tier == 1))
    tier2_count = await db.execute(select(func.count(SkillIndex.id)))
    sources = await db.execute(select(Source))

    return {
        "tier1_skills": tier1_count.scalar(),
        "tier2_skills": tier2_count.scalar(),
        "total_skills": (tier1_count.scalar() or 0) + (tier2_count.scalar() or 0),
        "sources": [
            {
                "name": s.name,
                "display_name": s.display_name,
                "total_skills": s.total_skills,
                "last_crawled_at": s.last_crawled_at.isoformat() if s.last_crawled_at else None,
            }
            for s in sources.scalars().all()
        ],
    }
