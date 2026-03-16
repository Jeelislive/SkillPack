from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import bundles, skills, search, crawl, live, cron


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[yellow]Scheduler failed to start: {e}[/yellow]")
    yield
    # Shutdown
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="SkillPack API",
    description="Aggregate, curate, and bundle AI agent skills from across the web.",
    version="1.0.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bundles.router, prefix="/api/bundles", tags=["bundles"])
app.include_router(skills.router,  prefix="/api/skills",  tags=["skills"])
app.include_router(search.router,  prefix="/api/search",  tags=["search"])
app.include_router(crawl.router,   prefix="/api/crawl",   tags=["crawl"])
app.include_router(live.router,    prefix="/api/live",    tags=["live"])
app.include_router(cron.router,    prefix="/api/cron",    tags=["cron"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/scheduler/status")
async def scheduler_status():
    from scheduler import get_scheduler_status
    return get_scheduler_status()
