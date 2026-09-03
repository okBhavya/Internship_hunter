"""SQLAlchemy ORM models for the Internship Hunter database."""
from __future__ import annotations

import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, default="Bhavya Gupta")
    email = Column(String(300), nullable=False, default="f20230494@pilani.bits-pilani.ac.in")
    phone = Column(String(50), default="+91-9530382520")
    location = Column(String(200), default="Pilani")
    citizenship = Column(String(100), default="Indian")
    requires_sponsorship = Column(Boolean, default=True)
    linkedin_url = Column(String(500), default="https://linkedin.com/in/bhavya-gupta")
    github_url = Column(String(500), default="https://github.com/bhavyagupta")
    portfolio_url = Column(String(500), default="")
    availability = Column(String(100), default="immediate")
    preferred_job_type = Column(String(100), default="remote")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    education_entries = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    search_preferences = relationship("SearchPreference", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    university = Column(String(300), nullable=False)
    degree = Column(String(300), nullable=False)
    field_of_study = Column(String(300), default="")
    location = Column(String(200), default="")
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    gpa = Column(String(50), default="")
    is_current = Column(Boolean, default=False)

    user = relationship("User", back_populates="education_entries")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), default="general")  # programming, framework, cloud, ml, tool
    proficiency = Column(String(50), default="intermediate")  # beginner, intermediate, advanced, expert

    user = relationship("User", back_populates="skills")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(300), nullable=False)
    description = Column(Text, default="")
    technologies = Column(String(500), default="")
    url = Column(String(500), default="")
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")

    user = relationship("User", back_populates="projects")


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String(300), nullable=False)
    title = Column(String(300), nullable=False)
    location = Column(String(200), default="")
    start_date = Column(String(50), default="")
    end_date = Column(String(50), default="")
    description = Column(Text, default="")
    is_current = Column(Boolean, default=False)

    user = relationship("User", back_populates="experiences")


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(300), nullable=False)
    issuer = Column(String(300), default="")
    date_obtained = Column(String(50), default="")
    url = Column(String(500), default="")

    user = relationship("User", back_populates="certifications")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    parsed_data = Column(JSON, default=dict)
    is_primary = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="resumes")


# ── Jobs ─────────────────────────────────────────────────────────
class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    adapter_class = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default=dict)
    last_run = Column(DateTime, nullable=True)
    jobs_found = Column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(500), default="")
    title = Column(String(500), nullable=False)
    company = Column(String(300), nullable=False)
    location = Column(String(300), default="")
    remote_type = Column(String(50), default="remote")
    employment_type = Column(String(50), default="internship")
    internship_or_fulltime = Column(String(50), default="internship")
    country = Column(String(100), default="")
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String(10), default="")
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    preferred_qualifications = Column(Text, default="")
    skills = Column(JSON, default=list)  # list of skill strings
    experience_required = Column(String(100), default="")
    visa_information = Column(Text, default="")
    sponsorship_information = Column(Text, default="")
    application_url = Column(String(1000), default="")
    source_name = Column(String(200), default="")
    source_url = Column(String(1000), default="")
    date_posted = Column(String(50), default="")
    deadline = Column(String(50), default="")
    is_duplicate = Column(Boolean, default=False)
    canonical_job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    duplicate_sources = Column(JSON, default=list)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw_data = Column(JSON, default=dict)

    # Relationships
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


# ── Job Matching ─────────────────────────────────────────────────
class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fit_score = Column(Float, default=0.0)
    technical_match = Column(Float, default=0.0)
    role_match = Column(Float, default=0.0)
    experience_match = Column(Float, default=0.0)
    education_match = Column(Float, default=0.0)
    location_match = Column(Float, default=0.0)
    authorization_match = Column(Float, default=0.0)
    project_match = Column(Float, default=0.0)
    feasibility_match = Column(Float, default=0.0)
    missing_skills = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    concerns = Column(JSON, default=list)
    recommendation = Column(String(20), default="SKIP")
    explanation = Column(Text, default="")
    matched_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="matches")


# ── Applications ─────────────────────────────────────────────────
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), default="discovered")
    resume_version = Column(String(300), default="")
    cover_letter = Column(Text, default="")
    tailored_resume_path = Column(String(1000), default="")
    application_answers = Column(JSON, default=dict)
    recruiter_name = Column(String(300), default="")
    notes = Column(Text, default="")
    interview_dates = Column(JSON, default=list)
    follow_up_date = Column(String(50), default="")
    rejection_date = Column(String(50), default="")
    date_discovered = Column(DateTime, default=datetime.datetime.utcnow)
    date_applied = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class ApplicationMaterial(Base):
    __tablename__ = "application_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    material_type = Column(String(100), nullable=False)  # resume, cover_letter, summary, etc.
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(100), default="")
    suggested_answer = Column(Text, default="")
    approved = Column(Boolean, default=False)


# ── Agent Activity & Events ──────────────────────────────────────
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(200), nullable=False)
    status = Column(String(50), default="running")
    task = Column(String(500), default="")
    input_summary = Column(Text, default="")
    actions = Column(JSON, default=list)
    decisions = Column(JSON, default=list)
    outputs = Column(JSON, default=dict)
    errors = Column(JSON, default=list)
    blocked_actions = Column(JSON, default=list)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    title = Column(String(500), default="")
    message = Column(Text, default="")
    event_metadata = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, default="")
    notification_type = Column(String(100), default="info")  # info, warning, success, approval_needed
    is_read = Column(Boolean, default=False)
    action_url = Column(String(1000), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Search Settings ──────────────────────────────────────────────
class SearchPreference(Base):
    __tablename__ = "search_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keywords = Column(JSON, default=list)
    locations = Column(JSON, default=list)
    remote_only = Column(Boolean, default=True)
    employment_types = Column(JSON, default=lambda: ["internship", "co_op"])
    min_fit_score = Column(Integer, default=70)
    require_sponsorship_eligible = Column(Boolean, default=True)
    exclude_companies = Column(JSON, default=list)
    preferred_countries = Column(JSON, default=lambda: ["Worldwide"])
    salary_min = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")
    max_results = Column(Integer, default=100)

    user = relationship("User", back_populates="search_preferences")
