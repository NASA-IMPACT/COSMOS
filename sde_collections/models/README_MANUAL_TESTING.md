# COSMOS Curation System Testing Guide

Manual acceptance tests for the curation pipeline. This is the curator-facing counterpart to
[`LOCAL_VERIFICATION_GUIDE.md`](../../LOCAL_VERIFICATION_GUIDE.md), which verifies a local install
from a developer's point of view. Here the question is whether the workflow behaves correctly for
the people who use it.

The pipeline these tests exercise is described in [`WORKFLOW.md`](../../WORKFLOW.md), and what each
status change triggers is in [`README_STATUS_TRIGGERS.md`](./README_STATUS_TRIGGERS.md).

## Before you start

Every dispatch-gating setting defaults blank or off, so on an unwired host **nothing will happen**
when you change a status and the tests below will all appear to fail. Confirm first:

- `CRAWLER_INSTANCE_ID` and `SDE_S3_BUCKET` are set, and `SCRAPE_POLL_ENABLED=true`, for anything
  involving a scrape.
- `SDE_INDEX_BUCKET`, `INDEXING_ECS_CLUSTER`, `INDEXING_TASK_FAMILY`, `INDEXING_DISPATCH_ROLE_ARN`,
  `INDEXING_SUBNETS`, `INDEXING_SECURITY_GROUPS` are set, and `INDEX_POLL_ENABLED=true`, for
  anything involving indexing.
- `manage.py migrate` has been run **since** those flags were last changed. The poller schedules are
  `django_celery_beat` rows written by a `post_migrate` receiver, so a restart alone does not enable
  them.

Pick a small collection. Avoid one whose documents are already in the target index under a
different id scheme — the indexer refuses those deliberately, which looks like a failure but is
correct behaviour.

## Test Flow 1: Scrape dispatch and ingest

### Objective

Verify a collection can be scraped and its results ingested.

### Test Cases

#### 1.1 Dispatch

1. Set a collection's workflow status to **Ready for Engineering**.
2. Confirm a `ScrapeDispatch` row is created, carrying an `ssm_command_id` and `dispatched_at`.
3. Confirm the job JSON lands in the crawler's inbox. It is written via a temporary file and then
   moved, so the watcher should never see a partial file.
4. Failure path: with `CRAWLER_INSTANCE_ID` unset or the instance unreachable, confirm the status
   moves to **Scraping Failed** rather than hanging.
5. Cap check: request a page count above the crawler's cap (100,000) and confirm the job is
   rejected outright rather than silently clamped.

#### 1.2 Ingest

1. Wait for the crawler to write its results. The poller runs every 5 minutes.
2. Confirm the status moves to **Scraping Successful**, then on to **Ready for Curation**.
3. Confirm `DumpUrl` rows appear, then `DeltaUrl` rows after migration.
4. Confirm a summary is posted to Slack.
5. Staleness: confirm results older than the dispatch are ignored — the poller only accepts a
   summary written *after* `ScrapeDispatch.dispatched_at`.
6. Empty result: a scrape returning zero pages should land on **Scraping Failed**, not
   **Scraping Successful** with an empty collection.
7. Stall: with nothing fresh for longer than `SCRAPE_STALL_TIMEOUT_HOURS` (default 24), confirm the
   collection lands on **Scraping Failed**.

Expected results:

- Each status transition fires exactly once; re-saving a collection does not re-dispatch.
- Claiming is atomic, so two pollers running concurrently cannot double-ingest.
- With `INFERENCE_ENABLED=False` (the default) classification is skipped entirely and migration to
  DeltaUrls runs immediately.

## Test Flow 2: Curation and the test-indexing hand-off

### Objective

Verify curation promotes correctly and hands off to the indexer.

### Test Cases

#### 2.1 Promotion and dispatch

1. Curate the collection — apply include/exclude patterns, title and document-type changes.
2. Set the status to **Curated**.
3. Confirm `DeltaUrl`s are promoted to `CuratedUrl`s and the Delta set is cleared.
4. Confirm an export appears in S3 under `curated_collections/{config_folder}/{run_id}/`, with
   `documents.jsonl` written first and `manifest.json` **last**. The manifest's `document_count`
   must exactly match the JSONL line count.
5. Confirm excluded URLs are absent from the export.
6. Confirm an `IndexDispatch` row is created with a `run_id`, `target=test`, and a `task_arn`, and
   that the status moves to **Test Indexing**.
7. Empty-curation failure path: a collection with no curated URLs should fail dispatch and land on
   **Indexing Failed on Test** rather than exporting an empty file.

#### 2.2 Reading the result

1. The poller runs every 2 minutes. When the indexer finishes, confirm the collection **stays** in
   **Test Indexing** — a successful test run is not an automatic promotion.
2. Confirm the validation report is posted to Slack.
3. Failure path: confirm a failed run, an unrecognised result, or no result at all within
   `INDEX_STALL_TIMEOUT_HOURS` (default 6) lands on **Indexing Failed on Test**.

## Test Flow 3: Quality check and production indexing

### Objective

Verify the QC decision drives the production hand-off.

### Test Cases

1. From **Test Indexing**, set **QC: Perfect** and confirm a second indexing run is dispatched with
   a new `run_id`, and the status moves to **Production Indexing**.
2. On success, confirm the status lands on **Prod: Perfect**.
3. Repeat from **QC: Minor Issues** and confirm the terminal status is **Prod: Minor Issues** — the
   distinction must survive the round trip.
4. Failure path: confirm a failed production run lands on **Indexing Failed on Prod**.

## Test Flow 4: Re-scrape and re-curation

### Objective

Verify an already-published collection can be refreshed.

### Test Cases

1. Set `reindexing_status` to **Re-Indexing Needed** and confirm a *new* `ScrapeDispatch` row is
   created.
2. Confirm the poller ignores the previous scrape's S3 output until fresh results land.
3. Confirm the collection reaches **Ready for Re-Curation**.
4. Confirm patterns are reapplied to the new URLs and that manual, per-URL changes are preserved.
5. Set **Re-Curation Finished** and confirm promotion runs. Note the causality: the curator sets
   this status, and that triggers promotion — not the reverse.
6. Confirm **Re-Indexing Finished** triggers nothing on its own; the ingest task sets that status
   itself, and a second trigger would double-fire.

## Test Flow 5: Pattern system

### Objective

Test creation, application, and interaction of pattern types. This area is independent of the
scrape/index plumbing and is unchanged by the rewiring.

### Test Cases

#### 5.1 Include/exclude patterns

1. Create an exclude pattern for a directory:
   ```python
   pattern = "https://example.com/internal/*"
   ```
2. Create an include pattern for one file inside it:
   ```python
   pattern = "https://example.com/internal/public-doc.html"
   ```
3. Verify the include pattern overrides the exclude.
4. Test wildcard matching and precedence rules.
5. Confirm excluded URLs do not reach the export in Test Flow 2.

#### 5.2 Modification patterns

1. Create overlapping title patterns:
   ```python
   pattern1 = "*/docs/* → title='Documentation'"
   pattern2 = "*/docs/api/* → title='API Reference'"
   ```
2. Create division patterns of differing specificity.
3. Test document-type patterns with wildcards.
4. Verify "smallest set priority" resolution.
5. Check pattern application during migrations.

#### 5.3 Pattern removal

1. Remove a pattern affecting only Delta URLs.
2. Remove one affecting Curated URLs.
3. Verify handling where several patterns affect the same URL.
4. Confirm manual changes are preserved.

Expected results:

- Precedence rules are applied consistently.
- Manual changes survive pattern operations.
- Removing a pattern reverses its effects.

## Edge cases

### URL patterns

1. URLs with and without trailing slashes.
2. Overlapping wildcards.
3. Equal URL-count matches.
4. Maximum pattern chain depth.
5. Malformed URLs.

### Status transitions

1. Interrupted transitions.
2. Failed automated actions — every failure path should reach a terminal *failed* status, never
   leave the collection in an in-progress state indefinitely.
3. Concurrent status updates.
4. Invalid progressions.
5. Recovery: confirm a collection that reached **Scraping Failed** or **Indexing Failed on Test**
   can be re-driven through the workflow without manual database surgery.

### Data volume

1. Large collections (>100k URLs).
2. Pattern application performance.
3. Migration speed on large datasets.
4. Memory use during bulk operations.

## Common issues to watch for

1. **Nothing happens on a status change.** Almost always an unwired setting or a missing `migrate`
   — check the prerequisites above before investigating anything else.
2. **Pattern precedence.** Multiple patterns on one URL, include/exclude conflicts, equal-specificity
   resolution.
3. **Data integrity.** Field preservation across Dump → Delta → Curated, retention of manual
   changes, pattern effect tracking.
4. **Stale results.** The scrape poller uses dispatch time to reject old output; index runs are
   namespaced by `run_id`. A collection picking up a previous run's data is a bug worth reporting
   in detail.
5. **Status races.** Two workers acting on one collection, or a status change firing twice.
