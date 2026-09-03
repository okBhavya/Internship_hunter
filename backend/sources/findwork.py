"""Findwork.dev API job source adapter — free API, no key required, tech jobs."""
from __future__ import annotations

import asyncio
from typing import List, Optional

import httpx

from backend.sources.base import JobSourceAdapter, RawJob


class FindworkSource(JobSourceAdapter):
    """Adapter for Findwork (findwork.dev) — public API, tech-focused jobs."""

    name = "findwork"
    API_URL = "https://findwork.dev/api/jobs/"

    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search Findwork for tech jobs matching keywords."""
        jobs = []

        # Build search queries from keywords
        search_queries = set()
        for kw in keywords:
            kw_lower = kw.lower()
            # Simplify to core terms
            if "software" in kw_lower or "engineer" in kw_lower:
                search_queries.add("software engineer")
            if "data" in kw_lower:
                search_queries.add("data science")
            if "machine learning" in kw_lower or "ml" in kw_lower:
                search_queries.add("machine learning")
            if "ai" in kw_lower:
                search_queries.add("artificial intelligence")
            if "backend" in kw_lower:
                search_queries.add("backend")
            if "frontend" in kw_lower:
                search_queries.add("frontend")
            if "intern" in kw_lower:
                search_queries.add("intern")
            if "python" in kw_lower:
                search_queries.add("python")

        if not search_queries:
            search_queries = {"software engineer", "data science", "machine learning", "intern"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                try:
                    params = {
                        "search": query,
                        "order_by": "relevance",
                        "remote": "true",
                    }
                    resp = await client.get(self.API_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        job_list = data.get("results", []) or []
                        for j in job_list:
                            title = (j.get("role") or "").lower()
                            desc = (j.get("text") or "").lower()

                            # Accept jobs in our target fields
                            target_words = [
                                "software", "engineer", "developer", "data", "machine learning",
                                "ml", "ai", "backend", "frontend", "full stack", "fullstack",
                                "python", "intern", "junior", "entry",
                            ]
                            if not any(w in title for w in target_words):
                                if not any(w in desc[:500] for w in target_words[:6]):
                                    continue

                            # Get salary info
                            salary = ""
                            if j.get("salary_min"):
                                salary = f"{j['salary_min']}"
                                if j.get("salary_max"):
                                    salary += f"-{j['salary_max']}"

                            raw = RawJob(
                                external_id=str(j.get("id", "")),
                                title=j.get("role", ""),
                                company=j.get("company_name", ""),
                                location=j.get("location", "Remote"),
                                remote_type="remote" if j.get("remote") else "onsite",
                                employment_type="internship" if "intern" in title else "full_time",
                                description=j.get("text", "")[:5000],
                                application_url=j.get("url", "") or j.get("apply_url", ""),
                                source_url=j.get("url", "") or j.get("url_preview", ""),
                                date_posted=j.get("date_posted", ""),
                                salary=salary,
                                raw_data=j,
                            )
                            jobs.append(raw)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Findwork search error for {query}: {e}")
                    continue

        # Deduplicate
        seen = set()
        unique = []
        for j in jobs:
            key = f"{j.title.lower()}:{j.company.lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(j)

        return unique[:limit]

    async def fetch_job(self, job_id: str) -> Optional[RawJob]:
        """Fetch a specific job from Findwork."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{self.API_URL}{job_id}/")
                if resp.status_code == 200:
                    j = resp.json()
                    return RawJob(
                        external_id=str(j.get("id", "")),
                        title=j.get("role", ""),
                        company=j.get("company_name", ""),
                        location=j.get("location", "Remote"),
                        remote_type="remote" if j.get("remote") else "onsite",
                        description=j.get("text", ""),
                        application_url=j.get("url", "") or j.get("apply_url", ""),
                        source_url=j.get("url", ""),
                        date_posted=j.get("date_posted", ""),
                        raw_data=j,
                    )
            except Exception as e:
                print(f"Findwork fetch error: {e}")
        return None
