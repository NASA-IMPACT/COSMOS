# COSMOS Test Audit

**Branch:** `cosmos-rewiring` · **Date:** 2026-08-14 · **Status:** all changes uncommitted on the working tree

**Goal:** verify that every test in the repository actually exercises production behavior — that mocks sit at external boundaries (AWS, HTTP, Celery, Slack) while assertions land on real code paths and database state, never on the mock's own configuration.

| Metric | Before | After |
|---|---|---|
| Full-suite result | **66 failed**, 401 passed, 2 collection errors | **482 passed, 0 failed**, 2 env-gated skips |
| Runtime | ~3:54 | ~37s |
| New boundary tests | — | 14 |
| Vacuous / dead tests repaired | — | 15 |
| Lint | — | flake8 clean on all touched files |

---

## 1 · Method

Every test file changed or added on this branch was reviewed line-by-line; the legacy suites (pattern/delta/promotion, users, feedback, environmental justice, inference, management commands) were audited in a parallel sweep. Each test was classified as:

- **Vacuous** — patches the system under test itself, asserts only what the mock was configured to return, or asserts a condition that cannot fail. These stay green with broken production code.
- **Boundary-mocked (healthy)** — mocks external services but asserts real DB state, return values, or logic branches.
- **Plain functional** — no mocks.

**Verdict on the pre-existing suite:** healthier than its mock density suggests. The ~2,500 lines of pattern/delta/promotion tests are essentially mock-free and carry the real regression protection. The rot was concentrated in the backup-command tests, a few inference tests, and three self-referential or assertion-free tests — all repaired below.

---

## 2 · New coverage: the AWS boundary modules

The branch's new pipeline tests (`test_scrape_dispatch`, `test_scrape_ingest`, `test_indexing_dispatch`, `test_inference_flag`, `test_workflow_status_triggers`) were already well-shaped. But every caller-side test mocks the three AWS boundary modules away, so their internal logic had **zero coverage** — the S3 key layouts that form the contract with the crawler and indexer, the SSM script construction, and the missing-key-versus-real-error branching. 14 tests were added (12 functions, 14 runs with parametrization):

| Module | New tests (location) | What is now proven |
|---|---|---|
| `scraping/ssm_dispatch.py` | `TestSendJobToCrawler` ×4 (test_scrape_dispatch.py) | The generated shell script is shell-split and the job JSON recovered by round-trip — the payload the crawler receives equals `build_job_json()` exactly, including a hostile seed URL with quotes/spaces/ampersands. Write is atomic (`.tmp` → `chown` → `mv`, in that order), the command targets `CRAWLER_INSTANCE_ID` via AWS-RunShellScript, and the SSM comment is truncated to its 100-char limit. |
| `scraping/s3_results.py` | `TestS3ResultFetchers` ×4, 5 runs (test_scrape_ingest.py) | Exact crawler key contract: `failure_logs/{id}_failures_summary.json` and `scraped_collections/{id}.json` against `SDE_S3_BUCKET`; `LastModified` passthrough (feeds the staleness rule); `NoSuchKey`/`404` → "run not finished" (`None`); `AccessDenied` raises rather than reading as "still crawling" forever. |
| `indexing/run_status.py` | `TestRunStatusFetchers` ×4, 5 runs (test_indexing_dispatch.py) | Exact indexer key contract: `index_runs/{config_folder}/{run_id}/status.json` and `validation.json` against `SDE_INDEX_BUCKET`; missing key → in-flight (`None`); real S3 errors propagate instead of stalling to timeout. |

Also tightened in the branch tests: the Slack-notification assertion in `test_workflow_status_triggers.py` contained `or "<" in message`, which made it nearly impossible to fail; it now asserts the collection name **and** the transition-specific message text.

---

## 3 · Vacuous tests repaired

| File | Defect | Repair |
|---|---|---|
| `sde_collections/tests/test_database_backup.py` | Three tests could never fail: error/cleanup assertions checked that a file at a bare relative path — which production never writes (it writes to `/app/backups/`) and which the mocked `pg_dump` never created — did not exist. `test_handle_compression_error` additionally mocked a method on a fixture `Command` instance that `call_command` never touches. | The mocked `pg_dump` now genuinely writes a dump file. The real `compress_file` gzips it (content verified by decompressing), the real `temp_file_handler` cleanup is observed, error paths assert the reported message ("Backup failed" / "Error during backup process") plus absence of artifacts, and `compress_file` is patched on the class so the failure actually occurs. The integration test now pins the exact `/app/backups/…` path. |
| `sde_collections/tests/test_url_apis.py` | `test_candidate_url_api_alias` reversed the same URL name twice into one variable and asserted a response equal to itself. | Now compares `candidate-urls-api` against `curated-urls-api` — the actual alias contract (both routes serve `CuratedURLAPIView`) — with distinct-route and non-empty-payload checks. |
| `sde_collections/tests/test_promote_collection.py` | `test_promotion_with_overlapping_patterns_and_deletion` had zero assertions — its "verification" was `print()` loops. `test_promotion_with_title_change` ended with a bare call and a comment about an expected production error. | Real assertions on exact pattern↔URL relations before and after a deletion promotion — which exposed a latent bug in the test itself (§4.2). The title-change test now asserts the update carries through and the pattern relation survives. |
| `sde_collections/tests/test_migrate_dump.py` | The file kept its own copy of `DELTA_COMPARISON_FIELDS` ("assuming a central definition") — silently drift-prone — and `test_empty_delta_comparison_fields` "emptied" that local copy, a no-op on production. | Imports the production constant from `models/collection.py`; the empty-fields test patches it in the module where production reads it, with *differing* titles, genuinely proving the field list drives delta creation. |
| `inference/tests/test_classification_utils.py` | `test_threshold_parameter_behavior` asserted that the `threshold` argument is *discarded* — certifying a live production bug as correct behavior. | Production bug fixed (§5); the test now asserts the threshold is forwarded to `map_classification_to_tdamm_tags`. |
| `inference/tests/test_batch.py` | `test_extremely_large_text` patched two methods of the `BatchProcessor` under test and never checked the truncation its docstring promised. `test_integration_with_mock_django_db` carried a dead `patch.object` wrapper and misleading comments. | The batch limit is constructor-configurable, so the test now feeds real 250-char text against a limit of 100 and asserts the emitted batch contains the actually-truncated text. The integration test drops the dead patch and asserts text and metadata produced by the real `prepare_url_data`. |
| `sde_collections/tests/test_delta_patterns.py` | Two dead statements where assertions were clearly intended: a discarded `.first()` queryset (plus a commented-out `apply()`), and an attribute assignment never saved. | Both became assertions: the equal-titles test now proves the pattern *matched* the CuratedUrl (so the missing DeltaUrl is a deliberate skip, not a failed match); the reapplication test asserts the title was applied on create (`save()` auto-applies patterns). |

---

## 4 · Failures found and their root causes

### 4.1 · 66 tests failing in every full-suite run — infra bug, fixed

`environmental_justice/tests/conftest.py` registered an **autouse fixture that permanently overwrote** `settings.ROOT_URLCONF` with its private EJ-only URL table and never restored it. The EJ module collects early (alphabetical order), so every later test that resolves a named URL failed with `NoReverseMatch` — while passing in isolation, which is why it went unnoticed. Pre-existing on `dev`; unrelated to the rewiring branch. Fixed with pytest-django's self-restoring `settings` fixture (the test-local urlconf itself is legitimate: the EJ API has no registration in the project urlconf). Runtime fell from ~3:54 to ~37s once the failure churn disappeared.

| File | Failed | Tests |
|---|---|---|
| `feedback/tests.py` | 20 | All of `TestFeedbackAPI` (8: dropdown options, create success, invalid email, 4× missing-field, invalid dropdown) and `TestContentCurationRequestAPI` (12: create success, without additional info, invalid email, 5× missing-field, 4× max-length). Only the 2 pure model tests survived. |
| `sde_collections/tests/test_url_apis.py` | 19 | `TestDeltaURLAPIView` (5: empty list, with data, wrong config folder, serializer fields, pagination) and `TestCuratedURLAPIView` / `TestCandidateURLAPIView` (7 each: empty list, with data, wrong config folder, serializer fields, alias, multiple collections, invalid filters). |
| `sde_collections/tests/frontend/` | 15 | `test_auth.py` (failed login, logout, successful login); `test_homepage_features.py` (collections display, universal search, 6 search panes: connector type, curated URLs, curator, division, reindexing status, workflow status); `test_pattern_application.py` (create document-type / exclude / include / title pattern). |
| `sde_indexing_helper/users/tests/` | 12 | `test_admin.py` (changelist, search, add, view user); `test_views.py` (get_success_url, form_valid, get_redirect_url, not_authenticated); `test_urls.py` (detail, update, redirect); `test_models.py` (get_absolute_url). |

### 4.2 · Latent test bug: wildcard vs. regex match patterns — masked bug, fixed

Adding real assertions to the overlapping-patterns promotion test revealed its regex-idiom patterns (`.*docs.*` etc.) **matched zero URLs**: `BaseMatchPattern.get_regex_pattern()` runs `re.escape()` on the pattern and only translates `*` wildcards — so `.*docs.*` becomes a literal-dot regex that never matches. The print-only "assertions" had concealed for the test's whole life that it tested an empty scenario. Converted to wildcard idiom (`*docs*`, `*api/v1/doc*`, …) with exact expected relation sets, verified against actual behavior.

### 4.3 · Two directories cannot import in the test container — pre-existing, excluded

A bare `pytest` in the Django container aborts collection on `functional_tests/` (imports `webdriver_manager`, installed nowhere) and `document_classifier/` (imports `numpy`). Neither is a real pytest suite: `functional_tests/test_check_collection.py` is a standalone Selenium script that takes a collection name from `sys.argv`, drives real Chrome, and targets the *live* NASA Sinequa servers — infrastructure this branch deletes. The project's own CI (`init.sh`, line 8) already excludes both directories; the audit runs used matching `--ignore` flags.

---

## 5 · Production code changes

Two non-test files changed; everything else is test-only.

- **`inference/utils/classification_utils.py`** — bug, fixed. `update_url_with_classification_results(…, threshold=X)` accepted and documented a `threshold` parameter but silently discarded it; every caller got `settings.TDAMM_CLASSIFICATION_THRESHOLD` regardless. One-line fix forwards it. No live behavior change on this branch (inference is dormant, `INFERENCE_ENABLED=False`) — **flag to the team anyway**.
- **`environmental_justice/tests/conftest.py`** — the URLconf-leak fix (§4.1). Test infrastructure only.

---

## 6 · Current state

```
482 passed, 2 skipped, 0 failed   (~37s; was 66 failed, ~3:54)
flake8 clean on all touched files (isort applied)
```

13 files modified, all **uncommitted** on `cosmos-rewiring`: 11 test files, 1 production fix (`classification_utils.py`), 1 test-infra fix (EJ conftest). The 2 skips are pre-existing environment-gated skips, unchanged. Verification:

```bash
docker compose -f local.yml run --rm django pytest -q \
    --ignore=document_classifier --ignore=functional_tests
```

---

## 7 · Flagged but deliberately not changed

- **`inference/tests/test_inference_integration.py`** — every test skips via fixture when `http://host.docker.internal:8000` is unreachable, so in CI the module is unconditionally green while asserting nothing. Coverage theater rather than vacuous mocking; consider gating on an env var that CI sets explicitly.
- **`test_field_modifier_patterns.py`** — three tests assert only that model fields equal the values just passed to `objects.create()` (testing Django, not the app). Harmless; low value.
- **`test_database_restore.py`** — monkeypatches `pytest.mark` at import time to define `integration`. Works, but fragile and affects any other module using that mark name; a `conftest`/`pytest.ini` marker registration would be safer.
- **`test_delta_patterns.py`** (2 spots) — expected titles computed by calling the same `resolve_title()` the production path calls; a bug there changes both sides identically. Would need hand-computed expected strings to close.

> **Recommendation:** add `--ignore=document_classifier --ignore=functional_tests` to `addopts` in `pytest.ini` (or rename the Selenium script off the `test_*.py` glob) so a plain `pytest` in the container behaves like CI instead of aborting on collection errors.
