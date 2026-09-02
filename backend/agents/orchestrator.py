"""Agent orchestration for Internship Hunter."""
from __future__ import annotations

import datetime
import json
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.models.models import AgentRun, Event


class Orchestrator:
    """Coordinates discovery, matching, and deduplication."""

    def __init__(self, db: Session):
        self.db = db

    async def full_discovery_cycle(self, keywords: List[str] = None, source_names: List[str] = None) -> dict:
        from backend.services.job_service import run_discovery, get_or_create_user
        from backend.services.matching_engine import match_jobs_for_user
        from backend.services.duplicate_detector import detect_and_mark_duplicates

        user = get_or_create_user(self.db)

        # Create a single agent run for the whole cycle
        agent_run = AgentRun(
            agent_name="orchestrator",
            status="running",
            task=f"Full discovery cycle",
            input_summary=f"Keywords: {len(keywords or [])}, Sources: {source_names or 'all'}",
        )
        self.db.add(agent_run)
        self.db.commit()
        self.db.refresh(agent_run)

        results = {}
        try:
            # 1. Discover
            results["discovery"] = await run_discovery(self.db, keywords, source_names)

            # 2. Match
            matches = match_jobs_for_user(self.db, user)
            results["matching"] = {"total_matched": len(matches)}

            # 3. Deduplicate
            dup_count = detect_and_mark_duplicates(self.db)
            results["duplicates"] = {"duplicates_found": dup_count}

            # Log event
            event = Event(
                event_type="orchestrator_cycle",
                title="Full Discovery Cycle Complete",
                message=json.dumps({
                    "discovered": results["discovery"].get("saved", 0),
                    "matched": results["matching"].get("total_matched", 0),
                    "duplicates": results["duplicates"].get("duplicates_found", 0),
                }),
            )
            self.db.add(event)

            agent_run.status = "completed"
            agent_run.outputs = results
            agent_run.completed_at = datetime.datetime.utcnow()
            agent_run.duration_seconds = (
                agent_run.completed_at - agent_run.started_at
            ).total_seconds()
            self.db.commit()

        except Exception as e:
            agent_run.status = "failed"
            agent_run.errors = [{"error": str(e)}]
            agent_run.completed_at = datetime.datetime.utcnow()
            self.db.commit()
            results["error"] = str(e)

        return results
