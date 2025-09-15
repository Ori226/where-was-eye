"""
Where Was Eye - A tool for querying Google Timeline location history data.

This package provides functionality to parse Google Timeline location history,
query locations at specific times, and integrate with AI agents.
"""

from .timeline_db import MyTimelineDB
from .agent import WhereWasEyeAgent, create_agent
from .server import create_app

__version__ = "0.1.0"
__all__ = ["MyTimelineDB", "WhereWasEyeAgent", "create_agent", "create_app"]