"""
This file is maintained for backward compatibility.
All task implementations have been moved to the tasks/ directory.
"""

from .tasks.github import (
    pull_latest_collection_metadata_from_github,
    push_to_github_task,
    sync_with_production_webapp,
)
from .tasks.text import fetch_and_replace_full_text, resolve_title_pattern
from .tasks.urls import import_candidate_urls_from_api

__all__ = [
    "push_to_github_task",
    "sync_with_production_webapp",
    "pull_latest_collection_metadata_from_github",
    "resolve_title_pattern",
    "fetch_and_replace_full_text",
    "import_candidate_urls_from_api",
]
