# Collection Status Workflows

This document outlines the automated workflows triggered by status changes in Collections.
The single dispatcher is the `handle_workflow_status_change` post_save receiver in
`collection.py` (formerly `create_configs_on_status_change` — renamed in the Sinequa
retirement: it no longer creates configs).

## Workflow Status Transitions

Collections progress through workflow statuses that trigger specific automated actions:

### Initial Flow
1. `RESEARCH_IN_PROGRESS` → `READY_FOR_ENGINEERING`
   - Triggers `dispatch_scrape_job`: a job JSON (seed + any `ScraperConfigOverride`
     values) is written to the crawl4ai crawler's inbox on EC2 via SSM, and a
     `ScrapeDispatch` row records the dispatch time

2. Scrape completion (automated — no manual status change)
   - The `poll_scrape_jobs` beat task (every 5 min, gated on `SCRAPE_POLL_ENABLED`)
     watches S3 for a results summary fresher than the dispatch
   - On completion, `ingest_scraped_collection` claims the collection
     (→ `SCRAPING_SUCCESSFUL`), replaces its DumpUrls from S3, migrates to DeltaUrls,
     and lands on `READY_FOR_CURATION`
   - A zero-document crawl, a dispatch/ingest failure, or a stall past
     `SCRAPE_STALL_TIMEOUT_HOURS` lands on `SCRAPING_FAILED`

3. `READY_FOR_CURATION` → `CURATION_IN_PROGRESS` → `CURATED`
   - When curation finishes, the curator marks the collection as `CURATED`
   - This promotes DeltaUrls to CuratedUrls **and** enqueues `index_collection_to_test`
     (→ `TEST_INDEXING`) — the hand-off to the WEB_COSMOS indexing pipeline

4. Quality Check Flow:
   - During quality checks the curator can put the status as `QUALITY_CHECK_PERFECT/MINOR`
   - These passing quality statuses enqueue `index_collection_to_prod`
     (→ `PRODUCTION_INDEXING`)
   - Indexing failures surface as `INDEXING_FAILED_ON_TEST` / `INDEXING_FAILED_ON_PROD`

`INDEXING_FINISHED_ON_DEV` is a Sinequa-era status and no longer triggers anything.

### Reindexing Flow

After the main workflow, collections can enter a re-scrape cycle:

1. `REINDEXING_NOT_NEEDED` → `REINDEXING_NEEDED_ON_DEV`
   - Manually marked; triggers `dispatch_scrape_job` (same dispatch/poll path as the
     initial flow — this replaces the engineer manually re-running a Sinequa job)

2. Scrape completion (automated)
   - The poller watches the same S3 contract; ingest claims via
     `REINDEXING_NEEDED_ON_DEV → REINDEXING_FINISHED_ON_DEV` and the migrate task
     promotes to `REINDEXING_READY_FOR_CURATION`
   - `REINDEXING_FINISHED_ON_DEV` itself deliberately triggers **nothing**: the ingest
     sets it, so a trigger here would double-fire

3. `REINDEXING_READY_FOR_CURATION` → `REINDEXING_CURATED`
   - When re-curation finishes, the curator marks the collection as `REINDEXING_CURATED`
   - This triggers the promotion of DeltaUrls to CuratedUrls

4. `REINDEXING_CURATED` → `REINDEXING_INDEXED_ON_PROD`
   - After the collection has been indexed on Prod, a dev marks it as `REINDEXING_INDEXED_ON_PROD`

## Slack notifications

Status-transition messages (`STATUS_CHANGE_NOTIFICATIONS`) are sent from the post_save
receiver — never from `Collection.save()` — so a message cannot be sent for a save that
then fails. The detailed ingest summary is posted by the migrate task after delta counts
exist.

## Scrape Ingest Process

The S3 ingest (replacing the old Sinequa full-text import) integrates with both workflows:

1. Claims the collection via an atomic status compare-and-swap (the transition is the lock)
2. Clears existing DumpUrls for the collection
3. Creates new DumpUrls from the scraped documents in S3
4. Migrates DumpUrls to DeltaUrls
5. Updates collection status based on context:
   - In main workflow: Updates to `READY_FOR_CURATION`
   - In reindexing: Updates to `REINDEXING_READY_FOR_CURATION`

## New Pipeline Statuses (crawl4ai scraper + web indexing)

Statuses 21–26 support the Sinequa-replacement pipeline (see `WORKFLOW.md`). As of Phase 1
they are selectable and rendered everywhere; their triggers land in later phases (P3–P7):

- `SCRAPING_SUCCESSFUL` (21) — set by the ingest task when fresh scrape results with
  `documents_scraped > 0` are ingested from S3.
- `TEST_INDEXING` (22) — in-flight: curated content is being indexed to OpenSearch test.
- `SCRAPING_FAILED` (23) — scrape produced zero documents, the SSM dispatch failed, or the
  job stalled past the timeout.
- `INDEXING_FAILED_ON_TEST` (24) — the test-indexing run reported failure.
- `INDEXING_FAILED_ON_PROD` (25) — the prod-indexing run reported failure.
- `PRODUCTION_INDEXING` (26) — in-flight: curated content is being indexed to OpenSearch prod.

Failure statuses (23–25) render `btn-danger`; in-flight statuses (22, 26) render `btn-light`.
Both Python colour maps fall back to `btn-light` for unmapped values instead of raising
`KeyError`.

## Key Models and Files

- `Collection`: Main model handling status transitions
- `WorkflowStatusChoices`: Enum defining main workflow states
- `ReindexingStatusChoices`: Enum defining reindexing states
- `tasks.py`: Contains full text import logic and status updates
- Signal handler in Collection model manages status change triggers
