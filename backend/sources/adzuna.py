"""Adzuna API job source adapter — uses the public Adzuna API."""
from __future__ import annotations

import asyncio
from typing import List, Optional

import httpx

from backend.sources.base import JobSourceAdapter, RawJob
from backend.config import get_settings


class AdzunaSource(JobSourceAdapter):
    """Adapter for Adzuna job search API (adzuna.com)."""

    name = "adzuna"
    base_url = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.adzuna_app_id
        self.app_key = settings.adzuna_app_key

    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search Adzuna for jobs matching keywords."""
        jobs = []

        if not self.app_id or not self.app_key:
            # Return empty — no API key configured
            print("Adzuna: No API key configured, skipping.")
            return []

        countries = ["us", "gb", "de"]  # Adzuna country codes

        async with httpx.AsyncClient(timeout=30.0) as client:
            for country in countries:
                for kw in keywords[:3]:  # Limit keyword searches per country
                    try:
                        url = f"{self.base_url}/{country}/search/1"
                        params = {
                            "app_id": self.app_id,
                            "app_key": self.app_key,
                            "what": kw,
                            "results_per_page": min(limit // len(countries), 50),
                            "content-type": "application/json",
                        }
                        resp = await client.get(url, params=params)
                        if resp.status_code == 200:
                            data = resp.json()
                            for j in data.get("results", []):
                                location_data = j.get("location", {})
                                display_name = location_data.get("display_name", "") if isinstance(location_data, dict) else ""

                                raw = RawJob(
                                    external_id=str(j.get("id", "")),
                                    title=j.get("title", ""),
                                    company=j.get("company", {}).get("display_name", "") if isinstance(j.get("company"), dict) else "",
                                    location=display_name,
                                    remote_type=self._detect_remote(j),
                                    description=j.get("description", "")[:5000],
                                    application_url=j.get("redirect_url", ""),
                                    source_url=j.get("redirect_url", ""),
                                    date_posted=j.get("created", ""),
                                    salary=str(j.get("salary_min", "")),
                                    raw_data=j,
                                )
                                jobs.append(raw)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Adzuna search error for {country}/{kw}: {e}")
                        continue

        seen = set()
        unique = []
        for j in jobs:
            key = f"{j.title.lower()}:{j.company.lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(j)

        return unique[:limit]

    async def fetch_job(self, job_id: str) -> Optional[RawJob]:
        """Fetch a specific job from Adzuna."""
        if not self.app_id or not self.app_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            for country in ["us", "gb"]:
                try:
                    url = f"{self.base_url}/{country}/jobs/{job_id}"
                    params = {"app_id": self.app_id, "app_key": self.app_key}
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        j = resp.json()
                        return RawJob(
                            external_id=str(j.get("id", "")),
                            title=j.get("title", ""),
                            company=j.get("company", {}).get("display_name", ""),
                            location=j.get("location", {}).get("display_name", ""),
                            description=j.get("description", ""),
                            application_url=j.get("redirect_url", ""),
                            source_url=j.get("redirect_url", ""),
                            date_posted=j.get("created", ""),
                            raw_data=j,
                        )
                except Exception:
                    continue
        return None

    def _detect_remote(self, job_data: dict) -> str:
        """Detect if job is remote from Adzuna data."""
        title = (job_data.get("title") or "").lower()
        desc = (job_data.get("description") or "").lower()
        loc = str(job_data.get("location", {}).get("display_name", "")).lower()

        if any(w in title or w in desc for w in ["remote", "work from home", "wfh", "distributed"]):
            return "remote"
        if "remote" in loc:
            return "remote"
        return "onsite"
