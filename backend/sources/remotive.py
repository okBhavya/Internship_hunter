"""Remotive API job source adapter — uses the public Remotive API."""
from __future__ import annotations

import asyncio
from typing import List, Optional

import httpx

from backend.sources.base import JobSourceAdapter, RawJob


class RemotiveSource(JobSourceAdapter):
    """Adapter for Remotive (remotive.com) — public API, no key required."""

    name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"
    API_URL = "https://remotive.com/api/remote-jobs"

    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search Remotive for remote jobs matching keywords."""
        jobs = []
        category_map = {
            "software": "software-dev",
            "data": "data",
            "ai": "software-dev",
            "machine learning": "software-dev",
            "backend": "software-dev",
            "frontend": "software-dev",
            "full stack": "software-dev",
            "devops": "software-dev",
            "qa": "qa",
        }

        categories_to_search = set()
        for kw in keywords:
            kw_lower = kw.lower()
            for key, cat in category_map.items():
                if key in kw_lower:
                    categories_to_search.add(cat)

        if not categories_to_search:
            categories_to_search = {"software-dev", "data", "qa"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for category in categories_to_search:
                try:
                    params = {"category": category, "limit": min(limit, 100)}
                    resp = await client.get(self.API_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        job_list = data.get("jobs", [])

                        for j in job_list:
                            # Filter by keywords
                            title = (j.get("title") or "").lower()
                            desc = (j.get("description") or "").lower()
                            company = (j.get("company_name") or "").lower()

                            # Accept all jobs from the category (category already filters)
                            if True:
                                raw = RawJob(
                                    external_id=str(j.get("id", "")),
                                    title=j.get("title", ""),
                                    company=j.get("company_name", ""),
                                    location=j.get("candidate_required_location", "Remote"),
                                    remote_type="remote",
                                    employment_type="internship" if "intern" in title else "full_time",
                                    description=j.get("description", "")[:5000],
                                    application_url=j.get("url", ""),
                                    source_url=j.get("url", ""),
                                    date_posted=j.get("publication_date", ""),
                                    salary=j.get("salary", ""),
                                    raw_data=j,
                                )
                                jobs.append(raw)

                        await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"Remotive search error for {category}: {e}")
                    continue

        # Deduplicate within source
        seen = set()
        unique = []
        for j in jobs:
            key = f"{j.title.lower()}:{j.company.lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(j)

        return unique[:limit]

    async def fetch_job(self, job_id: str) -> Optional[RawJob]:
        """Fetch a specific job from Remotive."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Remotive doesn't have single-job endpoint, search instead
                resp = await client.get(self.API_URL, params={"id": job_id})
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    if jobs:
                        j = jobs[0]
                        return RawJob(
                            external_id=str(j.get("id", "")),
                            title=j.get("title", ""),
                            company=j.get("company_name", ""),
                            location=j.get("candidate_required_location", "Remote"),
                            remote_type="remote",
                            description=j.get("description", ""),
                            application_url=j.get("url", ""),
                            source_url=j.get("url", ""),
                            date_posted=j.get("publication_date", ""),
                            salary=j.get("salary", ""),
                            raw_data=j,
                        )
            except Exception as e:
                print(f"Remotive fetch error: {e}")
        return None
