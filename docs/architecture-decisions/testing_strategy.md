## Overview
COSMOS's tests grew up around the EJ portal, the URL lifecycle, and the pattern system — the parts
of the app that were always ours. The rewiring changed what sits at the edges: scraping is now
COSMOS → SSM → the crawl4ai crawler on EC2 → S3 → `DumpUrl`s, and indexing is now COSMOS → an S3
export → `sts:AssumeRole` → `ecs:RunTask` → the WEB_COSMOS indexer, whose result COSMOS reads back
out of S3. Both of those halves were built with tests beside them.

This document records where testing effort belongs and why, so that new tests land where a
regression is expensive rather than where code happens to be easy to exercise. It is deliberately
qualitative: the coverage numbers are produced by CI on every pull request, and a table pasted in
here goes stale the day after it is written.

## How the suite runs
- `pytest.ini` pins `--ds=config.settings.test --reuse-db`; everything runs against
  `config/settings/test.py`.
- CI (`.github/workflows/run_full_test_suite.yml`) triggers on pull requests to `dev`, builds the
  `local.yml` stack, runs `bash ./init.sh`, then `coverage report`.
- `init.sh` runs each `test_*.py` file as its own pytest process under `coverage run --append`,
  excluding `document_classifier/` and `functional_tests/`. To see current coverage locally:
  `docker-compose -f local.yml run --rm django bash ./init.sh` followed by
  `docker-compose -f local.yml run --rm django coverage report`.

Two properties of the test settings are load-bearing and must survive any refactor of them:

- `CELERY_BROKER_URL` is forced to `memory://` (both the setting and the environment variable).
  Without it, any test that changes a workflow status would publish a real message to the same
  Redis the local `celeryworker` consumes, and that worker would run the task against the *local*
  database.
- Every pipeline setting (`SDE_S3_BUCKET`, `CRAWLER_INSTANCE_ID`, `SDE_INDEX_BUCKET`, `INDEXING_*`,
  `SCRAPE_POLL_ENABLED`, `INDEX_POLL_ENABLED`, `INFERENCE_ENABLED`) defaults to blank/off, so a test
  that forgets to mock is pointed at no real bucket, instance, or cluster. Tests that need those
  values supply them with `override_settings`.

## Where the tests live
| Location | What it covers |
|---|---|
| `sde_collections/tests/` | The bulk of the suite: scrape dispatch and ingest, the indexing hand-off, workflow-status triggers, the URL lifecycle, the pattern system, the inference flag, AWS session selection, the URL APIs, the backup/restore commands. |
| `sde_collections/tests/frontend/` | Selenium tests (auth, homepage features, pattern application). They `pytest.fail` unless `chromedriver` and `chromium` are on `PATH`. |
| `inference/tests/` | The classification pipeline, which is dormant (`INFERENCE_ENABLED` defaults to `False`) but not deleted. Its unit tests still run; `test_inference_integration.py` skips itself unless a live inference API is reachable. |
| `environmental_justice/tests/`, `sde_indexing_helper/users/tests/`, `scripts/ej/`, `tests/` | The EJ API, the user app, the EJ CMR/threshold processing scripts, and the dotenv merge helper. |
| `document_classifier/`, `functional_tests/` | Excluded from `init.sh` and from CI. `functional_tests/test_check_collection.py` is a Sinequa-era Selenium script pointed at the retired `sciencediscoveryengine.*` endpoints; it no longer describes anything the system does. |

## Critical Areas

### Scraping: dispatch and ingest
This is a contract with another repository, expressed in shell commands and S3 key names — the
class of thing that breaks silently. Cover, at minimum:

- `sde_collections/scraping/job_builder.py` — `build_job_json()`: which override fields are emitted
  (`None` is skipped, `False` is not), and the `MAX_PAGES_CAP` refusal.
- `sde_collections/scraping/ssm_dispatch.py` — `send_job_to_crawler()`: the exact command sent, the
  `.tmp` + `mv` atomic delivery, shell quoting of hostile seed URLs, and the SSM comment limit.
- `sde_collections/scraping/s3_results.py` — the key layout, missing-key codes meaning "not
  finished" rather than an error, and `results_ready()` rejecting a summary older than the latest
  `ScrapeDispatch` (without which a re-dispatch would instantly "complete" against the previous
  run's output).
- `sde_collections/tasks.py` — `dispatch_scrape_job()` (failure lands on **Scraping Failed** and
  never raises), `poll_scrape_jobs()` (which statuses are scanned, the stall timeout), and
  `ingest_scraped_collection()` (the compare-and-swap claim, zero documents counting as a failure,
  replay idempotence, and failure after a claim not stranding the collection).

### Indexing hand-off
The export layout is fixed by the indexer and cannot be renegotiated in a patch release, so its
shape belongs in tests:

- `sde_collections/indexing/export.py` — manifest written **last**, `document_count` exactly
  matching the JSONL line count, excluded URLs absent, title/label resolution, and the refusal to
  export with a blank bucket.
- `sde_collections/indexing/dispatch.py` — the settings guard, role assumption, the full command
  override (the image has no entrypoint, so the executable must be restated), and `RunTask`
  failures surfacing as errors.
- `sde_collections/indexing/run_status.py` — status/validation reads under the `run_id` prefix, and
  a missing `status.json` meaning "in flight".
- `sde_collections/tasks.py` — `index_collection_to_test()` / `index_collection_to_prod()` and
  `poll_index_runs()`: the `IndexDispatch` record, the in-flight and failed statuses, prod success
  mirroring the QC status the run entered with, unknown states counting as failure, and an old
  run's status never resolving a newer dispatch.

### Workflow status machine
`sde_collections/models/collection.py` is where the pipeline is actually wired: which status change
promotes, which enqueues an index run, the re-entrancy guard, the Slack notification (whose failure
must not break the save), and `WorkflowHistory` rows. Every status and reindexing status must
resolve to a button colour — an unmapped status silently rendering neutral is a real defect class.
The complementary assertion is negative: no removed Sinequa method may reappear on a transition.

### URL lifecycle
`DumpUrl → DeltaUrl → CuratedUrl` is the core data model, described in
`sde_collections/models/README_LIFECYCLE.md`:

- `Collection.migrate_dump_to_delta()` and `create_or_update_delta_url()` — the diff, including
  deletion markers and `DELTA_COMPARISON_FIELDS`.
- `Collection.promote_to_curated()` — updates, deletions, metadata changes, repeated promotions,
  and patterns re-applied afterwards.
- `sde_collections/models/delta_url.py`, `candidate_url.py`.

### Pattern system
`sde_collections/models/delta_patterns.py` and `pattern.py` carry the most intricate logic in the
repo: apply and unapply for exclude, include, title, document type, division and other field
modifiers, plus specificity resolution when patterns overlap. This area is comparatively well
covered; keep it that way, and add a test for every reported mis-application rather than for the
fix alone.

### Inference gating
The classification pipeline is disabled, not removed. What must stay tested is the gate itself:
`queue_necessary_classifications()` short-circuiting straight to migration when
`INFERENCE_ENABLED` is `False`, and `inference/signals.py` re-asserting `enabled` on its beat rows
from the flag on every `post_migrate` — the flag, not a hand-edit in the admin, is the source of
truth. Tests here should call the real method and patch only the queued task's `.delay`; patching
the method wholesale would guard nothing.

### AWS session boundary
`sde_collections/utils/aws.py::get_boto3_session()` decides between explicit `SDE_AWS_*` keys (local
dev) and the default credential chain (instance role in AWS), and deliberately ignores the
`DJANGO_AWS_*` static-assets credentials. Partial keys must fall back rather than half-configure.

### APIs, serializers, and the UI
`sde_collections/views.py` and `sde_collections/serializers.py` back the curation UI and the
DataTables endpoints. The list APIs keyed by `config_folder` are covered; the viewsets, the bulk
create path, and `CollectionDetailView.post` are thinner.

### Operational surfaces
`sde_collections/management/commands/` (backup/restore are covered; the pipeline commands are not),
`sde_collections/admin.py` actions, and `sde_collections/utils/slack_utils.py` message formatting.

## Critical Areas Lacking Tests
- **Beat-row creation for the pollers** — `sde_collections/signals.py` creates the `poll_scrape_jobs`
  and `poll_index_runs` schedules on `post_migrate` and re-asserts `enabled` from
  `SCRAPE_POLL_ENABLED` / `INDEX_POLL_ENABLED`. The equivalent handler in `inference/signals.py` is
  tested; this one is not.
- **Pipeline management commands** — `dispatch_scrape`, `ingest_scrape_results`,
  `migrate_urls_and_patterns`, `deduplicate_patterns`, `deduplicate_urls`, `export_urls_to_csv`,
  `sync_with_production_webapp`.
- **Admin actions** — the CSV export, the exclude/include pattern actions, and the read-only
  guarantees on the `ScrapeDispatch` / `IndexDispatch` admins.
- **Slack message construction** — `send_detailed_import_notification()` and
  `send_indexing_validation_report()` are exercised only as patched call sites; the message bodies
  themselves are untested.
- **Views and serializers** beyond the URL list APIs.
- **Project settings** — `config/settings/local.py` and `production.py` have no tests.
- **Frontend** — the Selenium suite covers auth, the homepage, and pattern application; the rest of
  the curation UI is unverified, and the suite is skipped wherever Chromium is absent.

## Conventions for new pipeline tests
- Mock at the seam, not at AWS: patch `get_boto3_session` *in the module under test*
  (`sde_collections.indexing.export.get_boto3_session`, `…scraping.s3_results._get_object`), or the
  task-module alias of a helper (`sde_collections.tasks.fetch_run_status`). Patching
  `boto3` globally hides which client a module actually asks for.
- Drive the pipeline settings with `override_settings`; never rely on a developer's `.envs`.
- Patch `.delay` when a test changes a workflow status, unless the enqueue *is* what is being
  asserted.
- Assert on the request that would have gone out — the SSM command text, the S3 key, the `RunTask`
  overrides — rather than on the mock having been called. These are cross-repo contracts, and the
  arguments are the contract.
