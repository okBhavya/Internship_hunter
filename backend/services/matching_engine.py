"""Job matching and scoring engine."""
from __future__ import annotations

import re
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session

from backend.models.models import User, Job, JobMatch


# Skill similarity mapping for fuzzy matching
SKILL_ALIASES = {
    "javascript": ["js", "es6", "es2015", "ecmascript"],
    "typescript": ["ts"],
    "python": ["py"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs", "node"],
    "fastapi": ["fast api"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "computer vision": ["cv"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google cloud"],
    "microsoft azure": ["azure"],
    "postgres": ["postgresql"],
    "mongo": ["mongodb"],
    "kubernetes": ["k8s"],
    "langchain": ["lang chain"],
    "pytorch": ["py torch"],
    "tensorflow": ["tf"],
}


def normalize_skill(skill: str) -> str:
    s = skill.lower().strip()
    for suffix in [" experience", " knowledge", " proficiency", " expertise"]:
        s = s.replace(suffix, "")
    return s


def skill_matches(user_skill: str, required_skill: str) -> bool:
    us = normalize_skill(user_skill)
    rs = normalize_skill(required_skill)
    if us == rs or rs in us or us in rs:
        return True
    for main, aliases in SKILL_ALIASES.items():
        if (rs == main or rs in aliases) and (us == main or us in aliases):
            return True
        if (us == main or us in aliases) and (rs == main or rs in aliases):
            return True
    return False


def score_job_match(user: User, job: Job) -> dict:
    """
    Score how well a job matches the user's profile (0-100).
    Prioritizes internships and target fields, but scores all jobs fairly.
    """
    title_lower = (job.title or "").lower()
    desc_lower = (job.description or "").lower()

    # Gather user skills
    user_skills = set()
    for s in user.skills:
        user_skills.add(normalize_skill(s.name))

    # ── Determine if this is an internship / entry-level ──
    intern_words = {"intern", "internship", "co-op", "coop", "trainee", "apprentice"}
    entry_words = {"junior", "entry", "associate", "new grad", "graduate"}
    is_internship = any(w in title_lower for w in intern_words)
    is_entry_level = any(w in title_lower for w in entry_words)

    # ── Determine if in target field (software/AI/DS/ML) ──
    field_words = [
        "software", "engineer", "developer", "data", "machine learning",
        "ml", "ai", "backend", "frontend", "full stack", "fullstack",
        "python", "java", "devops", "cloud",
    ]
    is_target_field = any(w in title_lower for w in field_words)

    # ── Role Match (0-20) ──
    if is_internship:
        role_score = 20  # Best fit — exactly what we want
    elif is_entry_level:
        role_score = 18  # Great fit
    elif job.internship_or_fulltime == "internship":
        role_score = 18
    elif job.internship_or_fulltime in ("co_op", "entry_level"):
        role_score = 16
    elif is_target_field:
        role_score = 12  # Good field match, but full-time
    else:
        role_score = 5  # Off-field

    # ── Technical Skill Match (0-30) ──
    job_skills_raw = job.skills or []
    job_skills_lower = {normalize_skill(s) for s in job_skills_raw}

    if job_skills_lower:
        matched = sum(1 for js in job_skills_lower if any(skill_matches(us, js) for us in user_skills))
        technical_score = min(30, (matched / max(len(job_skills_lower), 1)) * 30)
    else:
        # No structured skills — check title for key technologies
        tech_in_title = [
            "python", "java", "javascript", "typescript", "react", "node",
            "data", "machine learning", "ai", "backend", "frontend",
        ]
        title_matches = sum(1 for t in tech_in_title if t in title_lower)
        technical_score = min(20, title_matches * 5)

    missing = []
    if job_skills_lower:
        missing = [s for s in job_skills_lower if not any(skill_matches(us, s) for us in user_skills)]

    # ── Experience Match (0-15) ──
    exp_score = 12
    exp_text = (job.experience_required or "").lower()
    if "5+" in exp_text or "senior" in exp_text:
        exp_score = 3
    elif "3+" in exp_text or "mid" in exp_text:
        exp_score = 7
    elif "1+" in exp_text:
        exp_score = 12
    # Internships typically don't require experience
    if is_internship:
        exp_score = 15

    # ── Education Match (0-10) ──
    edu_score = 8
    if any(deg in desc_lower for deg in ["bachelor", "b.e.", "b.tech", "bs.", "bs "]):
        edu_score = 10
    elif any(deg in desc_lower for deg in ["master", "m.tech", "ms.", "ms "]):
        edu_score = 6

    # ── Location / Remote Match (0-10) ──
    remote_type = (job.remote_type or "").lower()
    if "remote" in remote_type:
        location_score = 10
    elif "hybrid" in remote_type:
        location_score = 7
    elif "onsite" in remote_type:
        if user.location.lower() in (job.location or "").lower():
            location_score = 9
        else:
            location_score = 3
    else:
        location_score = 8

    # ── Work Authorization (0-5) ──
    auth_score = 4
    sponsorship_info = (job.sponsorship_information or "").lower()
    if "no sponsorship" in sponsorship_info or "no visa" in sponsorship_info:
        auth_score = 1
    elif "sponsorship" in sponsorship_info and "available" in sponsorship_info:
        auth_score = 5

    # ── Project Match (0-5) ──
    project_score = 3
    if job_skills_lower and any(
        skill_matches(normalize_skill(s.name), js)
        for s in user.skills
        for js in job_skills_lower
    ):
        project_score = 5

    # ── Application Feasibility (0-5) ──
    feasibility_score = 5 if job.application_url else 2

    # ── Total Score ──
    total = (
        technical_score + role_score + exp_score + edu_score
        + location_score + auth_score + project_score + feasibility_score
    )
    total = min(100, round(total))

    # ── Determine recommendation ──
    if total >= 75:
        recommendation = "APPLY"
    elif total >= 55:
        recommendation = "CONSIDER"
    else:
        recommendation = "SKIP"

    # ── Strengths ──
    strengths = []
    if technical_score >= 20:
        strengths.append("Strong technical skill match")
    if is_internship:
        strengths.append("Internship — ideal experience level")
    if is_entry_level:
        strengths.append("Entry-level role — good fit")
    if "remote" in remote_type:
        strengths.append("Remote position")
    if project_score >= 4:
        strengths.append("Relevant project experience")
    if is_target_field:
        strengths.append("Target field (software/AI/DS/ML)")

    # ── Concerns ──
    concerns = []
    if missing:
        concerns.append(f"Missing skills: {', '.join(missing[:5])}")
    if auth_score <= 2:
        concerns.append("Sponsorship may not be available")
    if not is_internship and not is_entry_level:
        concerns.append("Full-time role — may require more experience")

    # ── Explanation ──
    explanation = (
        f"Technical: {round(technical_score)}/30 | "
        f"Role: {round(role_score)}/20 | "
        f"Experience: {round(exp_score)}/15 | "
        f"Education: {round(edu_score)}/10 | "
        f"Remote: {round(location_score)}/10 | "
        f"Auth: {round(auth_score)}/5 | "
        f"Projects: {round(project_score)}/5 | "
        f"Feasibility: {round(feasibility_score)}/5"
    )

    return {
        "fit_score": total,
        "technical_match": round(technical_score),
        "role_match": round(role_score),
        "experience_match": round(exp_score),
        "education_match": round(edu_score),
        "location_match": round(location_score),
        "authorization_match": round(auth_score),
        "project_match": round(project_score),
        "feasibility_match": round(feasibility_score),
        "missing_skills": missing[:10],
        "strengths": strengths,
        "concerns": concerns,
        "recommendation": recommendation,
        "explanation": explanation,
    }


def match_jobs_for_user(db: Session, user: User, limit: int = 100) -> List[JobMatch]:
    """Match all unduplicated jobs against user profile."""
    jobs = db.query(Job).filter(Job.is_duplicate == False).order_by(Job.discovered_at.desc()).limit(limit).all()
    matches = []
    for job in jobs:
        existing = db.query(JobMatch).filter(
            JobMatch.job_id == job.id,
            JobMatch.user_id == user.id,
        ).first()
        result = score_job_match(user, job)
        if existing:
            for k, v in result.items():
                setattr(existing, k, v)
            matches.append(existing)
        else:
            match = JobMatch(job_id=job.id, user_id=user.id, **result)
            db.add(match)
            matches.append(match)
    db.commit()
    return matches
