"""Duplicate job detection service."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.models import Job


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def similarity(a: str, b: str) -> float:
    """Calculate text similarity ratio."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def is_duplicate(new_job: dict, existing_jobs: List[Job]) -> Optional[int]:
    """
    Check if a new job is a duplicate of an existing one.
    Returns the canonical job ID if duplicate, None otherwise.
    """
    new_title = normalize_text(new_job.get("title", ""))
    new_company = normalize_text(new_job.get("company", ""))
    new_url = (new_job.get("application_url") or "").strip().lower()
    new_desc = new_job.get("description", "")

    for existing in existing_jobs:
        # Check 1: Same application URL
        if new_url and existing.application_url:
            if new_url == existing.application_url.lower().strip():
                return existing.id

        # Check 2: Same external_id
        if new_job.get("external_id") and existing.external_id:
            if new_job["external_id"] == existing.external_id:
                return existing.id

        # Check 3: Same company + similar title
        ext_title = normalize_text(existing.title)
        ext_company = normalize_text(existing.company)

        if new_company == ext_company:
            title_sim = similarity(new_title, ext_title)
            if title_sim > 0.85:
                return existing.id

            # Check 4: Same company + same location + high description similarity
            if new_job.get("location", "").lower().strip() == (existing.location or "").lower().strip():
                desc_sim = similarity(new_desc[:500], (existing.description or "")[:500])
                if desc_sim > 0.70:
                    return existing.id

    return None


def detect_and_mark_duplicates(db: Session) -> int:
    """Scan all jobs and mark duplicates. Returns count of duplicates found."""
    jobs = db.query(Job).filter(Job.is_duplicate == False).order_by(Job.discovered_at.asc()).all()
    dup_count = 0

    seen_groups = {}  # canonical_job_id -> list of duplicates

    for i, job in enumerate(jobs):
        if job.is_duplicate:
            continue

        later_jobs = jobs[i+1:]
        for later in later_jobs:
            if later.is_duplicate:
                continue

            result = is_duplicate(
                {
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "application_url": job.application_url,
                    "description": job.description,
                    "external_id": job.external_id,
                },
                [later],
            )

            if result is not None:
                # job is a duplicate of 'later' (which came after, so 'later' is canonical)
                # Actually 'later' is newer, mark the older one as dup pointing to newer
                later_existing = db.query(Job).filter(Job.id == later.id).first()
                if later_existing:
                    # Mark this job as duplicate of later
                    existing_dups = later_existing.duplicate_sources or []
                    if job.source_name not in existing_dups:
                        existing_dups.append(job.source_name)
                    later_existing.duplicate_sources = existing_dups
                    dup_count += 1

    db.commit()
    return dup_count
