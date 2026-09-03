"""Jobicy API job source adapter — free API, no key required, remote jobs."""
from __future__ import annotations

import asyncio
from typing import List, Optional

import httpx

from backend.sources.base import JobSourceAdapter, RawJob


class JobicySource(JobSourceAdapter):
    """Adapter for Jobicy (jobicy.com) — public API, remote jobs."""

    name = "jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search Jobicy for remote jobs matching keywords."""
        jobs = []
        tag_map = {
            "software": ["software", "developer", "engineer"],
            "data": ["data", "analytics", "database"],
            "ai": ["ai", "machine learning", "ml", "artificial intelligence"],
            "backend": ["backend", "backend engineer", "server"],
            "frontend": ["frontend", "frontend engineer", "react", "vue"],
            "full stack": ["full stack", "fullstack"],
            "python": ["python"],
            "intern": ["intern", "internship", "junior", "entry level", "trainee"],
        }

        # Map our keywords to Jobicy tags
        tags_to_search = set()
        for kw in keywords:
            kw_lower = kw.lower()
            for tag_key, tag_values in tag_map.items():
                if any(tv in kw_lower for tv in tag_values):
                    tags_to_search.add(tag_key)

        if not tags_to_search:
            tags_to_search = {"software", "data", "ai"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for tag in tags_to_search:
                try:
                    params = {"tag": tag, "count": min(limit, 50)}
                    resp = await client.get(self.API_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        job_list = data.get("jobs", [])
                        for j in job_list:
                            title = (j.get("jobTitle") or "").lower()
                            desc = (j.get("jobDescription") or "").lower()

                            # Accept jobs that match our target fields
                            target_words = [
                                "software", "engineer", "developer", "data", "machine learning",
                                "ml", "ai", "backend", "frontend", "full stack", "fullstack",
                                "python", "java", "devops", "cloud", "intern", "junior",
                                "entry", "associate", "qa", "test",
                            ]
                            if not any(w in title for w in target_words):
                                # Also check description for key terms
                                if not any(w in desc[:500] for w in target_words[:8]):
                                    continue

                            raw = RawJob(
                                external_id=str(j.get("id", "")),
                                title=j.get("jobTitle", ""),
                                company=j.get("companyName", ""),
                                location=j.get("jobGeo", "Remote"),
                                remote_type="remote",
                                employment_type=self._map_job_type(j.get("jobType", [""])),
                                description=j.get("jobDescription", "")[:5000],
                                application_url=j.get("url", ""),
                                source_url=j.get("url", ""),
                                date_posted=j.get("pubDate", ""),
                                salary=j.get("annualSalaryMin", "") if j.get("annualSalaryMin") else "",
                                raw_data=j,
                            )
                            jobs.append(raw)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Jobicy search error for {tag}: {e}")
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
        """Fetch a specific job from Jobicy."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{self.API_URL}/{job_id}")
                if resp.status_code == 200:
                    j = resp.json()
                    return RawJob(
                        external_id=str(j.get("id", "")),
                        title=j.get("jobTitle", ""),
                        company=j.get("companyName", ""),
                        location=j.get("jobGeo", "Remote"),
                        remote_type="remote",
                        description=j.get("jobDescription", ""),
                        application_url=j.get("url", ""),
                        source_url=j.get("url", ""),
                        date_posted=j.get("pubDate", ""),
                        raw_data=j,
                    )
            except Exception as e:
                print(f"Jobicy fetch error: {e}")
        return None

    def _map_job_type(self, job_type) -> str:
        if isinstance(job_type, list):
            job_type = job_type[0] if job_type else ""
        jt = str(job_type).lower()
        if "intern" in jt:
            return "internship"
        if "full" in jt:
            return "full_time"
        if "part" in jt:
            return "part_time"
        if "contract" in jt:
            return "contract"
        if "freelance" in jt:
            return "freelance"
        return job_type
