"""TalentVerse 2.0 FastAPI Backend Application."""
import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.config import CORS_ORIGINS
from backend.database import init_db, SessionLocal
from backend.ai_engine import AIProviderUnavailable, RateLimitError
from backend.routes.auth import cleanup_expired_demo_sessions
from backend.routes import (
    auth,
    resumes,
    roadmaps,
    jobs,
    projects,
    interviews,
    profiles,
    reports,
    analytics,
    system,
)

logger = logging.getLogger(__name__)
DEMO_CLEANUP_INTERVAL_SECONDS = 60 * 60

# Initialize database schemas immediately
init_db()


def _cleanup_expired_demo_sessions_once() -> None:
    db = SessionLocal()
    try:
        cleanup_expired_demo_sessions(db)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Expired demo session cleanup failed.")
    finally:
        db.close()


async def _demo_session_cleanup_worker() -> None:
    while True:
        cleanup_task = asyncio.create_task(
            asyncio.to_thread(_cleanup_expired_demo_sessions_once)
        )
        try:
            await asyncio.shield(cleanup_task)
        except asyncio.CancelledError:
            await cleanup_task
            raise
        await asyncio.sleep(DEMO_CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(_demo_session_cleanup_worker())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(
    title="TalentVerse 2.0 API",
    description="Next-generation AI-powered career intelligence and talent acceleration platform.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RateLimitError)
async def ai_rate_limit_handler(request: Request, exc: RateLimitError):
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.exception_handler(AIProviderUnavailable)
async def ai_unavailable_handler(request: Request, exc: AIProviderUnavailable):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(roadmaps.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TalentVerse 2.0 Backend",
        "version": "2.0.0",
    }


# Static Frontend Distribution mounting
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    frontend_root = frontend_dist.resolve()
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # Do not intercept API requests
        if full_path.startswith("api"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API endpoint not found.")
        target_file = (frontend_root / full_path).resolve()
        if target_file.is_relative_to(frontend_root) and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist / "index.html")
