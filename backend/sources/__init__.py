"""Job source adapters package."""
from backend.sources.base import JobSourceAdapter, RawJob
from backend.sources.remotive import RemotiveSource
from backend.sources.adzuna import AdzunaSource

AVAILABLE_SOURCES = {
    "remotive": RemotiveSource,
    "adzuna": AdzunaSource,
}

def get_source(name: str) -> JobSourceAdapter:
    if name not in AVAILABLE_SOURCES:
        raise ValueError(f"Unknown source: {name}. Available: {list(AVAILABLE_SOURCES.keys())}")
    return AVAILABLE_SOURCES[name]()

def get_all_sources() -> list[JobSourceAdapter]:
    return [cls() for cls in AVAILABLE_SOURCES.values()]
