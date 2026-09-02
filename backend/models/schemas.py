"""Pydantic schemas for API request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ── Profile ──────────────────────────────────────────────────────
class EducationBase(BaseModel):
    university: str
    degree: str
    field_of_study: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    is_current: bool = False

class EducationCreate(EducationBase):
    pass

class EducationOut(EducationBase):
    id: int
    model_config = {"from_attributes": True}


class SkillBase(BaseModel):
    name: str
    category: str = "general"
    proficiency: str = "intermediate"

class SkillCreate(SkillBase):
    pass

class SkillOut(SkillBase):
    id: int
    model_config = {"from_attributes": True}


class ProjectBase(BaseModel):
    name: str
    description: str = ""
    technologies: str = ""
    url: str = ""
    start_date: str = ""
    end_date: str = ""

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    model_config = {"from_attributes": True}


class ExperienceBase(BaseModel):
    company: str
    title: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    is_current: bool = False

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceOut(ExperienceBase):
    id: int
    model_config = {"from_attributes": True}


class CertificationBase(BaseModel):
    name: str
    issuer: str = ""
    date_obtained: str = ""
    url: str = ""

class CertificationCreate(CertificationBase):
    pass

class CertificationOut(CertificationBase):
    id: int
    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    id: int
    filename: str
    file_path: str
    is_primary: bool
    uploaded_at: datetime
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str = "Bhavya Gupta"
    email: str = "f20230494@pilani.bits-pilani.ac.in"
    phone: str = "+91-9530382520"
    location: str = "Pilani"
    citizenship: str = "Indian"
    requires_sponsorship: bool = True
    linkedin_url: str = "https://linkedin.com/in/bhavya-gupta"
    github_url: str = "https://github.com/bhavyagupta"
    portfolio_url: str = ""
    availability: str = "immediate"
    preferred_job_type: str = "remote"


class UserOut(UserCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    education_entries: List[EducationOut] = []
    skills: List[SkillOut] = []
    projects: List[ProjectOut] = []
    experiences: List[ExperienceOut] = []
    certifications: List[CertificationOut] = []
    resumes: List[ResumeOut] = []
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    citizenship: Optional[str] = None
    requires_sponsorship: Optional[bool] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    availability: Optional[str] = None
    preferred_job_type: Optional[str] = None


# ── Jobs ─────────────────────────────────────────────────────────
class JobOut(BaseModel):
    id: int
    external_id: str = ""
    title: str
    company: str
    location: str = ""
    remote_type: str = "remote"
    employment_type: str = "internship"
    internship_or_fulltime: str = "internship"
    country: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = ""
    description: str = ""
    requirements: str = ""
    skills: List[str] = []
    experience_required: str = ""
    visa_information: str = ""
    sponsorship_information: str = ""
    application_url: str = ""
    source_name: str = ""
    source_url: str = ""
    date_posted: str = ""
    deadline: str = ""
    is_duplicate: bool = False
    discovered_at: datetime
    model_config = {"from_attributes": True}


class JobMatchOut(BaseModel):
    id: int
    job_id: int
    fit_score: float
    technical_match: float = 0
    role_match: float = 0
    experience_match: float = 0
    education_match: float = 0
    location_match: float = 0
    authorization_match: float = 0
    project_match: float = 0
    feasibility_match: float = 0
    missing_skills: List[str] = []
    strengths: List[str] = []
    concerns: List[str] = []
    recommendation: str = "SKIP"
    explanation: str = ""
    matched_at: datetime
    model_config = {"from_attributes": True}


class JobWithMatch(BaseModel):
    job: JobOut
    match: Optional[JobMatchOut] = None


# ── Search Preferences ───────────────────────────────────────────
class SearchPreferenceBase(BaseModel):
    keywords: List[str] = [
        "Software Engineer Intern",
        "Software Engineering Intern",
        "Data Science Intern",
        "Machine Learning Intern",
        "AI Intern",
        "Data Analyst",
        "Backend Engineer",
        "Full Stack Engineer",
        "ML Engineer Intern",
    ]
    locations: List[str] = ["Worldwide"]
    remote_only: bool = True
    employment_types: List[str] = ["internship", "co_op", "graduate", "full_time"]
    min_fit_score: int = 60
    require_sponsorship_eligible: bool = True
    exclude_companies: List[str] = []
    preferred_countries: List[str] = ["Worldwide"]
    salary_min: Optional[int] = None
    salary_currency: str = "USD"
    max_results: int = 100

class SearchPreferenceCreate(SearchPreferenceBase):
    pass

class SearchPreferenceOut(SearchPreferenceBase):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


# ── Applications ─────────────────────────────────────────────────
class ApplicationOut(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: str
    resume_version: str = ""
    cover_letter: str = ""
    notes: str = ""
    interview_dates: List[Any] = []
    follow_up_date: str = ""
    date_discovered: datetime
    date_applied: Optional[datetime] = None
    last_updated: datetime
    job: Optional[JobOut] = None
    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    cover_letter: Optional[str] = None
    resume_version: Optional[str] = None


# ── Application Materials ────────────────────────────────────────
class ApplicationMaterialsOut(BaseModel):
    resume: str = ""
    cover_letter: str = ""
    summary: str = ""
    skills_summary: str = ""
    why_company: str = ""
    why_role: str = ""
    recruiter_message: str = ""
    question_answers: List[dict] = []


# ── Agent Activity ───────────────────────────────────────────────
class AgentRunOut(BaseModel):
    id: int
    agent_name: str
    status: str
    task: str = ""
    input_summary: str = ""
    actions: List[Any] = []
    decisions: List[Any] = []
    outputs: dict = {}
    errors: List[Any] = []
    blocked_actions: List[Any] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: int
    event_type: str
    title: str = ""
    message: str = ""
    event_metadata: dict = {}
    is_read: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str = ""
    notification_type: str = "info"
    is_read: bool = False
    action_url: str = ""
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Dashboard / Analytics ────────────────────────────────────────
class DashboardStats(BaseModel):
    jobs_discovered: int = 0
    jobs_matching: int = 0
    applications_prepared: int = 0
    applications_approved: int = 0
    applications_submitted: int = 0
    interview_count: int = 0
    response_rate: float = 0.0
    top_companies: List[dict] = []
    top_categories: List[dict] = []
    average_fit_score: float = 0.0


# ── Generic ──────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: Optional[Any] = None
