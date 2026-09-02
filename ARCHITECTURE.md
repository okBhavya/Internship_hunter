# Architecture — Internship Hunter

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  Overview │ Jobs │ Matches │ Applications │ Profile │ Setup  │
└─────────────┬───────────────────────────────────────────────┘
              │ HTTP API
┌─────────────▼───────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Profile  │  │     Jobs     │  │    Applications      │   │
│  │ Service   │  │   Service    │  │     Service          │   │
│  └──────────┘  └──────────────┘  └─────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Multi-Agent Orchestrator                │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐   │   │
│  │  │Disco-  │ │Match-  │ │Resume  │ │Cover Letter│   │   │
│  │  │very    │ │ing     │ │Tailor  │ │Agent       │   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────────┘   │   │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐                 │   │
│  │  │Dup     │ │App Q&A │ │Veri-     │                 │   │
│  │  │Detect  │ │Agent   │ │fication  │                 │   │
│  │  └────────┘ └────────┘ └──────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Source Adapters (modular)                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ Remotive │  │  Adzuna  │  │ Indeed   │           │   │
│  │  │   API    │  │   API    │  │  RSS     │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │   SQLite Database     │  │   Browser Automation     │    │
│  │   (SQLAlchemy ORM)    │  │   (Playwright + stops)   │    │
│  └──────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. User triggers discovery (or scheduled)
   ↓
2. Job Discovery Agent → searches source adapters
   ↓
3. Sources return RawJob objects → normalized to Job schema
   ↓
4. Duplicate Detection Agent → marks duplicates
   ↓
5. Job Matching Agent → scores each job against user profile
   ↓
6. Dashboard shows ranked matches
   ↓
7. User selects jobs → Prepare Application mode
   ↓
8. Resume Tailoring Agent → generates tailored resume
9. Cover Letter Agent → generates cover letter
10. Application Q&A Agent → answers application questions
   ↓
11. Verification Agent → checks for factual inconsistencies
   ↓
12. Application placed in Approval Queue
   ↓
13. User reviews → approves → opens application page
   ↓
14. Application Tracker updates status
```

## Agent Architecture

### Orchestrator
Coordinates all agents, runs full discovery cycles, and manages workflow state.

### Specialized Agents
| Agent | Responsibility |
|-------|---------------|
| Job Discovery | Search source APIs, normalize results |
| Job Matching | Score jobs against profile (0-100) |
| Resume Tailoring | Generate ATS-friendly tailored resume |
| Cover Letter | Generate personalized cover letters |
| Application Q&A | Classify and answer application questions |
| Duplicate Detection | Find and mark duplicate listings across sources |
| Verification | Check materials for factual inconsistencies |

### Matching Score Weights
| Factor | Weight | Max Points |
|--------|--------|-----------|
| Technical Skill Match | 30% | 30 |
| Role Match | 20% | 20 |
| Experience Match | 15% | 15 |
| Education Match | 10% | 10 |
| Location/Remote Match | 10% | 10 |
| Work Authorization | 5% | 5 |
| Project Match | 5% | 5 |
| Application Feasibility | 5% | 5 |

## Database Schema (13 tables)

- `users` — User profile
- `education` — Education history
- `skills` — Technical skills
- `projects` — Personal/academic projects
- `experiences` — Work experience
- `certifications` — Certifications
- `resumes` — Uploaded resumes
- `jobs` — Discovered job listings
- `job_sources` — Source adapter metadata
- `job_matches` — AI match scores
- `applications` — Application tracking
- `application_materials` — Generated materials
- `question_answers` — Application Q&A
- `agent_runs` — Agent activity log
- `events` — System events
- `notifications` — User notifications
- `search_preferences` — Search configuration

## Security

- Environment variables for all secrets
- No passwords stored in plaintext
- Browser agent never bypasses CAPTCHA, login walls, or anti-bot systems
- Audit logs for all agent actions
- No fabricated information in application materials
