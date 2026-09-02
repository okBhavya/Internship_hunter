"""Job matching and scoring engine."""
from __future__ import annotations

import re
from typing import List

from sqlalchemy.orm import Session

from backend.models.models import User, Job, JobMatch


SKILL_ALIASES = {
    "javascript": ["js", "es6", "ecmascript"],
    "typescript": ["ts"],
    "python": ["py"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs", "node"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp"],
    "postgres": ["postgresql"],
    "kubernetes": ["k8s"],
    "langchain": ["lang chain"],
    "pytorch": ["py torch"],
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
    return False


def _extract_skills_from_job(job: Job) -> List[str]:
    """Extract skills to match against. Only uses the structured skills field."""
    if job.skills:
        return job.skills
    return []


def score_job_match(user: User, job: Job) -> dict:
    user_skills = {normalize_skill(s.name) for s in user.skills}
    job_skills_raw = _extract_skills_from_job(job)
    job_skills = {normalize_skill(s) for s in job_skills_raw}

    # ── Technical Skill Match (0-30) ──
    if job_skills:
        matched = sum(1 for js in job_skills if any(skill_matches(us, js) for us in user_skills))
        technical_score = round(min(30, (matched / max(len(job_skills), 1)) * 30))
        missing = [s for s in job_skills_raw if not any(skill_matches(us, s) for us in user_skills)]
    else:
        # No structured skills listed — infer from title + description keywords
        desc_lower = (job.description or "").lower() + " " + (job.title or "").lower()
        title_skills = []
        for s in user.skills:
            if s.name.lower() in desc_lower:
                title_skills.append(s.name)
        if title_skills:
            technical_score = min(20, len(title_skills) * 5)
        else:
            technical_score = 10  # neutral when no skills data available
        missing = []

    # ── Role Match (0-20) ──
    title_lower = (job.title or "").lower()
    is_intern = any(w in title_lower for w in ["intern", "internship", "co-op", "coop"])
    is_junior = any(w in title_lower for w in ["junior", "entry", "associate", "graduate", "new grad", "trainee", "jr."])
    is_relevant_title = any(w in title_lower for w in [
        "software", "data", "machine learning", "ai", "backend", "frontend",
        "full stack", "fullstack", "developer", "engineer", "scientist", "analyst",
        "ml ", "devops", "platform", "infrastructure",
    ])
    is_too_senior = any(w in title_lower for w in ["senior", "sr.", "lead", "principal", "staff", "director", "vp"])

    if is_intern:
        role_score = 20
    elif is_junior:
        role_score = 18
    elif is_relevant_title and not is_too_senior:
        role_score = 14
    elif is_too_senior:
        role_score = 5
    else:
        role_score = 8

    # ── Experience Match (0-15) ──
    desc_lower = (job.description or "").lower()
    exp_text = (job.experience_required or "").lower() + " " + desc_lower
    if any(w in exp_text for w in ["5+ years", "5+ yrs", "senior", "7+ years"]):
        exp_score = 3
    elif any(w in exp_text for w in ["3+ years", "3+ yrs", "mid-level"]):
        exp_score = 7
    elif any(w in exp_text for w in ["1+ years", "1+ yrs", "entry level", "no experience"]):
        exp_score = 12
    elif is_intern or is_junior:
        exp_score = 14
    else:
        exp_score = 10

    # ── Education Match (0-10) ──
    edu_score = 8
    if any(d in desc_lower for d in ["bachelor", "b.e.", "b.tech", "bs.", "bs "]):
        edu_score = 10
    elif any(d in desc_lower for d in ["master", "m.tech", "ms.", "ms "]):
        edu_score = 6
    elif is_intern:
        edu_score = 9

    # ── Location / Remote Match (0-10) ──
    remote_type = (job.remote_type or "").lower()
    if "remote" in remote_type:
        location_score = 10
    elif "hybrid" in remote_type:
        location_score = 7
    elif user.location.lower() in (job.location or "").lower():
        location_score = 9
    else:
        location_score = 4

    # ── Work Authorization (0-5) ──
    auth_score = 4
    sponsorship_info = (job.sponsorship_information or "").lower()
    visa_info = (job.visa_information or "").lower()
    if "no sponsorship" in sponsorship_info or "no visa" in visa_info:
        auth_score = 1
    elif "sponsorship" in sponsorship_info and "available" in sponsorship_info:
        auth_score = 5

    # ── Project Match (0-5) ──
    project_score = 3
    if any(tech.lower() in desc_lower for p in user.projects for tech in p.technologies.split(",") if tech.strip()):
        project_score = 5

    # ── Application Feasibility (0-5) ──
    feasibility_score = 5 if job.application_url else 2

    # ── Total ──
    total = min(100, round(
        technical_score + role_score + exp_score + edu_score +
        location_score + auth_score + project_score + feasibility_score
    ))

    if total >= 75:
        recommendation = "APPLY"
    elif total >= 55:
        recommendation = "CONSIDER"
    else:
        recommendation = "SKIP"

    strengths = []
    if technical_score >= 20:
        strengths.append("Strong technical skill match")
    elif technical_score >= 10 and job_skills:
        strengths.append("Partial technical match")
    if is_intern or is_junior:
        strengths.append("Entry-level / intern role — good fit")
    if "remote" in remote_type:
        strengths.append("Remote position")
    if project_score >= 4:
        strengths.append("Relevant project experience")

    concerns = []
    if missing:
        concerns.append(f"Missing skills: {', '.join(missing[:5])}")
    if auth_score <= 2:
        concerns.append("Sponsorship may not be available")
    if is_too_senior:
        concerns.append("May require more experience than you have")

    explanation = (
        f"Tech: {technical_score}/30 | Role: {role_score}/20 | Exp: {exp_score}/15 | "
        f"Edu: {edu_score}/10 | Location: {location_score}/10 | Auth: {auth_score}/5 | "
        f"Projects: {project_score}/5 | Feasibility: {feasibility_score}/5"
    )

    return {
        "fit_score": total,
        "technical_match": technical_score,
        "role_match": role_score,
        "experience_match": exp_score,
        "education_match": edu_score,
        "location_match": location_score,
        "authorization_match": auth_score,
        "project_match": project_score,
        "feasibility_match": feasibility_score,
        "missing_skills": missing[:10],
        "strengths": strengths,
        "concerns": concerns,
        "recommendation": recommendation,
        "explanation": explanation,
    }


def match_jobs_for_user(db: Session, user: User, limit: int = 100) -> List[JobMatch]:
    jobs = db.query(Job).filter(Job.is_duplicate == False).order_by(Job.discovered_at.desc()).limit(limit).all()
    matches = []
    for job in jobs:
        existing = db.query(JobMatch).filter(JobMatch.job_id == job.id, JobMatch.user_id == user.id).first()
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
