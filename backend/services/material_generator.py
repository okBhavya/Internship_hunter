"""Application material generation service — produces real ATS-friendly content."""
from __future__ import annotations

import re
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.models.models import User, Job, JobMatch, Application, ApplicationMaterial


def _extract_job_skills(job: Job) -> List[str]:
    """Extract key skills/technologies from job description."""
    desc = (job.description or "").lower()
    tech_keywords = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "nodejs", "fastapi", "django", "flask", "spring",
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s",
        "postgresql", "mysql", "mongodb", "redis", "sql",
        "machine learning", "ml", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "git", "ci/cd", "terraform", "linux",
        "rest api", "graphql", "grpc",
        "data science", "data analysis", "sql", "tableau",
        "ai", "artificial intelligence", "llm", "genai",
        "go", "rust", "c++", "c#",
    ]
    found = []
    for kw in tech_keywords:
        if kw in desc:
            found.append(kw)
    return found[:15]


def _generate_ats_resume(user: User, job: Job) -> str:
    """Generate an ATS-friendly plain text resume tailored to the job."""
    education = user.education_entries[0] if user.education_entries else None
    skills = [s.name for s in user.skills]
    job_skills = _extract_job_skills(job)

    # Prioritize skills that match the job
    relevant_skills = [s for s in skills if any(js in s.lower() for js in job_skills)]
    other_skills = [s for s in skills if s not in relevant_skills]
    ordered_skills = relevant_skills + other_skills

    lines = []
    lines.append(f"{(user.name or "UNKNOWN").upper()}")
    lines.append(f"{user.email or ""} | {user.phone or ""} | {user.location or ""}")
    if user.linkedin_url:
        lines.append(f"LinkedIn: {user.linkedin_url}")
    if user.github_url:
        lines.append(f"GitHub: {user.github_url}")
    lines.append("")

    # Education
    if education:
        lines.append("EDUCATION")
        lines.append(f"{education.degree} in {education.field_of_study}")
        lines.append(f"{education.university} | {education.start_date} - {education.end_date}")
        if education.gpa:
            lines.append(f"GPA: {education.gpa}")
        lines.append("")

    # Skills — tailored to job
    lines.append("TECHNICAL SKILLS")
    lines.append(", ".join(ordered_skills[:15]))
    lines.append("")

    # Experience
    if user.experiences:
        lines.append("EXPERIENCE")
        for exp in user.experiences[:3]:
            lines.append(f"{exp.title} — {exp.company}")
            lines.append(f"{exp.location} | {exp.start_date} - {exp.end_date}")
            # Split description into bullet points
            desc = exp.description or ""
            bullets = [b.strip() for b in re.split(r'[.\n]', desc) if b.strip()]
            for bullet in bullets[:4]:
                lines.append(f"  • {bullet[0].upper() + bullet[1:]}" if bullet else "")
            lines.append("")

    # Projects
    if user.projects:
        lines.append("PROJECTS")
        for proj in user.projects[:3]:
            lines.append(f"{proj.name}")
            lines.append(f"Tech: {proj.technologies}")
            desc = proj.description or ""
            bullets = [b.strip() for b in re.split(r'[.\n]', desc) if b.strip()]
            for bullet in bullets[:3]:
                lines.append(f"  • {bullet[0].upper() + bullet[1:]}" if bullet else "")
            lines.append("")

    # Certifications
    if user.certifications:
        lines.append("CERTIFICATIONS")
        for cert in user.certifications:
            lines.append(f"• {cert.name} — {cert.issuer} ({cert.date_obtained})")
        lines.append("")

    return "\n".join(lines)


def generate_cover_letter(user: User, job: Job, match: Optional[JobMatch] = None) -> str:
    """Generate a catchy, humanized cover letter tailored to the specific job."""
    education = user.education_entries[0] if user.education_entries else None
    degree_info = f"{education.degree} in {education.field_of_study}" if education else "my Computer Science degree"
    university = education.university if education else "my university"

    # Extract what the company actually does from job description
    desc = (job.description or "").lower()
    company_focus = []
    if any(w in desc for w in ["remote", "distributed", "work from anywhere"]):
        company_focus.append("remote-first culture")
    if any(w in desc for w in ["startup", "series", "founded"]):
        company_focus.append("startup energy")
    if any(w in desc for w in ["scale", "millions", "billion", "enterprise"]):
        company_focus.append("large-scale impact")
    if any(w in desc for w in ["innovat", "cutting", "research", "前沿"]):
        company_focus.append("technical innovation")
    if any(w in desc for w in ["open source", "open-source", "community"]):
        company_focus.append("open-source values")
    if any(w in desc for w in ["fast-paced", "agile", "move fast"]):
        company_focus.append("fast-paced environment")
    if not company_focus:
        company_focus.append("mission-driven work")

    # Extract what the role actually involves
    role_signals = []
    if any(w in desc for w in ["build", "develop", "ship", "create"]):
        role_signals.append("building and shipping products")
    if any(w in desc for w in ["data", "analy", "insight", "metric"]):
        role_signals.append("working with data to drive decisions")
    if any(w in desc for w in ["ml", "machine learning", "model", "train", "predict"]):
        role_signals.append("developing ML models")
    if any(w in desc for w in ["api", "backend", "service", "microservice"]):
        role_signals.append("designing and building backend systems")
    if any(w in desc for w in ["frontend", "ui", "ux", "interface"]):
        role_signals.append("crafting user interfaces")
    if any(w in desc for w in ["scale", "performance", "optimi", "reliab"]):
        role_signals.append("optimizing for scale and reliability")
    if not role_signals:
        role_signals.append("solving interesting technical challenges")

    # Match user's experience to the role
    exp_highlights = []
    for exp in user.experiences[:2]:
        exp_desc = (exp.description or "").lower()
        # Find overlap between user's experience and job requirements
        job_skills = _extract_job_skills(job)
        matching = [s for s in job_skills if s in exp_desc]
        if matching:
            exp_highlights.append(f"my work on {exp.title} at {exp.company} where I used {', '.join(matching[:3])}")
        else:
            exp_highlights.append(f"my experience as {exp.title} at {exp.company}")

    project_highlights = []
    for proj in user.projects[:2]:
        proj_tech = (proj.technologies or "").lower()
        job_skills = _extract_job_skills(job)
        matching = [s for s in job_skills if s in proj_tech]
        if matching:
            project_highlights.append(f"{proj.name} (using {', '.join(matching[:2])})")

    # Build the letter
    opening = f"I'm excited about the {job.title} role at {job.company} — "

    # Pick the strongest opening hook
    if exp_highlights:
        opening += f"it's a perfect match for what I've been building. "
    else:
        opening += f"it aligns exactly with where I want to take my career."

    paragraph_1 = f"""{opening}

As a {degree_info} student at {university}, I've spent the last couple of years getting my hands dirty with real engineering work. {'Most recently, ' + exp_highlights[0] + '.' if exp_highlights else 'I bring a strong foundation in software engineering and a hunger to learn.'}"""

    if role_signals:
        paragraph_2 = f"\n\nWhat excites me most is {role_signals[0]}. "
        if project_highlights:
            paragraph_2 += f"I've been doing exactly this through projects like {project_highlights[0]}, "
            paragraph_2 += f"which taught me how to take an idea from concept to a working system."
        else:
            paragraph_2 += f"I'm eager to bring my skills in {', '.join(s.name for s in user.skills[:4])} to tackle these challenges at {job.company}."

    paragraph_3 = f"\n\nI'm drawn to {job.company} because of its {company_focus[0]}. "
    paragraph_3 += f"I believe great engineering happens when talented people work on problems they genuinely care about, "
    paragraph_3 += f"and that's exactly the environment where I do my best work."

    closing = f"\n\nI'd love to chat about how I can contribute to the team. "
    closing += f"I'm available {user.availability or 'immediately'} and happy to jump on a call anytime."

    signature = f"\n\nBest,\n{user.name}\n{user.email}\n{user.phone}"

    parts = ["Dear Hiring Manager,", "", paragraph_1]
    if role_signals:
        parts.append(paragraph_2)
    parts.extend([paragraph_3, closing, signature])

    if user.requires_sponsorship:
        parts.insert(-2, "\n\nNote: I'm an Indian citizen and would require visa sponsorship for this role.")

    return "\n".join(parts)


def generate_application_summary(user: User, job: Job) -> str:
    """Generate a concise one-line application summary."""
    skills = [s.name for s in user.skills[:6]]
    education = user.education_entries[0] if user.education_entries else None
    exp = user.experiences[0] if user.experiences else None

    parts = [f"{user.name}"]
    if education:
        parts.append(f"{education.degree} student at {education.university}")
    if exp:
        parts.append(f"previously {exp.title} at {exp.company}")
    parts.append(f"applying for {job.title} at {job.company}")

    return " — ".join(parts)


def generate_skills_summary(user: User, job: Job) -> str:
    """Generate a skills summary prioritized by job relevance."""
    job_skills = _extract_job_skills(job)
    user_skills = [s.name for s in user.skills]

    relevant = [s for s in user_skills if any(js in s.lower() for js in job_skills)]
    other = [s for s in user_skills if s not in relevant]

    parts = []
    if relevant:
        parts.append("Relevant: " + ", ".join(relevant[:10]))
    if other:
        parts.append("Additional: " + ", ".join(other[:6]))
    return " | ".join(parts) if parts else "Skills: " + ", ".join(user_skills[:10])


def generate_why_company(user: User, job: Job) -> str:
    """Generate a specific 'Why this company?' response."""
    desc = (job.description or "").lower()
    strengths = []
    if any(w in desc for w in ["remote", "distributed", "work from anywhere"]):
        strengths.append("your commitment to remote work and distributed teams")
    if any(w in desc for w in ["innovat", "cutting-edge", "advanced", "research"]):
        strengths.append("your innovative approach to technology and research")
    if any(w in desc for w in ["grow", "learning", "mentor", "development"]):
        strengths.append("your investment in employee growth and mentorship")
    if any(w in desc for w in ["impact", "mission", "meaningful", "purpose"]):
        strengths.append("the meaningful impact your work has on users")
    if any(w in desc for w in ["open source", "open-source", "community"]):
        strengths.append("your contributions to the open-source community")
    if any(w in desc for w in ["startup", "early", "found", "build from scratch"]):
        strengths.append("the opportunity to build something from the ground up")
    if not strengths:
        strengths.append("the technical challenges you're tackling")

    text = " and ".join(strengths[:2])
    return (
        f"I'm excited about {job.company} because of {text}. "
        f"The {job.title} role offers a chance to work alongside talented engineers on problems that genuinely matter."
    )


def generate_why_role(user: User, job: Job) -> str:
    """Generate a specific 'Why this role?' response."""
    skills = [s.name for s in user.skills[:5]]
    desc = (job.description or "").lower()
    signals = []
    if any(w in desc for w in ["build", "develop", "ship", "create"]):
        signals.append("building and shipping real products")
    if any(w in desc for w in ["design", "architect", "plan"]):
        signals.append("designing systems that scale")
    if any(w in desc for w in ["data", "analy", "model", "train"]):
        signals.append("working with data and ML models")
    if any(w in desc for w in ["scale", "performance", "optimi"]):
        signals.append("optimizing for performance at scale")
    if any(w in desc for w in ["learn", "grow", "mentor"]):
        signals.append("learning from experienced engineers")
    activity = " and ".join(signals[:2]) if signals else "solving real engineering challenges"

    return (
        f"The {job.title} position at {job.company} matches my skills in "
        f"{', '.join(skills)}. I'm passionate about {activity}, "
        f"and this role would let me apply what I've learned in real-world projects."
    )


def generate_recruiter_message(user: User, job: Job) -> str:
    """Generate a short LinkedIn recruiter message."""
    edu = user.education_entries[0] if user.education_entries else None
    degree = edu.degree if edu else "CS"
    university = edu.university if edu else "my university"
    skills = [s.name for s in user.skills[:4]]

    return (
        f"Hi! I'm {user.name}, a {degree} student at {university}. "
        f"I came across the {job.title} role at {job.company} and got really excited about it. "
        f"I've been working with {', '.join(skills)} and would love to bring that experience to your team. "
        f"Would you be open to a quick chat?"
    )


def generate_standard_answers(user: User, job: Job) -> dict:
    """Generate answers to standard application questions."""
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

    return [
        {"question": "How did you hear about this position?", "answer": "I found this position through an online job board and was immediately drawn to the role and company mission."},
        {"question": "Are you legally authorized to work?", "answer": f"I am an Indian citizen. {sponsor_text}"},
        {"question": "When can you start?", "answer": f"I am available {user.availability or 'immediately'}."},
        {"question": "What is your expected salary?", "answer": "I am flexible and open to discussion based on the role and market standards."},
        {"question": "Tell us about yourself", "answer": f"I am {user.name or 'a candidate'}, a {edu_degree} student at {edu_university} with hands-on experience in {skills_str}. I've worked on projects ranging from AI-powered tutoring systems to distributed task queues, and I'm passionate about building software that makes a real impact."},
        {"question": "What is your GPA?", "answer": edu_gpa if edu_gpa else "I would prefer not to disclose at this time."},
        {"question": "Do you require visa sponsorship?", "answer": sponsor_detail},
        {"question": "Link to your portfolio", "answer": user.portfolio_url or "https://github.com/bhavyagupta"},
        {"question": "Link to your GitHub", "answer": user.github_url or ""},
        {"question": "Link to your LinkedIn", "answer": user.linkedin_url or ""},
        {"question": "Why are you interested in this role?", "answer": f"I'm excited about this role because it aligns perfectly with my skills in {skills_str} and my passion for building impactful software. The opportunity to work at {job.company} on {job.title} is exactly the kind of challenge I'm looking for."},
        {"question": "What makes you a good fit?", "answer": f"My experience with {skills_str} combined with my project work gives me a strong foundation for this role. I've built production systems handling real users and I'm eager to bring that practical experience to {job.company}."},
    ]


def prepare_application_materials(db: Session, user: User, job: Job, match: Optional[JobMatch] = None) -> dict:
    """Prepare all application materials for a job."""
    return {
        "resume": _generate_ats_resume(user, job),
        "cover_letter": generate_cover_letter(user, job, match),
        "summary": generate_application_summary(user, job),
        "skills_summary": generate_skills_summary(user, job),
        "why_company": generate_why_company(user, job),
        "why_role": generate_why_role(user, job),
        "recruiter_message": generate_recruiter_message(user, job),
        "question_answers": generate_standard_answers(user, job),
    }


def classify_question(question: str) -> str:
    """Classify an application question by type."""
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
