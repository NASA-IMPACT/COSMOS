# Collection Status Workflows

This document outlines the automated workflows triggered by status changes in Collections.

## Workflow Status Transitions

Collections progress through workflow statuses that trigger specific automated actions:

### Initial Flow
1. `RESEARCH_IN_PROGRESS` → `READY_FOR_ENGINEERING`
   - Triggers: Creation of initial scraper and indexer configs

2. `READY_FOR_ENGINEERING` → `ENGINEERING_IN_PROGRESS` → `INDEXING_FINISHED_ON_DEV`
   - When indexing finishes, a developer changes the status to `INDEXING_FINISHED_ON_DEV`
   - This will trigger a full text fetch from LRM dev
   - If the fetch completes successfully, it updates the status to `READY_FOR_CURATION`

3. `READY_FOR_CURATION`
   - Triggers creation/update of plugin config

4. `READY_FOR_CURATION` → `CURATION_IN_PROGRESS` → `CURATED`
   - When curation finishes, the curator marks the collection as `CURATED`
   - This triggers the promotion of DeltaUrls to CuratedUrls

5. Quality Check Flow:
   - During quality checks the curator can put the status as `QUALITY_CHECK_PERFECT/MINOR`
   - These passing quality statuses will trigger the addition of the collection to the public query
   - After the PR is merged and SDE Prod server is updated with the latest code, this collection will become visible

### Reindexing Flow

After the main workflow, collections can enter a reindexing cycle:

1. `REINDEXING_NOT_NEEDED` → `REINDEXING_NEEDED_ON_DEV`
   - By default collections do not need reindexing
   - They can be manually marked as reindexing needed on dev

2. `REINDEXING_NEEDED_ON_DEV` → `REINDEXING_FINISHED_ON_DEV`
   - When re-indexing finishes, a developer changes the status to `REINDEXING_FINISHED_ON_DEV`
   - This will trigger a full text fetch from LRM dev
   - If the fetch completes successfully, it updates the status to `REINDEXING_READY_FOR_CURATION`

3. `REINDEXING_READY_FOR_CURATION` → `REINDEXING_CURATED`
   - When re-curation finishes, the curator marks the collection as `REINDEXING_CURATED`
   - This triggers the promotion of DeltaUrls to CuratedUrls

4. `REINDEXING_CURATED` → `REINDEXING_INDEXED_ON_PROD`
   - After the collection has been indexed on Prod, a dev marks it as `REINDEXING_INDEXED_ON_PROD`

## Full Text Import Process

The full text import process integrates with both workflows:

1. Clears existing DumpUrls for the collection
2. Fetches and processes new full text data in batches
3. Creates new DumpUrls
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
