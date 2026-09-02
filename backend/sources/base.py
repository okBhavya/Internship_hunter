"""Base job source adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


class RawJob(BaseModel):
    """Raw job data from a source before normalization."""
    external_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    remote_type: str = "remote"
    employment_type: str = "internship"
    description: str = ""
    application_url: str = ""
    source_url: str = ""
    date_posted: str = ""
    salary: str = ""
    raw_data: dict = {}


class JobSourceAdapter(ABC):
    """Base class for all job source adapters."""

    name: str = "unknown"
    base_url: str = ""

    @abstractmethod
    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search for jobs matching keywords."""
        ...

    @abstractmethod
    async def fetch_job(self, job_id: str) -> Optional[RawJob]:
        """Fetch a specific job by ID."""
        ...

    def normalize(self, raw: RawJob) -> dict:
        """Normalize a raw job into our standard schema."""
        # Parse salary
        salary_min = None
        salary_max = None
        currency = ""
        if raw.salary:
            import re
            nums = re.findall(r'[\d,]+', raw.salary.replace(",", ""))
            if nums:
                try:
                    salary_min = float(nums[0])
                    if len(nums) > 1:
                        salary_max = float(nums[1])
                except ValueError:
                    pass
            if "$" in raw.salary:
                currency = "USD"
            elif "€" in raw.salary:
                currency = "EUR"
            elif "£" in raw.salary:
                currency = "GBP"
            elif "₹" in raw.salary:
                currency = "INR"

        # Determine internship vs fulltime
        title_lower = raw.title.lower()
        if any(w in title_lower for w in ["intern", "internship"]):
            internship_or_fulltime = "internship"
        elif any(w in title_lower for w in ["full time", "full-time", "permanent"]):
            internship_or_fulltime = "full_time"
        elif any(w in title_lower for w in ["co-op", "coop"]):
            internship_or_fulltime = "co_op"
        else:
            internship_or_fulltime = "full_time"

        # Determine employment type
        if "remote" in (raw.remote_type or "").lower():
            employment_type_display = "remote"
        else:
            employment_type_display = raw.employment_type

        return {
            "external_id": raw.external_id,
            "title": raw.title,
            "company": raw.company,
            "location": raw.location,
            "remote_type": raw.remote_type or "remote",
            "employment_type": employment_type_display,
            "internship_or_fulltime": internship_or_fulltime,
            "country": self._extract_country(raw.location),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
            "description": raw.description,
            "requirements": "",
            "preferred_qualifications": "",
            "skills": [],  # Will be extracted from description
            "experience_required": "",
            "visa_information": "",
            "sponsorship_information": "",
            "application_url": raw.application_url or raw.source_url,
            "source_name": self.name,
            "source_url": raw.source_url,
            "date_posted": raw.date_posted,
            "raw_data": raw.raw_data,
        }

    def _extract_country(self, location: str) -> str:
        """Extract country from location string."""
        if not location:
            return ""
        loc = location.lower()
        countries = {
            "usa": "United States", "united states": "United States", "us ": "United States",
            "uk": "United Kingdom", "united kingdom": "United Kingdom",
            "germany": "Germany", "france": "France", "netherlands": "Netherlands",
            "india": "India", "canada": "Canada", "australia": "Australia",
            "singapore": "Singapore", "japan": "Japan", "remote": "Worldwide",
            "worldwide": "Worldwide", "global": "Worldwide",
        }
        for key, val in countries.items():
            if key in loc:
                return val
        return location.split(",")[-1].strip() if "," in location else location.strip()
