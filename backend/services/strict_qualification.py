"""Reject-by-default hard filters for the autonomous remote-internship pipeline."""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict

TECH = re.compile(r"\b(software|software development|software engineer|data scien|data scientist|artificial intelligence|ai engineering|machine learning|\bml\b|data analy|data engineering|backend|full[ -]?stack|computer vision|natural language processing|deep learning|mlops|ai research|ml research|research engineer)\b", re.I)
FORBIDDEN = re.compile(r"\b(marketing|human resources|\bhr\b|recruit|sales|business development|finance|accounting|legal|operations|customer support|content writ|social media|graphic design|mechanical|civil|electrical|chemical|medical|administrative|general business)\b", re.I)
SENIOR = re.compile(r"\b(senior|staff|lead|manager|director|principal)\b|\b[3-9]\+?\s*years?\b", re.I)
INTERN = re.compile(r"\b(intern(?:ship)?|co[ -]?op|student internship)\b", re.I)
REMOTE = re.compile(r"\b(remote|fully remote|remote worldwide|worldwide remote|work from anywhere|distributed|remote internship)\b", re.I)
AMBIGUOUS_REMOTE = re.compile(r"\b(hybrid|remote\s*/\s*hybrid|remote possible|flexible location|on[ -]?site or remote)\b", re.I)


def qualify_job(job: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
    """Return structured confidence scores; any uncertainty rejects the job."""
    title = str(job.get("title", ""))
    text = f"{title} {job.get('description', '')} {job.get('location', '')}"
    internship_probability = 0.98 if INTERN.search(title) else (0.72 if INTERN.search(text) else 0.01)
    remote_probability = 0.98 if REMOTE.search(text) and not AMBIGUOUS_REMOTE.search(text) else 0.01
    technical_relevance = 0.01 if FORBIDDEN.search(title) else (0.96 if TECH.search(title) else 0.01)
    valid_url = str(job.get("application_url", "")).startswith(("https://", "http://"))
    bad = re.search(r"\b(expired|closed|no longer accepting|pay to apply|telegram|whatsapp)\b", text, re.I)
    job_validity = 0.95 if valid_url and not bad and job.get("company") else 0.01
    restricted_us = re.search(r"\b(us only|must be authorized to work in the united states)\b", text, re.I)
    citizenship = str(getattr(user, "citizenship", "")).lower()
    eligibility = "NOT_ELIGIBLE" if restricted_us and "united states" not in citizenship and citizenship not in {"us", "usa", "american"} else "LIKELY_ELIGIBLE"
    reasons = []
    if internship_probability < .90: reasons.append("not_explicit_internship")
    if remote_probability < .90: reasons.append("not_confirmed_remote")
    if technical_relevance < .85: reasons.append("unrelated_technical_domain")
    if SENIOR.search(text): reasons.append("senior_or_substantial_experience")
    if job_validity < .90: reasons.append("invalid_or_suspicious")
    if eligibility == "NOT_ELIGIBLE": reasons.append("not_eligible")
    return {"qualified": not reasons, "reasons": reasons, "internship_probability": internship_probability, "remote_probability": remote_probability, "technical_relevance": technical_relevance, "job_validity": job_validity, "remote_status": "CONFIRMED_REMOTE" if remote_probability >= .90 else "NOT_CONFIRMED", "remote_confidence": remote_probability, "eligibility": eligibility}
