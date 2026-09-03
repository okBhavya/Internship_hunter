"""Job source adapters package."""
from backend.sources.base import JobSourceAdapter, RawJob
from backend.sources.remotive import RemotiveSource
from backend.sources.jobicy import JobicySource
# from backend.sources.findwork import FindworkSource  # Requires API key
from backend.sources.google_jobs import GoogleJobsSource

# Registry of all available sources
AVAILABLE_SOURCES = {
    "jobicy": JobicySource,
    # "findwork": FindworkSource,  # Requires API key
    "google_jobs": GoogleJobsSource,
    "remotive": RemotiveSource,
}


def get_source(name: str) -> JobSourceAdapter:
    """Get a source adapter by name."""
    if name not in AVAILABLE_SOURCES:
        raise ValueError(f"Unknown source: {name}. Available: {list(AVAILABLE_SOURCES.keys())}")
    return AVAILABLE_SOURCES[name]()


def get_all_sources() -> list[JobSourceAdapter]:
    """Get all registered source adapters."""
    return [cls() for cls in AVAILABLE_SOURCES.values()]
