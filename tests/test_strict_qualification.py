from backend.services.strict_qualification import qualify_job


def job(title, description="Remote worldwide internship"):
    return {"title": title, "company": "Example Tech", "application_url": "https://example.com/apply", "description": description}


def test_required_accepts():
    for title in ["Software Engineering Intern", "Data Science Intern", "Machine Learning Intern", "AI Engineering Intern", "Data Engineering Intern", "Remote Software Internship", "Data Analyst Intern"]:
        assert qualify_job(job(title))["qualified"]


def test_required_rejections():
    for title, description in [
        ("AI Marketing Intern", "Remote internship"), ("HR Intern", "Remote Python internship"),
        ("AI-powered Sales Intern", "Remote internship"), ("Software Engineering Intern", "Hybrid internship"),
        ("ML Intern", "On-site internship"), ("Software Engineer", "Remote full-time role"),
        ("Senior Software Engineer", "Remote internship"), ("Machine Learning Intern", "Flexible location internship"),
    ]:
        assert not qualify_job(job(title, description))["qualified"]
