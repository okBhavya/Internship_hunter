"""Entry point for the Internship Hunter backend."""
import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level="info",
    )
