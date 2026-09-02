"""Internship Hunter — FastAPI backend application."""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import get_settings, BASE_DIR
from backend.database import get_db, init_db, SessionLocal
from backend.models.models import (
    User, Education, Skill, Project, Experience, Certification, Resume,
    Job, JobSource, JobMatch, Application, ApplicationMaterial, QuestionAnswer,
    AgentRun, Event, Notification, SearchPreference,
)
from backend.models.schemas import (
    UserCreate, UserUpdate, EducationCreate, SkillCreate, ProjectCreate,
    ExperienceCreate, CertificationCreate, SearchPreferenceCreate, SearchPreferenceOut,
    UserOut, JobOut, JobMatchOut, JobWithMatch, ApplicationOut, ApplicationUpdate,
    ApplicationMaterialsOut, AgentRunOut, EventOut, NotificationOut, DashboardStats,
    MessageResponse,
)
from backend.services.profile_service import (
    get_or_create_user, update_user, add_education, add_skill,
    add_project, add_experience, add_certification, upload_resume,
    get_user_profile_summary,
)
from backend.services.job_service import run_discovery, get_dashboard_stats
from backend.services.matching_engine import match_jobs_for_user, score_job_match
from backend.services.material_generator import prepare_application_materials
from backend.services.application_service import (
    start_application, approve_application, update_application_status,
    skip_application, get_application_materials,
)
from backend.agents.orchestrator import Orchestrator

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup
    init_db()
    os.makedirs(settings.uploads_dir, exist_ok=True)
    os.makedirs(settings.resumes_dir, exist_ok=True)

    # Ensure default user exists
    db = SessionLocal()
    try:
        get_or_create_user(db)
        # Ensure default search preferences
        user = get_or_create_user(db)
        prefs = db.query(SearchPreference).filter(SearchPreference.user_id == user.id).first()
        if not prefs:
            db.add(SearchPreference(user_id=user.id))
            db.commit()
    finally:
        db.close()

    yield
    # Shutdown


app = FastAPI(
    title="Internship Hunter API",
    description="AI-powered job discovery and application assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────
# PROFILE ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/profile", response_model=UserOut, tags=["Profile"])
def get_profile(db: Session = Depends(get_db)):
    """Get the current user profile."""
    return get_or_create_user(db)


@app.put("/api/profile", response_model=UserOut, tags=["Profile"])
def update_profile(data: UserUpdate, db: Session = Depends(get_db)):
    """Update user profile."""
    return update_user(db, data)


@app.post("/api/profile/education", tags=["Profile"])
def add_education_entry(data: EducationCreate, db: Session = Depends(get_db)):
    return add_education(db, data)


@app.post("/api/profile/skills", tags=["Profile"])
def add_skill_entry(data: SkillCreate, db: Session = Depends(get_db)):
    return add_skill(db, data)


@app.post("/api/profile/projects", tags=["Profile"])
def add_project_entry(data: ProjectCreate, db: Session = Depends(get_db)):
    return add_project(db, data)


@app.post("/api/profile/experience", tags=["Profile"])
def add_experience_entry(data: ExperienceCreate, db: Session = Depends(get_db)):
    return add_experience(db, data)


@app.post("/api/profile/certifications", tags=["Profile"])
def add_certification_entry(data: CertificationCreate, db: Session = Depends(get_db)):
    return add_certification(db, data)


@app.delete("/api/profile/skills/{skill_id}", tags=["Profile"])
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill:
        db.delete(skill)
        db.commit()
    return {"message": "deleted"}


@app.delete("/api/profile/education/{edu_id}", tags=["Profile"])
def delete_education(edu_id: int, db: Session = Depends(get_db)):
    entry = db.query(Education).filter(Education.id == edu_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"message": "deleted"}


@app.delete("/api/profile/projects/{project_id}", tags=["Profile"])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    entry = db.query(Project).filter(Project.id == project_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"message": "deleted"}


@app.delete("/api/profile/experience/{exp_id}", tags=["Profile"])
def delete_experience(exp_id: int, db: Session = Depends(get_db)):
    entry = db.query(Experience).filter(Experience.id == exp_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"message": "deleted"}


# ──────────────────────────────────────────────────────────────────
# RESUME ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.post("/api/resumes/upload", tags=["Resumes"])
async def upload_resume_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and parse a resume."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    # Save file
    filepath = os.path.join(settings.resumes_dir, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    resume = upload_resume(db, filepath, file.filename)
    return {
        "id": resume.id,
        "filename": resume.filename,
        "parsed_data": resume.parsed_data,
        "message": "Resume uploaded and parsed successfully",
    }


@app.get("/api/resumes", tags=["Resumes"])
def list_resumes(db: Session = Depends(get_db)):
    user = get_or_create_user(db)
    resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
    return resumes


# ──────────────────────────────────────────────────────────────────
# SEARCH PREFERENCES ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/search-preferences", tags=["Search"], response_model=SearchPreferenceOut)
def get_search_preferences(db: Session = Depends(get_db)):
    user = get_or_create_user(db)
    prefs = db.query(SearchPreference).filter(SearchPreference.user_id == user.id).first()
    if not prefs:
        prefs = SearchPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@app.put("/api/search-preferences", tags=["Search"], response_model=SearchPreferenceOut)
def update_search_preferences(data: SearchPreferenceCreate, db: Session = Depends(get_db)):
    user = get_or_create_user(db)
    prefs = db.query(SearchPreference).filter(SearchPreference.user_id == user.id).first()
    if not prefs:
        prefs = SearchPreference(user_id=user.id)
        db.add(prefs)

    for key, value in data.model_dump().items():
        setattr(prefs, key, value)

    db.commit()
    db.refresh(prefs)
    return prefs


# ──────────────────────────────────────────────────────────────────
# JOB ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/jobs", tags=["Jobs"])
def list_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=200),
    remote_only: bool = Query(False),
    internship_only: bool = Query(False),
    min_score: float = Query(0, ge=0, le=100),
    sort_by: str = Query("discovered_at", max_length=50),
    db: Session = Depends(get_db),
):
    """List jobs with filtering and pagination."""
    query = db.query(Job).filter(Job.is_duplicate == False)

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%") |
            Job.description.ilike(f"%{search}%")
        )

    if remote_only:
        query = query.filter(Job.remote_type.ilike("%remote%"))

    if internship_only:
        query = query.filter(Job.internship_or_fulltime == "internship")

    # Sort
    if sort_by == "fit_score":
        # Join with matches
        query = query.join(JobMatch, JobMatch.job_id == Job.id, isouter=True)
        query = query.order_by(JobMatch.fit_score.desc().nullslast())
    elif sort_by == "discovered_at":
        query = query.order_by(Job.discovered_at.desc())
    elif sort_by == "title":
        query = query.order_by(Job.title)

    total = query.count()
    offset = (page - 1) * limit
    jobs = query.offset(offset).limit(limit).all()

    user = get_or_create_user(db)
    results = []
    for job in jobs:
        match = db.query(JobMatch).filter(
            JobMatch.job_id == job.id,
            JobMatch.user_id == user.id,
        ).first()

        results.append({
            "job": JobOut.model_validate(job).model_dump(),
            "match": JobMatchOut.model_validate(match).model_dump() if match else None,
        })

    return {
        "jobs": results,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@app.get("/api/jobs/top-matches", tags=["Jobs"])
def top_matches(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """Get top matching jobs sorted by fit score."""
    user = get_or_create_user(db)
    matches = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == user.id, JobMatch.fit_score >= min_score)
        .order_by(JobMatch.fit_score.desc())
        .limit(limit)
        .all()
    )

    results = []
    for match in matches:
        job = db.query(Job).filter(Job.id == match.job_id).first()
        if job:
            results.append({
                "job": JobOut.model_validate(job).model_dump(),
                "match": JobMatchOut.model_validate(match).model_dump(),
            })

    return results


@app.get("/api/jobs/{job_id}", tags=["Jobs"])

def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    user = get_or_create_user(db)
    match = db.query(JobMatch).filter(
        JobMatch.job_id == job_id, JobMatch.user_id == user.id,
    ).first()
    return {
        "job": JobOut.model_validate(job).model_dump(),
        "match": JobMatchOut.model_validate(match).model_dump() if match else None,
    }


@app.post("/api/jobs/{job_id}/match", tags=["Jobs"])
def match_single_job(job_id: int, db: Session = Depends(get_db)):
    """Re-match a single job against the profile."""
    user = get_or_create_user(db)
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    result = score_job_match(user, job)
    existing = db.query(JobMatch).filter(
        JobMatch.job_id == job_id, JobMatch.user_id == user.id
    ).first()
    if existing:
        for k, v in result.items():
            setattr(existing, k, v)
        db.commit()
        return result
    else:
        match = JobMatch(job_id=job_id, user_id=user.id, **result)
        db.add(match)
        db.commit()
        return result


# ──────────────────────────────────────────────────────────────────
# DISCOVERY ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.post("/api/discovery/run", tags=["Discovery"])
async def run_discovery_endpoint(
    keywords: Optional[List[str]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """Run a job discovery cycle."""
    results = await run_discovery(db, keywords, sources)
    return results


@app.post("/api/discovery/orchestrate", tags=["Discovery"])
async def orchestrate_discovery(
    keywords: Optional[List[str]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """Run full orchestrator discovery cycle."""
    orchestrator = Orchestrator(db)
    results = await orchestrator.full_discovery_cycle(keywords, sources)
    return {
        "discovery": results.get("discovery", {}),
        "matching": results.get("matching", {}),
        "duplicates": results.get("duplicates", {}),
    }


# ──────────────────────────────────────────────────────────────────
# APPLICATION ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.post("/api/applications", tags=["Applications"])
def create_application(
    job_id: int = Query(...),
    mode: str = Query("prepare"),
    db: Session = Depends(get_db),
):
    """Start an application for a job."""
    app = start_application(db, job_id, mode)
    return ApplicationOut.model_validate(app).model_dump()


@app.get("/api/applications", tags=["Applications"])
def list_applications(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all applications."""
    user = get_or_create_user(db)
    query = db.query(Application).filter(Application.user_id == user.id)
    if status:
        query = query.filter(Application.status == status)

    apps = query.order_by(Application.last_updated.desc()).all()
    results = []
    for app in apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        d = ApplicationOut.model_validate(app).model_dump()
        if job:
            d["job"] = JobOut.model_validate(job).model_dump()
        results.append(d)
    return results


@app.get("/api/applications/{app_id}", tags=["Applications"])
def get_application(app_id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(404, "Application not found")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    materials = get_application_materials(db, app_id)

    d = ApplicationOut.model_validate(app).model_dump()
    if job:
        d["job"] = JobOut.model_validate(job).model_dump()
    d["materials"] = materials
    return d


@app.put("/api/applications/{app_id}", tags=["Applications"])
def update_application(app_id: int, data: ApplicationUpdate, db: Session = Depends(get_db)):
    app = update_application_status(db, app_id, data.status or "", data.notes or "")
    return ApplicationOut.model_validate(app).model_dump()


@app.post("/api/applications/{app_id}/approve", tags=["Applications"])
def approve_application_endpoint(app_id: int, db: Session = Depends(get_db)):
    app = approve_application(db, app_id)
    return ApplicationOut.model_validate(app).model_dump()


@app.post("/api/applications/{app_id}/skip", tags=["Applications"])
def skip_application_endpoint(app_id: int, db: Session = Depends(get_db)):
    skip_application(db, app_id)
    return {"message": "Application skipped"}


@app.get("/api/applications/{app_id}/materials", tags=["Applications"])
def get_application_materials_endpoint(app_id: int, db: Session = Depends(get_db)):
    return get_application_materials(db, app_id)



@app.post("/api/applications/batch-prepare", tags=["Applications"])
def batch_prepare(
    job_ids: List[int] = Query(...),
    mode: str = Query("prepare"),
    db: Session = Depends(get_db),
):
    """Prepare applications for multiple jobs."""
    results = []
    for job_id in job_ids:
        try:
            app = start_application(db, job_id, mode)
            results.append({"job_id": job_id, "application_id": app.id, "status": "success"})
        except Exception as e:
            results.append({"job_id": job_id, "status": "error", "error": str(e)})
    return results


# ──────────────────────────────────────────────────────────────────
# DASHBOARD & ANALYTICS ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/dashboard/stats", tags=["Dashboard"], response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


@app.get("/api/dashboard/overview", tags=["Dashboard"])
def dashboard_overview(db: Session = Depends(get_db)):
    user = get_or_create_user(db)
    return {
        "user": UserOut.model_validate(user).model_dump(),
        "stats": get_dashboard_stats(db),
        "recent_jobs": [
            JobOut.model_validate(j).model_dump()
            for j in db.query(Job).filter(Job.is_duplicate == False).order_by(Job.discovered_at.desc()).limit(5).all()
        ],
        "pending_approvals": db.query(Application).filter(
            Application.user_id == user.id,
            Application.status == "awaiting_approval",
        ).count(),
    }


# ──────────────────────────────────────────────────────────────────
# AGENT ACTIVITY ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/agents/runs", tags=["Agents"])
def list_agent_runs(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(AgentRun).order_by(AgentRun.started_at.desc())
    if status:
        query = query.filter(AgentRun.status == status)
    runs = query.limit(limit).all()
    return [AgentRunOut.model_validate(r).model_dump() for r in runs]


@app.get("/api/events", tags=["Events"])
def list_events(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    events = db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
    return [EventOut.model_validate(e).model_dump() for e in events]


# ──────────────────────────────────────────────────────────────────
# NOTIFICATIONS ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/notifications", tags=["Notifications"])
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    user = get_or_create_user(db)
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [NotificationOut.model_validate(n).model_dump() for n in notifs]


@app.post("/api/notifications/{notif_id}/read", tags=["Notifications"])
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "marked as read"}


# ──────────────────────────────────────────────────────────────────
# SOURCES ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/api/sources", tags=["Sources"])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(JobSource).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "adapter_class": s.adapter_class,
            "is_active": s.is_active,
            "last_run": s.last_run.isoformat() if s.last_run else None,
            "jobs_found": s.jobs_found,
        }
        for s in sources
    ]


@app.get("/api/sources/available", tags=["Sources"])
def list_available_sources():
    from backend.sources import AVAILABLE_SOURCES
    return [
        {"name": name, "class": cls.__name__}
        for name, cls in AVAILABLE_SOURCES.items()
    ]


# ──────────────────────────────────────────────────────────────────
# SEED ENDPOINT — Pre-populate with Bhavya's profile
# ──────────────────────────────────────────────────────────────────

@app.post("/api/seed-profile", tags=["Setup"])
def seed_profile(db: Session = Depends(get_db)):
    """Pre-populate the database with Bhavya Gupta's profile from resume."""
    user = get_or_create_user(db)

    # Check if already seeded
    if user.education_entries:
        return {"message": "Profile already seeded", "user_id": user.id}

    # Education
    add_education(db, EducationCreate(
        university="Birla Institute of Technology and Science, Pilani",
        degree="B.E. (Hons.)",
        field_of_study="Computer Science Engineering",
        location="Pilani, India",
        start_date="Aug 2023",
        end_date="May 2027",
        gpa="",
        is_current=True,
    ))

    # Skills
    skills_data = [
        ("Python", "programming", "advanced"),
        ("JavaScript", "programming", "advanced"),
        ("TypeScript", "programming", "intermediate"),
        ("Go", "programming", "intermediate"),
        ("SQL", "programming", "advanced"),
        ("React.js", "framework", "advanced"),
        ("FastAPI", "framework", "advanced"),
        ("LangChain", "framework", "advanced"),
        ("XGBoost", "ml", "intermediate"),
        ("Docker", "tool", "intermediate"),
        ("Git", "tool", "advanced"),
        ("RAG systems", "ml", "advanced"),
        ("PostgreSQL", "tool", "intermediate"),
        ("Redis", "tool", "intermediate"),
    ]
    for name, cat, prof in skills_data:
        add_skill(db, SkillCreate(name=name, category=cat, proficiency=prof))

    # Experience
    add_experience(db, ExperienceCreate(
        company="Kerala Infrastructure and Technology for Education (KITE)",
        title="AI/ML Intern",
        location="Kerala, India",
        start_date="May 2025",
        end_date="Jul 2025",
        description="Built AI analytics tools using Python ML pipelines for decision making on the Samagra serving 4M+ students. Enhanced ML models for automated anomaly detection. Deployed a RAG system cutting manual analysis time by 40%.",
    ))
    add_experience(db, ExperienceCreate(
        company="Students' Union Technical Team (SUTT)",
        title="Product Lead, SU App",
        location="Pilani, India",
        start_date="Jul 2025",
        end_date="Jan 2026",
        description="Initiated SU App handling Rs12Cr+ annual credits. Designed scalable and secure transaction architecture. Built core modules (ledger, auth, payments) ensuring <1s transactions latency.",
    ))

    # Projects
    add_project(db, ProjectCreate(
        name="Distributed Task Queue Engine",
        description="Implemented a distributed job queue handling 10k+ jobs/min with priority scheduling and at-least-once delivery. Added retry backoff, dead-letter queues, and fault-tolerant recovery. Built real-time dashboard with sub-second latency.",
        technologies="Go, Redis, PostgreSQL, Docker, React",
    ))
    add_project(db, ProjectCreate(
        name="BITS AI Tutor (BAIT)",
        description="Built an AI exam tutor using LangChain and RAG pipeline on 500+ PYQs/lectures. Optimized for BITS exams achieving 4.6/5 usability across beta testing with 1000+ students from 80+ courses.",
        technologies="LangChain, FastAPI, React.js, ChromaDB, OpenAI",
    ))
    add_project(db, ProjectCreate(
        name="Story Crafting Platform",
        description="Built an LLM-based storytelling platform managing 100+ dynamic state transitions. Engineered modular prompt pipelines improving coherence scores by 28%. Enabled low-latency (<300ms) with 50+ concurrent sessions.",
        technologies="FastAPI, React.js, Tailwind, JSON Schema, React Router",
    ))

    db.commit()
    return {"message": "Profile seeded successfully", "user_id": user.id}


@app.post("/api/seed-default-preferences", tags=["Setup"])
def seed_preferences(db: Session = Depends(get_db)):
    """Seed default search preferences."""
    user = get_or_create_user(db)
    prefs = db.query(SearchPreference).filter(SearchPreference.user_id == user.id).first()
    if not prefs:
        prefs = SearchPreference(user_id=user.id)
        db.add(prefs)

    prefs.keywords = [
        "Software Engineer Intern",
        "Software Engineering Intern",
        "Data Science Intern",
        "Machine Learning Intern",
        "Machine Learning Engineer Intern",
        "AI Intern",
        "Applied AI",
        "Data Analyst",
        "Backend Engineer",
        "Full Stack Engineer",
    ]
    prefs.locations = ["Worldwide"]
    prefs.remote_only = True
    prefs.employment_types = ["internship", "co_op", "graduate", "full_time"]
    prefs.min_fit_score = 50
    prefs.require_sponsorship_eligible = True
    prefs.preferred_countries = ["Worldwide"]

    db.commit()
    return {"message": "Preferences seeded"}


# ──────────────────────────────────────────────────────────────────
# SERVE FRONTEND (production build)
# ──────────────────────────────────────────────────────────────────

frontend_build = BASE_DIR / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_build / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_build / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_build / "index.html"))
