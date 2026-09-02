"""Profile management service."""
from __future__ import annotations

import os
import json
import shutil
from pathlib import Path
from typing import Optional

import pymupdf
from sqlalchemy.orm import Session

from backend.models.models import (
    User, Education, Skill, Project, Experience, Certification, Resume,
)
from backend.models.schemas import (
    UserCreate, UserUpdate, EducationCreate, SkillCreate,
    ProjectCreate, ExperienceCreate, CertificationCreate,
)
from backend.config import get_settings


settings = get_settings()


def get_or_create_user(db: Session) -> User:
    """Get the existing user or create default one."""
    user = db.query(User).first()
    if not user:
        user = User()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def update_user(db: Session, data: UserUpdate) -> User:
    """Update the user profile."""
    user = get_or_create_user(db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def add_education(db: Session, edu: EducationCreate) -> Education:
    user = get_or_create_user(db)
    entry = Education(user_id=user.id, **edu.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_skill(db: Session, skill: SkillCreate) -> Skill:
    user = get_or_create_user(db)
    entry = Skill(user_id=user.id, **skill.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_project(db: Session, project: ProjectCreate) -> Project:
    user = get_or_create_user(db)
    entry = Project(user_id=user.id, **project.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_experience(db: Session, exp: ExperienceCreate) -> Experience:
    user = get_or_create_user(db)
    entry = Experience(user_id=user.id, **exp.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_certification(db: Session, cert: CertificationCreate) -> Certification:
    user = get_or_create_user(db)
    entry = Certification(user_id=user.id, **cert.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def upload_resume(db: Session, file_path: str, filename: str) -> Resume:
    """Save resume and extract text."""
    user = get_or_create_user(db)

    # Parse resume
    parsed_data = parse_resume_pdf(file_path)

    resume = Resume(
        user_id=user.id,
        filename=filename,
        file_path=file_path,
        parsed_data=parsed_data,
        is_primary=True,
    )
    db.add(resume)

    # Mark others as non-primary
    db.query(Resume).filter(Resume.user_id == user.id, Resume.id != resume.id).update({"is_primary": False})

    db.commit()
    db.refresh(resume)
    return resume


def parse_resume_pdf(file_path: str) -> dict:
    """Extract structured data from a resume PDF."""
    try:
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        # Simple rule-based extraction
        parsed = {
            "full_text": text,
            "name": "",
            "email": "",
            "phone": "",
            "education": [],
            "skills": [],
            "experience": [],
            "projects": [],
        }

        lines = text.strip().split("\n")

        # Extract name (first non-empty line)
        for line in lines:
            stripped = line.strip()
            if stripped and len(stripped) > 2:
                parsed["name"] = stripped
                break

        # Extract email
        import re
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            parsed["email"] = email_match.group(0)

        # Extract phone
        phone_match = re.search(r'[\+]?[\d][\d\s\-]{8,15}', text)
        if phone_match:
            parsed["phone"] = phone_match.group(0).strip()

        # Extract skills from common patterns
        skill_keywords = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
            "React", "Angular", "Vue", "FastAPI", "Django", "Flask", "Node.js",
            "SQL", "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "GCP", "Azure", "Git", "Linux", "Machine Learning",
            "TensorFlow", "PyTorch", "LangChain", "RAG", "XGBoost",
            "HTML", "CSS", "Tailwind", "Next.js", "Express",
        ]
        for skill in skill_keywords:
            if skill.lower() in text.lower():
                parsed["skills"].append(skill)

        return parsed
    except Exception as e:
        return {"full_text": "", "error": str(e)}


def get_user_profile_summary(db: Session) -> str:
    """Generate a text summary of the user profile for AI matching."""
    user = get_or_create_user(db)

    parts = [
        f"Name: {user.name}",
        f"Email: {user.email}",
        f"Phone: {user.phone}",
        f"Location: {user.location}",
        f"Citizenship: {user.citizenship}",
        f"Requires Sponsorship: {'Yes' if user.requires_sponsorship else 'No'}",
        f"Availability: {user.availability}",
        f"Preferred Job Type: {user.preferred_job_type}",
        f"LinkedIn: {user.linkedin_url}",
        f"GitHub: {user.github_url}",
        "",
        "Education:",
    ]

    for edu in user.education_entries:
        parts.append(f"  - {edu.degree} in {edu.field_of_study}, {edu.university}, {edu.start_date} - {edu.end_date}, GPA: {edu.gpa}")

    parts.append("\nSkills:")
    skills_by_cat = {}
    for s in user.skills:
        skills_by_cat.setdefault(s.category, []).append(s.name)
    for cat, skills in skills_by_cat.items():
        parts.append(f"  {cat}: {', '.join(skills)}")

    parts.append("\nExperience:")
    for exp in user.experiences:
        parts.append(f"  - {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})")
        if exp.description:
            parts.append(f"    {exp.description[:200]}")

    parts.append("\nProjects:")
    for proj in user.projects:
        parts.append(f"  - {proj.name}: {proj.description[:150]}")
        parts.append(f"    Tech: {proj.technologies}")

    if user.certifications:
        parts.append("\nCertifications:")
        for cert in user.certifications:
            parts.append(f"  - {cert.name} ({cert.issuer})")

    return "\n".join(parts)
