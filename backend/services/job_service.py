"""Job discovery and orchestration service."""
from __future__ import annotations

import asyncio
import datetime
from typing import List

from sqlalchemy.orm import Session

from backend.models.models import (
    Job, JobSource, JobMatch, User, SearchPreference, AgentRun, Event,
)
from backend.sources import get_all_sources, get_source
from backend.sources.base import RawJob, JobSourceAdapter
from backend.services.duplicate_detector import is_duplicate
from backend.services.matching_engine import score_job_match
from backend.services.profile_service import get_or_create_user, get_user_profile_summary
from backend.services.strict_qualification import qualify_job


def save_raw_jobs(db: Session, raw_jobs: List[RawJob], source_name: str, user: User = None) -> int:
    """Save normalized jobs to database, skipping duplicates. Returns count saved."""
    existing_jobs = db.query(Job).filter(Job.is_duplicate == False).all()
    saved = 0
    adapter = get_source(source_name)

    for raw in raw_jobs:
        normalized = adapter.normalize(raw)
        decision = qualify_job(normalized, user)
        if not decision["qualified"]:
            # Reject before the application/matching pipeline. The discovery run retains counts.
            continue

        # Check for duplicates against existing DB jobs
        dup_id = is_duplicate(normalized, existing_jobs)
        if dup_id is not None:
            # Record the duplicate source
            canonical = db.query(Job).filter(Job.id == dup_id).first()
            if canonical:
                dups = canonical.duplicate_sources or []
                if source_name not in dups:
                    dups.append(source_name)
                    canonical.duplicate_sources = dups
            continue

        job = Job(
            external_id=normalized.get("external_id", ""),
            title=normalized["title"],
            company=normalized["company"],
            location=normalized.get("location", ""),
            remote_type=normalized.get("remote_type", "remote"),
            employment_type=normalized.get("employment_type", ""),
            internship_or_fulltime=normalized.get("internship_or_fulltime", ""),
            country=normalized.get("country", ""),
            salary_min=normalized.get("salary_min"),
            salary_max=normalized.get("salary_max"),
            currency=normalized.get("currency", ""),
            description=normalized.get("description", ""),
            requirements=normalized.get("requirements", ""),
            preferred_qualifications=normalized.get("preferred_qualifications", ""),
            skills=normalized.get("skills", []),
            experience_required=normalized.get("experience_required", ""),
            visa_information=normalized.get("visa_information", ""),
            sponsorship_information=normalized.get("sponsorship_information", ""),
            application_url=normalized.get("application_url", ""),
            source_name=source_name,
            source_url=normalized.get("source_url", ""),
            date_posted=normalized.get("date_posted", ""),
            raw_data=normalized.get("raw_data", {}),
        )
        db.add(job)
        existing_jobs.append(job)  # Add to list for dedup of current batch
        saved += 1

    db.commit()
    return saved


async def run_discovery(
    db: Session,
    keywords: List[str] = None,
    source_names: List[str] = None,
    limit_per_source: int = 50,
) -> dict:
    """
    Run a full job discovery cycle across all enabled sources.
    Returns summary of results.
    """
    user = get_or_create_user(db)

    # Get search preferences
    prefs = db.query(SearchPreference).filter(SearchPreference.user_id == user.id).first()
    if prefs:
        keywords = keywords or prefs.keywords
        if prefs.locations and prefs.locations != ["Worldwide"]:
            pass  # Could filter by location

    if not keywords:
        keywords = [
            "Software Engineer Intern",
            "Data Science Intern",
            "Machine Learning Intern",
            "AI Intern",
            "Backend Engineer",
        ]

    # Create agent run record
    agent_run = AgentRun(
        agent_name="job_discovery",
        status="running",
        task=f"Discovering jobs with keywords: {', '.join(keywords[:5])}",
        input_summary=f"Sources: {source_names or 'all'}, Keywords: {len(keywords)}",
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    results = {"total_found": 0, "saved": 0, "sources": {}, "errors": []}

    try:
        sources = [get_source(n) for n in source_names] if source_names else get_all_sources()

        for source in sources:
            try:
                raw_jobs = await source.search(keywords, limit=limit_per_source)
                saved = save_raw_jobs(db, raw_jobs, source.name, user)
                results["sources"][source.name] = {
                    "found": len(raw_jobs),
                    "saved": saved,
                }
                results["total_found"] += len(raw_jobs)
                results["saved"] += saved

                # Update source record
                src_record = db.query(JobSource).filter(JobSource.name == source.name).first()
                if src_record:
                    src_record.last_run = datetime.datetime.utcnow()
                    src_record.jobs_found += len(raw_jobs)
                else:
                    db.add(JobSource(
                        name=source.name,
                        adapter_class=type(source).__name__,
                        is_active=True,
                        last_run=datetime.datetime.utcnow(),
                        jobs_found=len(raw_jobs),
                    ))

            except Exception as e:
                results["errors"].append(f"{source.name}: {str(e)}")

        db.commit()

        # Run matching after discovery
        unmatched_jobs = db.query(Job).filter(
            Job.is_duplicate == False,
            ~Job.id.in_(db.query(JobMatch.job_id))
        ).limit(200).all()

        matched_count = 0
        for job in unmatched_jobs:
            match_result = score_job_match(user, job)
            match = JobMatch(job_id=job.id, user_id=user.id, **match_result)
            db.add(match)
            matched_count += 1

        db.commit()

        # Log event
        event = Event(
            event_type="discovery_complete",
            title="Job Discovery Complete",
            message=f"Found {results['total_found']} jobs, saved {results['saved']}, matched {matched_count}",
            event_metadata=results,
        )
        db.add(event)

        # Update agent run
        agent_run.status = "completed"
        agent_run.outputs = results
        agent_run.completed_at = datetime.datetime.utcnow()
        agent_run.duration_seconds = (agent_run.completed_at - agent_run.started_at).total_seconds()
        db.commit()

    except Exception as e:
        agent_run.status = "failed"
        agent_run.errors = [str(e)]
        agent_run.completed_at = datetime.datetime.utcnow()
        db.commit()
        results["errors"].append(str(e))

    return results


def get_dashboard_stats(db: Session) -> dict:
    """Get dashboard statistics."""
    from sqlalchemy import func

    user = get_or_create_user(db)

    total_jobs = db.query(Job).filter(Job.is_duplicate == False).count()
    total_matches = db.query(JobMatch).filter(JobMatch.fit_score >= 60).count()
    total_apps = db.query(Application).filter(Application.user_id == user.id).count() if False else 0
    applied = 0
    interviews = 0

    # Import Application here to avoid circular
    from backend.models.models import Application
    total_apps = db.query(Application).filter(Application.user_id == user.id).count()
    applied = db.query(Application).filter(Application.user_id == user.id, Application.status == "applied").count()
    interviews = db.query(Application).filter(Application.user_id == user.id, Application.status == "interview").count()

    avg_score = db.query(func.avg(JobMatch.fit_score)).scalar() or 0

    # Top companies by match count
    top_companies_raw = (
        db.query(Job.company, func.count(JobMatch.id))
        .join(JobMatch, JobMatch.job_id == Job.id)
        .filter(JobMatch.fit_score >= 60)
        .group_by(Job.company)
        .order_by(func.count(JobMatch.id).desc())
        .limit(10)
        .all()
    )

    return {
        "jobs_discovered": total_jobs,
        "jobs_matching": total_matches,
        "applications_prepared": total_apps,
        "applications_approved": applied,
        "applications_submitted": applied,
        "interview_count": interviews,
        "response_rate": round(interviews / max(applied, 1) * 100, 1),
        "top_companies": [{"name": c, "count": n} for c, n in top_companies_raw],
        "top_categories": [],
        "average_fit_score": round(float(avg_score), 1),
    }
