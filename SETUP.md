# Setup Guide — Internship Hunter

## Prerequisites

- **Python 3.10+** (tested on 3.14)
- **Node.js 18+** (tested on 24)
- **npm** (comes with Node.js)

## Installation

### Step 1: Clone & Enter Project
```bash
cd D:\Auto_apply
```

### Step 2: Install Python Dependencies
```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings httpx python-multipart pymupdf apscheduler
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 4: Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys (optional)
```

### Step 5: Start Backend
```bash
python -m backend.run
```
Server starts at http://localhost:8000

### Step 6: Start Frontend (Development)
```bash
cd frontend
npm run dev
```
Frontend starts at http://localhost:5173

### Step 7: First-Time Setup
1. Open http://localhost:5173/setup
2. Click through each setup step:
   - **Seed Profile** — Loads Bhavya Gupta's resume data
   - **Configure Search** — Sets default keywords (Software Engineer, Data Science, ML, AI, Backend)
   - **Run Discovery** — Fetches jobs from Remotive API
   - **View Results** — Shows ranked matches

## Running Without API Keys

The system works out of the box using:
- **Remotive API** — Free, no key required
- **Indeed RSS** — Free, no key required

Optional API keys for more sources:
- `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` — Get free key at https://www.adzuna.com/developers
- `GEMINI_API_KEY` — For enhanced AI matching

## Docker (Future)
```bash
docker compose up --build
```

## Troubleshooting

**Port 8000 already in use:**
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

**Database locked:**
```bash
rm internship_hunter.db
# Restart the server
```

**Frontend build fails:**
```bash
cd frontend
rm -rf node_modules dist
npm install
npx vite build
```
