"""TalentVerse 2.0 FastAPI Backend Application."""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import CORS_ORIGINS
from backend.database import init_db, SessionLocal, User, CandidateProfileModel
from backend.auth_utils import hash_password
from backend.ai_engine import AIProviderUnavailable, RateLimitError
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

# Initialize database schemas immediately
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-seed demo user and profile if fresh database
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.email == "demo@talentverse.ai").first()
        if not demo_user:
            demo_user = User(
                email="demo@talentverse.ai",
                hashed_password=hash_password("talentverse123"),
                full_name="Alex Morgan",
                role="candidate",
                is_demo=True,
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            profile = CandidateProfileModel(
                user_id=demo_user.id,
                full_name="Alex Morgan",
                email="demo@talentverse.ai",
                phone="+1 (555) 019-2834",
                location="San Francisco, CA / Remote",
                target_role="Full Stack AI Engineer",
                experience_level="Entry-level",
                summary="Full stack engineer specializing in Python, React, TypeScript, and AI integrations. Focused on developing production-grade SaaS products with automated testing and modern design systems.",
                skills=["Python", "FastAPI", "React", "TypeScript", "SQL", "Git", "Docker", "Tailwind CSS", "REST APIs", "Azure Fundamentals"],
                soft_skills=["System Design", "Technical Problem Solving", "Effective Communication", "Agile Collaboration"],
                experience=[
                    "Software Engineering Fellow — TechLabs (2024): Developed modular full-stack web applications and automated data pipelines.",
                    "Undergraduate Teaching Assistant — Computer Science Dept (2023): Mentored 40+ students in data structures and Python programming."
                ],
                education=[
                    "B.Tech in Computer Science and Engineering - Expected Graduation: 2027"
                ],
                certifications=[
                    "Microsoft Azure Fundamentals (AZ-900)",
                    "AWS Certified Cloud Practitioner"
                ],
                projects=[
                    "TalentVerse: AI-powered career intelligence SaaS platform with multi-provider fallbacks and dynamic skill roadmapping.",
                    "Real-Time Analytics Pipeline: Distributed event streaming platform processing 10k events/sec."
                ],
                missing_information=[
                    "Quantified latency metrics on recent fellowship work",
                    "Links to live public repositories"
                ],
                strengths=[
                    "Strong full stack foundation across backend services and modern frontend frameworks",
                    "Demonstrated initiative in AI integration and cloud certification",
                    "High attention to code modularity and architecture standards"
                ],
                improvement_recommendations=[
                    "Add measurable benchmarks (latency reduction, query throughput) to project achievements",
                    "Practice distributed system architecture interviews",
                    "Deploy projects to live cloud environments with automated CI/CD"
                ],
                readiness_score=85,
            )
            db.add(profile)
            db.commit()
    finally:
        db.close()

    yield


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
