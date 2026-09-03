# Internship Hunter

Autonomous discovery, verification and preparation for **confirmed-remote technical internships**. The default qualification policy rejects listings unless they are explicitly internship/co-op/student roles, explicitly remote, strongly technical, currently valid, non-duplicate and eligible for the candidate.

Only Software, Data Science, AI, Machine Learning and the allowed adjacent technical domains proceed. Marketing, sales, HR, business, on-site/hybrid, senior, full-time, unclear, expired and suspicious listings are rejected before matching or application preparation.

## Run

```bash
pip install -r requirements.txt
python -m backend.run
cd frontend && npm install && npm run dev
```

Use the setup page to confirm a profile, upload a PDF resume, configure search, then run discovery. See [SETUP.md](SETUP.md) and [TESTING.md](TESTING.md).

## Submission safety

The system prepares and verifies applications automatically. It only records `APPLIED` after a permitted browser adapter obtains a real confirmation. CAPTCHA, MFA, login, site restrictions, unclear authorization/sponsorship, unknown questions and unsupported ATS workflows are marked `MANUAL_ACTION_REQUIRED`; none are bypassed.
