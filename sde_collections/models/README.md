# COSMOS Curation System

A system for managing collections of URLs through pattern-based rules and status workflows.

## Documentation


- [URL Pattern Overview](./README_PATTERN_OVERVIEW.md) - Core pattern system for URL filtering and modification
    - [Pattern System Details](./README_PATTERN_SYSTEM.md)
    - [URL Lifecycle Management](./README_LIFECYCLE.md)
    - [Pattern Resolution](./README_PATTERN_RESOLUTION.md)
    - [URL Inclusion/Exclusion](./README_INCLUSION.md)
    - [Pattern Unapplication Logic](./README_UNAPPLY_LOGIC.md)
- [Collection Status Workflows](./README_STATUS_TRIGGERS.md) - Collection progression and automated triggers
- [Reindexing Status System](./README_REINDEXING_STATUSES.md) - Status management for reindexing collections

## Scraping and Indexing Models

- [`ScraperConfigOverride`](./scraper_config.py) - Per-collection overrides (`max_pages`, `depth_limit`, `delay`, `concurrent_requests`, `obey_robots`, `include_subdomains`) merged onto the crawler's own defaults. All fields are nullable; only non-null values reach the job JSON.
- [`ScrapeDispatch`](./scraper_config.py) - One row per SSM scrape dispatch, recording `ssm_command_id` and `dispatched_at`. `dispatched_at` is the poller's freshness reference (older S3 results belong to a previous run) and the stall-timeout start time.
- [`IndexDispatch`](./indexing.py) - One row per indexing run, recording `collection`, `run_id`, `target` (test or prod), `task_arn`, `previous_workflow_status`, and `dispatched_at`, plus `completed_at` once the poller resolves the run.
