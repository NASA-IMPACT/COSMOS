"""Build the job JSON the crawl4ai crawler consumes.

Contract (sde-crawl4ai-scraper-v1/sde_crawler/job.py): merge_job() skips None values,
so only non-null overrides are emitted; `collection_id` names both the output file and
the S3 keys. COSMOS always sends config_folder — unique, editable=False, stable across
renames. Never the numeric PK.
"""

# Mirrors sde_crawler.crawler.MAX_PAGES_CAP — jobs above this land in jobs/failed/.
MAX_PAGES_CAP = 100_000

OVERRIDE_FIELDS = (
    "max_pages",
    "depth_limit",
    "delay",
    "concurrent_requests",
    "obey_robots",
    "include_subdomains",
)


def build_job_json(collection) -> dict:
    job = {"seed": collection.url, "collection_id": collection.config_folder}

    override = collection.scraper_config if hasattr(collection, "scraper_config") else None
    if override is not None:
        for field in OVERRIDE_FIELDS:
            value = getattr(override, field)
            if value is not None:
                job[field] = value

    if "max_pages" in job and job["max_pages"] > MAX_PAGES_CAP:
        raise ValueError(
            f"max_pages={job['max_pages']} exceeds the crawler cap of {MAX_PAGES_CAP}; "
            f"the job would be rejected into jobs/failed/"
        )

    return job
