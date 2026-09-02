"""Application workflow service."""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.models import (
    User, Job, JobMatch, Application, ApplicationMaterial,
    QuestionAnswer, Notification,
)
from backend.services.material_generator import (
    generate_cover_letter, generate_application_summary,
    generate_skills_summary, generate_why_company, generate_why_role,
    generate_recruiter_message, generate_standard_answers,
    prepare_application_materials, classify_question,
)
from backend.services.profile_service import get_or_create_user


def start_application(db: Session, job_id: int, mode: str = "prepare") -> Application:
    """Start an application for a job."""
    user = get_or_create_user(db)
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # Check if application already exists
    existing = db.query(Application).filter(
        Application.user_id == user.id,
        Application.job_id == job_id,
    ).first()
    if existing:
        return existing

    # Get match
    match = db.query(JobMatch).filter(
        JobMatch.job_id == job_id,
        JobMatch.user_id == user.id,
    ).first()

    # Create application
    app = Application(
        user_id=user.id,
        job_id=job_id,
        status="discovered",
        resume_version="primary",
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    if mode in ("prepare", "approval"):
        # Generate materials
        materials = prepare_application_materials(db, user, job, match)

        app.cover_letter = materials["cover_letter"]
        app.status = "prepared"

        # Save individual materials
        for mat_type, content in materials.items():
            if mat_type == "question_answers":
                for q, a in content.items():
                    q_type = classify_question(q)
                    qa = QuestionAnswer(
                        application_id=app.id,
                        question_text=q,
                        question_type=q_type,
                        suggested_answer=a,
                    )
                    db.add(qa)
            else:
                mat = ApplicationMaterial(
                    application_id=app.id,
                    material_type=mat_type,
                    content=str(content),
                )
                db.add(mat)

        if mode == "approval":
            app.status = "awaiting_approval"

    db.commit()
    db.refresh(app)

    # Create notification
    notif = Notification(
        user_id=user.id,
        title=f"Application prepared for {job.title} at {job.company}",
        message=f"Materials generated for {job.title}. Ready for review.",
        notification_type="info" if mode == "prepare" else "approval_needed",
        action_url=f"/applications/{app.id}",
    )
    db.add(notif)
    db.commit()

    return app


def approve_application(db: Session, application_id: int) -> Application:
    """Approve an application."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError(f"Application {application_id} not found")

    app.status = "applied"
    app.date_applied = datetime.datetime.utcnow()
    db.commit()
    db.refresh(app)

    # Notify
    job = db.query(Job).filter(Job.id == app.job_id).first()
    notif = Notification(
        user_id=app.user_id,
        title=f"Application approved: {job.title if job else 'Unknown'}",
        message=f"Application has been marked as submitted.",
        notification_type="success",
    )
    db.add(notif)
    db.commit()

    return app


def update_application_status(db: Session, application_id: int, status: str, notes: str = "") -> Application:
    """Update application status."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError(f"Application {application_id} not found")

    app.status = status
    app.last_updated = datetime.datetime.utcnow()
    if notes:
        app.notes = (app.notes or "") + f"\n[{datetime.datetime.utcnow().isoformat()}] {notes}"

    if status == "rejected":
        app.rejection_date = datetime.datetime.utcnow().isoformat()

    db.commit()
    db.refresh(app)
    return app


def skip_application(db: Session, application_id: int) -> None:
    """Skip/withdraw an application."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if app:
        app.status = "withdrawn"
        app.last_updated = datetime.datetime.utcnow()
        db.commit()


def get_application_materials(db: Session, application_id: int) -> dict:
    """Get all materials for an application."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return {}

    materials = db.query(ApplicationMaterial).filter(
        ApplicationMaterial.application_id == application_id
    ).all()

    qas = db.query(QuestionAnswer).filter(
        QuestionAnswer.application_id == application_id
    ).all()

    result = {
        "resume": "",
        "cover_letter": app.cover_letter or "",
        "summary": "",
        "skills_summary": "",
        "why_company": "",
        "why_role": "",
        "recruiter_message": "",
        "question_answers": [{"question": qa.question_text, "answer": qa.suggested_answer, "type": qa.question_type, "approved": qa.approved} for qa in qas],
    }

    for mat in materials:
        result[mat.material_type] = mat.content

    return result
