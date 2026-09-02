"""Application material generation service."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from backend.models.models import User, Job, JobMatch, Application, ApplicationMaterial


def generate_cover_letter(user: User, job: Job, match: Optional[JobMatch] = None) -> str:
    skills_text = ", ".join(s.name for s in user.skills[:8])
    latest_exp = user.experiences[0] if user.experiences else None
    latest_project = user.projects[0] if user.projects else None
    education = user.education_entries[0] if user.education_entries else None
    degree_info = f"{education.degree} in {education.field_of_study}" if education else "my degree"
    university = education.university if education else "my university"

    exp_highlight = ""
    if latest_exp:
        exp_highlight = f"During my time as {latest_exp.title} at {latest_exp.company}, I {latest_exp.description.split('.')[0].lstrip('- ')}"

    project_highlight = ""
    if latest_project:
        project_highlight = f"I also built {latest_project.name}, which {latest_project.description.split('.')[0]}"

    parts = [
        "Dear Hiring Manager,",
        "",
        f"I am writing to express my strong interest in the {job.title} position at {job.company}. As a {degree_info} student at {university}, I am eager to contribute my skills in {skills_text} to your team.",
        "",
        exp_highlight,
        "",
        project_highlight,
        "",
        f"I am particularly drawn to this role because of the opportunity to work on meaningful problems at {job.company}. The position aligns well with my technical background and career goals.",
    ]

    if user.requires_sponsorship:
        parts.append("")
        parts.append("I am an Indian citizen and would require visa sponsorship for this role.")

    parts.extend([
        "",
        f"I am available {user.availability} and would welcome the opportunity to discuss how my background can contribute to your team's success.",
        "",
        "Thank you for considering my application.",
        "",
        "Best regards,",
        user.name,
        user.email,
        user.phone,
    ])

    return "\n".join(parts)


def generate_application_summary(user: User, job: Job) -> str:
    skills = [s.name for s in user.skills[:8]]
    education = user.education_entries[0] if user.education_entries else None
    exp = user.experiences[0] if user.experiences else None
    parts = [f"{user.name} -- "]
    if education:
        parts.append(f"{education.degree} student at {education.university}. ")
    parts.append(f"Skills: {', '.join(skills)}. ")
    if exp:
        parts.append(f"Experience: {exp.title} at {exp.company}. ")
    parts.append(f"Applying for {job.title} at {job.company}.")
    return "".join(parts)


def generate_skills_summary(user: User, job: Job) -> str:
    job_text = (job.description or "").lower() + " " + (job.requirements or "").lower()
    relevant = [s for s in user.skills if any(w in job_text for w in s.name.lower().split())]
    other = [s for s in user.skills if s not in relevant]
    parts = []
    if relevant:
        parts.append("Relevant: " + ", ".join(s.name for s in relevant[:10]))
    if other:
        parts.append("Additional: " + ", ".join(s.name for s in other[:8]))
    return " | ".join(parts) if parts else "Skills: " + ", ".join(s.name for s in user.skills[:10])


def generate_why_company(user: User, job: Job) -> str:
    desc = (job.description or "").lower()
    strengths = []
    if any(w in desc for w in ["remote", "distributed", "work from anywhere"]):
        strengths.append("commitment to remote work")
    if any(w in desc for w in ["innovat", "cutting-edge", "advanced"]):
        strengths.append("innovative approach to technology")
    if any(w in desc for w in ["grow", "learning", "development"]):
        strengths.append("investment in employee growth")
    if any(w in desc for w in ["impact", "mission", "meaningful"]):
        strengths.append("meaningful impact through their work")
    text = ", ".join(strengths[:2]) if strengths else "innovative work and technical excellence"
    return (
        f"I am excited about {job.company} because of its {text}. "
        f"The {job.title} role offers an opportunity to work with talented engineers on problems that matter."
    )


def generate_why_role(user: User, job: Job) -> str:
    skills = [s.name for s in user.skills[:5]]
    desc = (job.description or "").lower()
    signals = []
    if any(w in desc for w in ["build", "develop", "engineer", "create"]):
        signals.append("building and developing")
    if any(w in desc for w in ["design", "architect", "plan"]):
        signals.append("designing and architecting")
    if any(w in desc for w in ["data", "analy", "model", "train"]):
        signals.append("working with data and models")
    if any(w in desc for w in ["scale", "performance", "optimi"]):
        signals.append("optimizing for scale and performance")
    activity = " ".join(signals[:2]) if signals else "solving real engineering challenges"
    return (
        f"The {job.title} position at {job.company} matches my skills in "
        f"{', '.join(skills)}. I am passionate about {activity} "
        f"and this role would let me apply my experience with real-world engineering challenges."
    )


def generate_recruiter_message(user: User, job: Job) -> str:
    edu = user.education_entries[0] if user.education_entries else None
    degree = edu.degree if edu else "CS"
    university = edu.university if edu else "my university"
    return (
        f"Hi, I am {user.name}, a {degree} student at {university}. "
        f"I am very interested in the {job.title} role at {job.company} "
        f"and believe my experience with {', '.join(s.name for s in user.skills[:4])} "
        f"makes me a strong fit. I would love to connect and learn more."
    )


def generate_standard_answers(user: User, job: Job) -> dict:
    education = user.education_entries[0] if user.education_entries else None
    edu_degree = education.degree if education else "Computer Science"
    edu_university = education.university if education else "my university"
    edu_gpa = education.gpa if education and education.gpa else None
    skills_str = ", ".join(s.name for s in user.skills[:5])
    sponsor_text = "I would require visa sponsorship." if user.requires_sponsorship else "I do not require sponsorship."
    sponsor_detail = (
        "Yes, I require visa sponsorship as an Indian citizen."
        if user.requires_sponsorship
        else "No, I do not require sponsorship."
    )

    return {
        "How did you hear about this position?": "I found this position through an online job board and was immediately drawn to the role and company.",
        "Are you legally authorized to work?": f"I am an Indian citizen. {sponsor_text}",
        "When can you start?": f"I am available {user.availability}.",
        "What is your expected salary?": "I am flexible and open to discussion based on the role and market standards.",
        "Tell us about yourself": f"I am {user.name}, a {edu_degree} student at {edu_university} with experience in {skills_str}.",
        "What is your GPA?": edu_gpa if edu_gpa else "I would prefer not to disclose at this time.",
        "Do you require visa sponsorship?": sponsor_detail,
        "Link to your portfolio": user.portfolio_url or "https://github.com/bhavyagupta",
        "Link to your GitHub": user.github_url,
        "Link to your LinkedIn": user.linkedin_url,
    }


def prepare_application_materials(db: Session, user: User, job: Job, match: Optional[JobMatch] = None) -> dict:
    return {
        "resume": "(Tailored resume content would go here)",
        "cover_letter": generate_cover_letter(user, job, match),
        "summary": generate_application_summary(user, job),
        "skills_summary": generate_skills_summary(user, job),
        "why_company": generate_why_company(user, job),
        "why_role": generate_why_role(user, job),
        "recruiter_message": generate_recruiter_message(user, job),
        "question_answers": generate_standard_answers(user, job),
    }


def classify_question(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["sponsor", "visa", "authorization", "legally", "work permit"]):
        return "sponsorship"
    if any(w in q for w in ["salary", "compensation", "pay", "expected"]):
        return "salary"
    if any(w in q for w in ["available", "start date", "when can you"]):
        return "availability"
    if any(w in q for w in ["tell us about", "describe yourself", "bio", "summary"]):
        return "free_form"
    if any(w in q for w in ["gpa", "grade", "transcript", "degree", "university"]):
        return "factual"
    if any(w in q for w in ["experience", "previous", "worked at", "project"]):
        return "experience"
    if any(w in q for w in ["technical", "programming", "algorithm", "system design"]):
        return "technical"
    if any(w in q for w in ["why", "motivation", "interest"]):
        return "behavioral"
    return "general"
