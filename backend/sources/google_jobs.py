"""Google Jobs scraper — discovers internships from Google search without API keys."""
from __future__ import annotations

import asyncio
import re
import json
from typing import List, Optional
from urllib.parse import quote_plus

import httpx

from backend.sources.base import JobSourceAdapter, RawJob


class GoogleJobsSource(JobSourceAdapter):
    """Scrapes Google search for job listings. Uses public search, no API key."""

    name = "google_jobs"
    SEARCH_URL = "https://www.google.com/search"

    async def search(self, keywords: List[str], location: str = "", limit: int = 50) -> List[RawJob]:
        """Search Google for job listings matching keywords."""
        jobs = []

        # Build targeted internship search queries
        queries = set()
        for kw in keywords:
            kw_lower = kw.lower()
            # Always include "intern" or "internship" in queries
            if "intern" not in kw_lower:
                # Add internship suffix
                base = kw.replace("Intern", "").replace("intern", "").strip()
                if base:
                    queries.add(f"{base} internship remote")
                    queries.add(f"{base} intern remote 2026")
            else:
                queries.add(f"{kw} remote")
                queries.add(f"{kw} 2026")

        if not queries:
            queries = {
                "software engineer intern remote 2026",
                "data science intern remote 2026",
                "machine learning intern remote 2026",
                "AI intern remote 2026",
                "backend engineer intern remote",
            }

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            for query in list(queries)[:6]:  # Limit queries to avoid rate limiting
                try:
                    params = {
                        "q": query,
                        "ibp": "htl;jobs",  # Google Jobs tab
                        "htichips": "date_posted:week",  # Recent only
                    }
                    resp = await client.get(self.SEARCH_URL, params=params, follow_redirects=True)
                    if resp.status_code == 200:
                        html = resp.text
                        # Parse Google Jobs results from HTML
                        parsed = self._parse_google_jobs(html, query)
                        jobs.extend(parsed)
                    await asyncio.sleep(1.5)  # Respectful rate limiting
                except Exception as e:
                    print(f"Google Jobs search error for '{query}': {e}")
                    continue

            # Also try direct job board searches
            board_queries = [
                ("greenhouse", "site:greenhouse.io intern software"),
                ("lever", "site:lever.co intern data science"),
                ("workday", "site:myworkdayjobs.com intern machine learning"),
                ("ashby", "site:ashbyhq.com intern AI"),
            ]
            for board_name, query in board_queries:
                try:
                    params = {"q": f"{query} remote 2026", "num": 20}
                    resp = await client.get(self.SEARCH_URL, params=params, follow_redirects=True)
                    if resp.status_code == 200:
                        parsed = self._parse_search_results(resp.text, board_name)
                        jobs.extend(parsed)
                    await asyncio.sleep(1.0)
                except Exception as e:
                    print(f"Google search error for {board_name}: {e}")
                    continue

        # Deduplicate
        seen = set()
        unique = []
        for j in jobs:
            key = f"{j.title.lower().strip()}:{j.company.lower().strip()}"
            if key not in seen and j.title.strip():
                seen.add(key)
                unique.append(j)

        return unique[:limit]

    def _parse_google_jobs(self, html: str, query: str) -> List[RawJob]:
        """Parse Google Jobs structured data from HTML."""
        jobs = []

        # Try to find JSON-LD structured data
        ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
        ld_matches = re.findall(ld_pattern, html, re.DOTALL)
        for match in ld_matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            job = self._parse_job_posting(item)
                            if job:
                                jobs.append(job)
                elif isinstance(data, dict) and data.get("@type") == "JobPosting":
                    job = self._parse_job_posting(data)
                    if job:
                        jobs.append(job)
            except (json.JSONDecodeError, KeyError):
                continue

        # Try to find job data in script tags (Google's custom format)
        script_pattern = r'AF_initDataCallback\((.*?)\);'
        script_matches = re.findall(script_pattern, html, re.DOTALL)
        for match in script_matches:
            try:
                # Google embeds job data in these callbacks
                if "JobPosting" in match or "jobTitle" in match:
                    # Extract job-like data
                    title_matches = re.findall(r'"([^"]*(?:intern|engineer|developer|data|ml|ai)[^"]*)"', match, re.I)
                    url_matches = re.findall(r'"(https?://[^"]*(?:greenhouse|lever|workday|ashby|careers)[^"]*)"', match)
                    for i, title in enumerate(title_matches[:5]):
                        if i < len(url_matches):
                            jobs.append(RawJob(
                                external_id=f"google_{hash(title)}",
                                title=title,
                                company=self._guess_company(url_matches[i]),
                                location="Remote",
                                remote_type="remote",
                                employment_type="internship" if "intern" in title.lower() else "full_time",
                                description=f"Found via Google search for: {query}",
                                application_url=url_matches[i],
                                source_url=url_matches[i],
                            ))
            except Exception:
                continue

        return jobs

    def _parse_job_posting(self, data: dict) -> Optional[RawJob]:
        """Parse a JobPosting JSON-LD object."""
        title = data.get("name", "")
        if not title:
            return None

        company = ""
        org = data.get("hiringOrganization", {})
        if isinstance(org, dict):
            company = org.get("name", "")
        elif isinstance(org, str):
            company = org

        location = ""
        loc = data.get("jobLocation", {})
        if isinstance(loc, dict):
            addr = loc.get("address", {})
            if isinstance(addr, dict):
                parts = [addr.get("addressLocality", ""), addr.get("addressCountry", "")]
                location = ", ".join(p for p in parts if p)
        elif isinstance(loc, list) and loc:
            first = loc[0]
            if isinstance(first, dict):
                addr = first.get("address", {})
                if isinstance(addr, dict):
                    parts = [addr.get("addressLocality", ""), addr.get("addressCountry", "")]
                    location = ", ".join(p for p in parts if p)

        url = data.get("url", "")
        desc = data.get("description", "")
        # Strip HTML tags from description
        desc = re.sub(r"<[^>]+>", " ", desc).strip()[:5000]

        date_posted = data.get("datePosted", "")

        return RawJob(
            external_id=f"google_{hash(f'{title}:{company}')}",
            title=title,
            company=company,
            location=location or "Remote",
            remote_type="remote",
            employment_type="internship" if "intern" in title.lower() else "full_time",
            description=desc,
            application_url=url,
            source_url=url,
            date_posted=date_posted,
        )

    def _parse_search_results(self, html: str, board_name: str) -> List[RawJob]:
        """Parse regular Google search results for job board links."""
        jobs = []
        # Find links to job boards
        link_pattern = r'href="(https?://[^"]*(?:greenhouse\.io|lever\.co|myworkdayjobs\.com|ashbyhq\.com|careers)[^"]*)"'
        links = re.findall(link_pattern, html)

        # Find titles near these links
        for link in links[:10]:
            # Extract job title from URL path
            path = link.rstrip("/").split("/")[-1]
            title = path.replace("-", " ").replace("_", " ").title()
            if len(title) < 3 or title.lower() in ["jobs", "careers", " openings"]:
                continue

            company = self._guess_company(link)

            jobs.append(RawJob(
                external_id=f"google_{hash(f'{title}:{link}')}",
                title=title,
                company=company,
                location="Remote",
                remote_type="remote",
                employment_type="internship" if "intern" in title.lower() else "full_time",
                description=f"Discovered via Google search on {board_name}",
                application_url=link,
                source_url=link,
            ))

        return jobs

    def _guess_company(self, url: str) -> str:
        """Guess company name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or ""
            # Remove www. and common TLDs
            for prefix in ["www.", "careers.", "jobs."]:
                host = host.replace(prefix, "")
            for suffix in [".io", ".co", ".com", ".org", ".net"]:
                host = host.replace(suffix, "")
            return host.replace("-", " ").title() if host else ""
        except Exception:
            return ""

    async def fetch_job(self, job_id: str) -> Optional[RawJob]:
        """Not implemented for Google Jobs source."""
        return None
