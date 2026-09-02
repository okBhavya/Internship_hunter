# Testing — Internship Hunter

## Running Tests

### Backend API Tests
```bash
# Start the server first
python -m backend.run &

# Test profile endpoint
curl http://localhost:8000/api/profile

# Test discovery
curl -X POST http://localhost:8000/api/discovery/run

# Test top matches
curl http://localhost:8000/api/jobs/top-matches?limit=10

# Test dashboard
curl http://localhost:8000/api/dashboard/stats
```

### Full E2E Flow Test
```bash
python -c "
import urllib.request, json

def api(method, path, data=None):
    url = f'http://localhost:8000/api{path}'
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode()
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

# 1. Seed profile
print('1. Seed profile:', api('POST', '/seed-profile'))

# 2. Seed preferences
print('2. Seed preferences:', api('POST', '/seed-default-preferences'))

# 3. Run discovery
result = api('POST', '/discovery/run')
print(f'3. Discovery: {result[\"saved\"]} jobs saved')

# 4. Check top matches
matches = api('GET', '/jobs/top-matches?limit=5')
print(f'4. Top matches: {len(matches)} jobs')

# 5. Prepare application for best match
if matches:
    job_id = matches[0]['job']['id']
    app = api('POST', f'/applications?job_id={job_id}&mode=prepare')
    print(f'5. Application created: {app[\"status\"]}')

    # 6. Check materials
    materials = api('GET', f'/applications/{app[\"id\"]}')
    print(f'6. Materials: cover_letter={len(materials.get(\"cover_letter\", \"\"))} chars')

    # 7. Approve
    api('POST', f'/applications/{app[\"id\"]}/approve')
    print('7. Application approved')

# 8. Dashboard stats
stats = api('GET', '/dashboard/stats')
print(f'8. Dashboard: {stats[\"jobs_discovered\"]} discovered, {stats[\"jobs_matching\"]} matching')
print('\\n✅ Full E2E flow passed!')
"
```

## Key Test Scenarios

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Seed profile | 14 skills, 3 projects, 2 experiences |
| 2 | Run discovery | 10+ jobs from Remotive |
| 3 | Job matching | Scores 0-100 for each job |
| 4 | Prepare application | Cover letter, summary, Q&A generated |
| 5 | Approve application | Status → "applied", date set |
| 6 | Dashboard stats | Non-zero counts |
| 7 | Duplicate detection | No duplicate jobs in results |
| 8 | Frontend build | Builds without errors |

## Known Limitations

- Remotive returns mostly full-time remote positions (limited internships)
- Adzuna requires API key (free) for additional sources
- Indeed RSS may rate-limit on heavy usage
- Browser automation not yet integrated into discovery flow
- AI-powered matching uses rule-based engine (Gemini integration available)
