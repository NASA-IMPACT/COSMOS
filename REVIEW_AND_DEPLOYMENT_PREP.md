# Review & Deployment Prep — `cosmos-rewiring` + `sde-api-scrapers` web indexing

Prepared 2026-08-25 against COSMOS `cosmos-rewiring` @ `c1505d36` (14 commits over `dev`, 130 files, +6440/−9372)
and `sde-api-scrapers` `web-indexing` @ `8dde345` (local checkout; see §1 — the work itself lives on `develop`).

---

## 0. TL;DR

1. **COSMOS branch review findings are applied in the working tree (uncommitted, 2026-08-25)** — §4 has a
   status column. Fixed: A (`on_commit`), B/C (dead Slack transitions), D (re-scrape clobbering prod status),
   E (unwired-host guard), G (in-crawl URL de-dup), H, I, K, template leftovers, gitleaks config, release notes,
   and the test gaps. Still open: F (whole-crawl-in-memory ingest), L (clock skew), cross-collection duplicate
   URLs (design call), DB indexes, and the out-of-band credential rotation. Full `init.sh` suite is green.
2. **`sde-api-scrapers/web-indexing` is already merged and deployed.** PR #47 (`c2aebad`) landed on `develop`
   and the dev stacks deployed 2026-08-20. The local `web-indexing` branch is now *behind* `develop` — diffing it
   against `develop` yields a **revert of the RDR prod-freeze work (PR #49/#50)**. Do not open a PR from it;
   rebase or delete it. "Review the indexer" means reviewing `web/` + the shared uploader changes as they sit on
   `develop`.
3. **One gate remains before the closed loop can run: C.2** — wire the P7 env block on the **staging** host,
   run `migrate` (the beat rows come from `post_migrate`), recreate containers. Infra on both sides is in place.
4. **One indexer bug must land before any test/prod tier deploy (R1):** the guards read the tier-capped endpoint
   but `APIOpenSearchUploader` writes to bare `OPENSEARCH_ENDPOINT`. Harmless in dev (same collection), a
   guard-bypass in prod.
5. **The production DB password is still in git history** (scrubbed from `SQLDumpRestoration.md` on this branch,
   but present on `dev`). Rotate it; the scrub alone does nothing. The gitleaks hook that should have caught it
   points at a `gitleaks-config.toml` that does not exist.
6. Uncommitted: COSMOS `.pre-commit-config.yaml` (pyupgrade bump `v3.20.0→v3.21.2`); scrapers repo has a
   status-update edit to the task tracker and an **untracked `COSMOS_INDEX_REAL_RUN.md`** which is the best
   description of the hand-off contract anywhere — commit it.

---

## 1. Branch state

| Repo | Branch | vs base | Notes |
|---|---|---|---|
| COSMOS | `cosmos-rewiring` @ `c1505d36` | 14 commits over `dev` (Phase 0–7) | Tree clean except `.pre-commit-config.yaml`. CI (`run_full_test_suite.yml`) runs only on PRs to `dev`, `paths-ignore: '**/*.md'`. |
| sde-api-scrapers | `web-indexing` @ `8dde345` | `origin/develop..web-indexing` = 1 commit (the merge); `web-indexing..origin/develop` = 8 commits | Web indexing merged via PR #47. Diff vs `develop` = removal of `RDR_API_BASE_URLS`/`_resolve_base_url()`/`schedule_enabled` — i.e. it would re-enable the frozen prod RDR EventBridge rule and reintroduce the silent sandbox fallback. |

Uncommitted / untracked:
- COSMOS: `.pre-commit-config.yaml` — pyupgrade `v3.20.0 → v3.21.2`. Fine to commit with the branch.
- scrapers: `Web Indexing - Task Plan & Tracking.md` (records NS.2 done, NS.7 closed, OOB.3 verified, ECR digest
  `ae1c9e02…` co-tagged `c2aebad…`, image linux/amd64 only); `COSMOS_INDEX_REAL_RUN.md` (untracked runbook, "not
  yet executed end to end").

---

## 2. What the COSMOS branch does

**Pipeline in one paragraph.** A curator moves a collection to *Ready for Engineering* → `post_save` enqueues
`dispatch_scrape_job`, which drops a crawl4ai job JSON into the crawler EC2 inbox over SSM `AWS-RunShellScript`
and records a `ScrapeDispatch`. `poll_scrape_jobs` (beat, every 5 min) watches
`s3://{SDE_S3_BUCKET}/failure_logs/{cf}_failures_summary.json`; a summary newer than `dispatched_at` triggers
`ingest_scraped_collection`, which claims the collection with a compare-and-swap, replaces `DumpUrl` rows from
`scraped_collections/{cf}.json`, then runs the existing delta migration → *Ready for Curation*. Inference is
present but dormant (`INFERENCE_ENABLED=False`). On *Curated*, `promote_to_curated()` then
`index_collection_to_test` exports `CuratedUrl` rows as JSONL to `s3://{SDE_INDEX_BUCKET}/curated_collections/{cf}/{run_id}/`
(`manifest.json` written last), assumes `INDEXING_DISPATCH_ROLE_ARN`, and `ecs:RunTask`s the indexer with a full
command override. `poll_index_runs` (every 2 min) reads `index_runs/{cf}/{run_id}/status.json`; test success
posts `validation.json` to Slack and holds at *Test Indexing*; a curator sets QC Perfect/Minor → prod dispatch →
*Production Indexing* → `PROD_PERFECT`/`PROD_MINOR`. Sinequa, GitHub config push, XML generation and the
health-check module are deleted outright.

### New modules

| Path | Purpose |
|---|---|
| `sde_collections/scraping/job_builder.py` | Pure `build_job_json(collection)` — seed URL + `collection_id` + non-null `ScraperConfigOverride` fields; refuses `max_pages > 100_000`. |
| `sde_collections/scraping/ssm_dispatch.py` | `send_job_to_crawler` — write `.tmp` → `chown` → `mv -f` into `CRAWLER_INBOX_PATH` via SSM; `shlex.quote`d. |
| `sde_collections/scraping/s3_results.py` | `fetch_summary`/`fetch_documents`/`results_ready` — missing key = not ready; `LastModified <= dispatched_at` = stale. |
| `sde_collections/indexing/export.py` | `export_curated_to_s3` — streams non-excluded `CuratedUrl` to JSONL, manifest last with exact `document_count`. |
| `sde_collections/indexing/dispatch.py` | `run_index_task` — settings guard, `sts:AssumeRole`, fresh ECS client, RunTask with full command override, optional `awsvpc` config. |
| `sde_collections/indexing/run_status.py` | `fetch_run_status`/`fetch_validation_report` from S3 only (never `ecs:DescribeTasks`). |
| `sde_collections/models/scraper_config.py` | `ScraperConfigOverride` (1:1, curator-editable), `ScrapeDispatch`. |
| `sde_collections/models/indexing.py` | `IndexDispatch` (`run_id`, `target`, `task_arn`, `previous_workflow_status`, `completed_at`). |
| `sde_collections/signals.py` | `post_migrate` creates/updates two `django_celery_beat` rows and re-asserts `enabled` from settings on every migrate. |
| `sde_collections/utils/aws.py` | `get_boto3_session()` — `SDE_AWS_*` keys if both set, else instance role. Ignores `DJANGO_AWS_*`. |
| `sde_collections/utils/slack_utils.py` | 10 new transition messages + `send_indexing_validation_report`. |
| `sde_collections/tasks.py` | `dispatch_scrape_job`, `poll_scrape_jobs`, `ingest_scraped_collection`, `_dispatch_index_run`, `index_collection_to_{test,prod}`, `poll_index_runs`. |
| `management/commands/{dispatch_scrape,ingest_scrape_results}.py` | Synchronous manual entry points (`--collection <config_folder>`); ingest uses `claim=False`. |

### New settings (`config/settings/base.py:346-382`; mirrored in `.env_sample`, `.envs/.local/.django`)

| Setting | Default | Setting | Default |
|---|---|---|---|
| `AWS_REGION` | `us-east-1` | `SDE_INDEX_BUCKET` | `""` |
| `SDE_S3_BUCKET` | `""` | `INDEXING_ECS_CLUSTER` | `""` |
| `CRAWLER_INSTANCE_ID` | `""` | `INDEXING_TASK_FAMILY` | `""` |
| `CRAWLER_INBOX_PATH` | `/opt/sde-crawler/jobs/incoming` | `INDEXING_CONTAINER_NAME` | `WEB_COSMOSContainer` |
| `SCRAPE_POLL_ENABLED` | `False` | `INDEXING_DISPATCH_ROLE_ARN` | `""` |
| `SCRAPE_STALL_TIMEOUT_HOURS` | `24` | `INDEXING_SUBNETS` | `""` |
| `INFERENCE_ENABLED` | `False` | `INDEXING_SECURITY_GROUPS` | `""` |
| `SDE_AWS_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY` | `""` (local only) | `INDEX_POLL_ENABLED` | `False` |
| | | `INDEX_STALL_TIMEOUT_HOURS` | `6` |

Removed: `GITHUB_ACCESS_TOKEN`, `SINEQUA_CONFIGS_*`, `XLI_*`, `LRM_*`. Dropped deps: `PyGithub`, `xmltodict`.
`config/settings/test.py` forces `CELERY_BROKER_URL=memory://` (without it tests publish real tasks).

### Migrations & statuses
- `0078` — `AlterField` for six new `WorkflowStatusChoices` (21 `SCRAPING_SUCCESSFUL`, 22 `TEST_INDEXING`,
  23 `SCRAPING_FAILED`, 24 `INDEXING_FAILED_ON_TEST`, 25 `INDEXING_FAILED_ON_PROD`, 26 `PRODUCTION_INDEXING`).
  Also sweeps unrelated `match_pattern_type` default drift on five delta-pattern models. **No data migration —
  none needed**; values are additive and `dev` topped out at 20.
- `0079` — `ScraperConfigOverride`, `ScrapeDispatch`. `0080` — `IndexDispatch`. All additive → rollback-safe.
- Orphaned statuses `8`, `10`, `17`, `20` remain in choices but nothing advances them any more (the
  `IndexingInstructionsView` that drove 8→10 is gone). Audit prod rows parked there.

---

## 3. What the indexer side does (`sde-api-scrapers` `develop`)

- Entry: `python3 api_scraper.py --source WEB_COSMOS --collection <key> --run-id <id> [--target test|prod]
  [--reconcile] [--web-index NAME] [--allow-id-collision]` (`api_scraper.py:616,695-728`). Exit 0 iff
  `status.state == "succeeded"`. Excluded from `--source ALL`.
- `web/web_pipeline.py` orchestrates: load manifest → ensure index → probe scope → id-collision check →
  scan existing ids → deletion guard → index/vectorize → tombstone → write `status.json` (+ `validation.json`
  when `--target test`).
- **Contract with COSMOS** (`web/cosmos_source.py:4-11`):
  ```
  COSMOS writes  curated_collections/{collection_key}/{run_id}/documents.jsonl
                 curated_collections/{collection_key}/{run_id}/manifest.json   ← must be LAST
  indexer writes index_runs/{collection_key}/{run_id}/status.json
                 index_runs/{collection_key}/{run_id}/validation.json          (test only)
  ```
  Manifest requires `collection_key`, `run_id`, `document_count`; also reads `collection_name`,
  `document_type`, `division`. Per-doc passthrough is `url`, `title`, `full_text` only — **`tdamm_tag` is
  dropped** at `web/web_processor.py:18-25`. Doc id `/SDE/{collection_key}/|{url}`; `version` = sha256[:32]
  of `[title, full_text, document_type, division]`.
- Index: working `sde-web-subset` (59 docs, 2 collections, mapping verified); live `sde-web` (431k docs,
  **no `version` field yet** — OOB.1). Mapping in `web/index_mappings/sde_web.json`.
- Runtime: Fargate 2 vCPU / 8 GB, family `web_cosmos-scraper-dev`, container `WEB_COSMOSContainer`,
  cluster `api-scrapers-cluster-dev`, logs `/ecs/api-scrapers-dev`. No cron, no monitoring alarm, **no
  `ENTRYPOINT`** — the baked command is a placeholder that argparse rejects; COSMOS must send the full
  command override (it does: `indexing/dispatch.py:47-58`).
- IAM: `CosmosIndexingDispatchRole-dev` trusts only `indexing-helper-role`; `RunTask` limited to the family +
  cluster; `PassRole` on the two ECS roles. Bucket policy grants COSMOS put on `curated_collections/*`, get
  on `index_runs/*`. No SSM parameters are used on the web path.
- Tier capping (`infrastructure/config/settings.py:330-350`): dev→dev/dev, test→test/test, prod→test/prod.

---

## 4. Code review checklist — COSMOS

Status column reflects the working tree as of 2026-08-25 (fixes applied, uncommitted; full `init.sh` suite green).

### High

| # | Status | Finding | Where | Resolution |
|---|---|---|---|---|
| A | ✅ fixed | `.delay()` fired inside `post_save`, no `transaction.on_commit`. Admin change views are atomic, so `export_curated_to_s3` could run before `promote_to_curated()`'s rows commit → false `INDEXING_FAILED_ON_TEST`. | `sde_collections/models/collection.py` `handle_workflow_status_change` | `_enqueue_on_commit()` wraps all four `.delay()` calls. Test: `test_task_is_enqueued_only_after_commit`. |
| B | ✅ fixed | Statuses set via queryset `.update()` bypassed `post_save`, so the `SCRAPING_SUCCESSFUL` / ingest-side `SCRAPING_FAILED` Slack messages never fired. | `tasks.py` ingest + `_mark_scrape_failed`; `utils/slack_utils.py` | `notify_status_change()` posts the mapped message after every `.update()`-set transition. Test: `test_claim_posts_the_scraping_successful_notification`. |
| C | ✅ fixed | "Live on Public Prod" keyed on `QC_* → PROD_*`, but the flow goes `PRODUCTION_INDEXING → PROD_*`. | `utils/slack_utils.py` `STATUS_CHANGE_NOTIFICATIONS` | Added `(PRODUCTION_INDEXING, PROD_PERFECT/PROD_MINOR)` pairs. Test: `test_prod_handoff_transitions_are_mapped`. |
| D | ✅ fixed | Ingest `except` unconditionally set `SCRAPING_FAILED`, including on the re-scrape path where the collection may be `PROD_PERFECT`. | `tasks.py` `_mark_scrape_failed` | Only rewrites `workflow_status` when it is in `SCRAPE_FLOW_STATUSES`; otherwise leaves it, resets `reindexing_status` → *Not Needed* (stops the 5-min re-enqueue loop) and posts a Slack alert. Tests: `test_rescrape_ingest_failure_leaves_workflow_status_alone`, `test_rescrape_dispatch_failure_leaves_prod_status_alone`. |
| E | ✅ fixed | Blank `CRAWLER_INSTANCE_ID` → `InstanceIds=[""]` → every *Ready for Engineering* transition on an unwired host failed + @-mention. | `scraping/ssm_dispatch.py` | Settings guard for `CRAWLER_INSTANCE_ID` / `CRAWLER_INBOX_PATH`, mirroring `indexing/dispatch.py`. Test: `test_unconfigured_crawler_refuses_to_dispatch`. |
| F | ❌ open | Whole crawl JSON (`full_text` for up to 100k pages) loaded with one `json.loads`; list held through batching. Worker OOM risk on large collections. | `scraping/s3_results.py` `fetch_documents`; `tasks.py` ingest | Needs a crawler-side JSONL contract or `ijson` (not in requirements). Not changed; size ceiling is `MAX_PAGES_CAP` = 100k. |
| G | ✅ partial | `BaseUrl.url` is `unique=True` **globally**. A duplicate URL in one crawl output — or a URL already in another collection's `DumpUrl` rows — raised `IntegrityError` → whole ingest failed. | `models/delta_url.py:72`; `tasks.py` `_dedupe_by_url` | In-crawl duplicates/blank URLs are now dropped (first wins, logged). **Cross-collection** duplicates still fail — skip-vs-fail is a design decision, see §10. Test: `test_duplicate_urls_in_crawl_output_are_dropped`. |

### Medium

| # | Status | Finding | Where | Resolution |
|---|---|---|---|---|
| H | ✅ fixed | Prod mirror map only had `QC_MINOR`; anything else silently became `PROD_PERFECT`. | `tasks.py` `PROD_STATUS_FOR_QC_STATUS` | Explicit two-key map; a prod run entered from a non-QC status holds at `PRODUCTION_INDEXING`, resolves the dispatch, and Slacks "set by hand". Test: `test_prod_success_from_non_qc_status_holds_for_manual_resolution`. |
| I | ✅ fixed | `print()` instead of `logging`; persistent S3 errors were invisible. | `tasks.py`, `utils/slack_utils.py` | Module loggers; `logger.exception` on failure paths so tracebacks are kept. |
| J | ⏸ by design | Beat `enabled` re-asserted on every `post_migrate`: flag flips need `migrate`, admin toggles are reverted on deploy. | `sde_collections/signals.py`; same in `inference/signals.py` | Kept (flag is the source of truth). Now in `RELEASE_NOTES.md` and pinned by `test_signals.py::test_flag_is_reasserted_on_every_migrate`. |
| K | ✅ fixed | `assignPublicIp: ENABLED` hardcoded; SGs only read inside the subnets guard. | `indexing/dispatch.py`; `config/settings/base.py` | New `INDEXING_ASSIGN_PUBLIC_IP` (default `True`; in `.env_sample`). Subnets/SGs read independently; one-without-the-other raises `ValueError`. 3 new tests. |
| L | ❌ open | `results_ready` compares S3 `LastModified` to the Django host clock — skew makes a fresh summary look stale forever. | `scraping/s3_results.py` `results_ready` | A tolerance window would let a quick re-dispatch accept the previous run's summary. Proper fix: snapshot the prior summary's `LastModified` on `ScrapeDispatch` at dispatch time (needs a migration). Decide in review. |
| M | ✅ test / ⏸ docs | Real account ID in a test; instance IDs, IPs, ARNs throughout the planning docs. | `tests/test_indexing_dispatch.py` | Test uses `123456789012`. Planning docs left in place (owner will remove). |
| N | ✅ hook / ⏸ rotate | Prod DB password + RDS host in git history (`SQLDumpRestoration.md` on `dev`); gitleaks hook pointed at a missing config. | `.pre-commit-config.yaml`; `gitleaks-config.toml` | `gitleaks-config.toml` created (extends default rules); `pre-commit run gitleaks --all-files` passes. **Credential rotation still required** — out of band. |

### Cleanup / leftovers

| Status | Item |
|---|---|
| ✅ | `collection_detail.html` "View on prod / secret prod" buttons (deleted properties) removed; `utils/generate_deployment_message.py` (unused) trimmed for the same reason. |
| ✅ | `IndexDispatch.TARGET_TEST` / `TARGET_PROD` constants replace bare `"test"`/`"prod"` in `tasks.py`. |
| ✅ | `threshold` behaviour change and orphaned statuses 8/10/17/20 documented in `RELEASE_NOTES.md` ("Unreleased") + `CHANGELOG.md`. |
| ❌ skipped | Cosmetic Sinequa `help_text` strings (`delta_url.py`, `candidate_url.py`, `pattern.py`, `delta_patterns.py`) and `ConnectorChoices.ONLY_IN_SINEQUA_CONFIGS` — Django tracks `help_text`, so editing them generates a migration; not worth the noise on this branch. Legacy `scripts/` and `jupyter_notebooks/` import nothing deleted. |
| ❌ later | Indexes on `IndexDispatch.run_id` / `ScrapeDispatch.collection` — needs a migration; fine at current scale. |
| ➖ non-issue | 5-min `poll_scrape_jobs` vs 10-min ingest `soft_time_limit`: the CAS claim runs *before* `fetch_documents`, so a second invocation exits without downloading. Earlier note was overstated. |

### Tests
- Branch added: `test_scrape_dispatch.py`, `test_scrape_ingest.py`, `test_indexing_dispatch.py`,
  `test_inference_flag.py`, `test_aws_utils.py`. Removed: `test_sinequa_api.py`, `test_import_fulltexts.py`,
  `sde_collections/tests.py`, `config_generation/tests/*`.
- Real fixes riding along: `environmental_justice/tests/conftest.py` no longer leaks `ROOT_URLCONF` into later
  modules; `test_promote_collection.py` patterns changed from `.*docs.*` to `*docs*` (the old regex idiom matched
  nothing); `test_migrate_dump.py` imports the real `DELTA_COMPARISON_FIELDS`.
- Review fixes added: `test_signals.py` (6), `test_management_commands.py` (6), plus on_commit ordering,
  Slack-content, re-scrape failure, URL de-dup, unmapped prod mirror, SSM guard and network-config tests in the
  existing suites. Trigger tests now use `captureOnCommitCallbacks(execute=True)`.
- Gaps closed: `signals.py`, both management commands, Slack message content, on_commit ordering. Still untested:
  F (memory) and L (clock skew) by nature.
- Run: `docker-compose -f local.yml run --rm django bash ./init.sh` then `… coverage report`
  (`init.sh` runs each `test_*.py` as its own process). Last run 2026-08-25: all files pass;
  `makemigrations --check` clean.

---

## 5. Code review checklist — indexer (`sde-api-scrapers`)

| # | Finding | Where | Action |
|---|---|---|---|
| R0 | Local `web-indexing` is behind `develop`; a PR from it reverts PR #49/#50 (RDR prod freeze + sandbox guard). | `scrapers/rdr_scraper.py`, `infrastructure/config/settings.py`, `infrastructure/scheduling/scheduling_stack.py:112` | Rebase onto `origin/develop` or delete the branch. |
| R1 | **Split-brain endpoints.** `WebPipeline._resolve_endpoint` tier-caps `self.endpoint` for `ensure_index`/`probe_scope`/collision check/state scan/validate, but `APIOpenSearchUploader` never receives it — six bare `get_opensearch_client()` calls fall back to env `OPENSEARCH_ENDPOINT`. Masked in dev/test (same collection); on prod `--target test` guards TEST and writes PROD. Uploader is a `MagicMock` in `test_web_pipeline.py`, so untested. | `web/web_pipeline.py:110-116`; `uploader/api_opensearch_upload.py:92,187,245,364,454,521` | Thread `endpoint` into the uploader constructor. **Block prod deploy on this.** |
| R2 | `export_incomplete` / skipped deletions set `out["error"]` but `state` is still overwritten to `"succeeded"`; COSMOS branches on `state` only → truncated export indexes partially and reports success. | `web/web_pipeline.py:155,226-228` | Decide: `failed`, or a distinct `succeeded_with_warnings` COSMOS handles explicitly. |
| R3 | Deletion thresholds (`0.90`, `0.25`, `5000`) have silent in-code defaults; only the deployed task def injects them. | `web/deletion_guard.py:28-48` | Acceptable with the drift test; note for local runs. |
| R4 | Hardcoded account `998871305517`, role ARN, three AOSS hostnames; `deploy.yml:163` verify step bakes the account into the S3 name. TEST/PROD COSMOS account IDs commented out (silently no grant, not a synth error). | `infrastructure/config/settings.py:241-243,290-292,310` | Fine for dev; must be resolved for test/prod (NS.5). |
| R5 | Operator-facing error strings tell you to read `FINDING_id_scheme_collision.md §9` — deleted in `8c34fea`. Nine dangling doc refs total. | `web/id_collision.py:15,42,146,172`; `web/scope.py:18`; `web/validate.py:2`; `README.md:99` | Restore §9 or rewrite the strings. |
| R6 | 369 unit tests pass; **zero E2E** (E2E.2–E2E.10 unchecked). `test_infra_web_env.py:374` is misnamed (asserts endpoint divergence, not bucket passthrough). | tracker `:446-459` | C.4 below is the E2E. |
| R8 | 12 id-collision collections (`gcn_circulars`, `CODE_NASA_API`, …) excluded by verbal agreement only; nothing enforces it on either side beyond the runtime refusal. The 0.90 ratio guard does not back up the scope filter; `WEB_DELETION_ABORT_MAX` is the real protection. `AWSV4SignerAuth` rotation fix unverified on a >6 h run. | tracker `:460-477` | Consider a COSMOS-side denylist or an `ScraperConfigOverride` flag. |
| R9 | `documents.jsonl` read 2× per run (3× with `--reconcile`); ids and titles held in memory — the reason for 8 GB. | `web/web_pipeline.py:204-206,267,284` | Note; not a blocker. |
| R10 | Three dependency sources (`requirements.txt`, `pyproject.toml`+`uv.lock`, `infrastructure/requirements.txt`); `requests-aws4auth` still pinned though unused. | | Cleanup. |
| — | `infrastructure/DEPLOYMENT.md` predates the branch; its `run-task` example has no command override and will fail for `WEB_COSMOS`. `API_SCRAPERS_ARCHITECTURE_REVIEW.md` is stale (3 sources, `us-west-1`). | | Update or mark stale. |

Deploy path: `.github/workflows/deploy.yml` on push to `develop`/`test`/`main` → `pytest tests/` → ECR
`:sha`+`:latest` → `cdk deploy --all` → verify. OIDC trust is branch-pinned, so `workflow_dispatch` from a feature
branch fails at credential setup; rollback is `git revert -m 1 <merge>` + push.

---

## 6. Pre-merge fix list

**COSMOS (before PR `cosmos-rewiring → dev`)** — applied 2026-08-25 in the working tree (uncommitted); full suite green via `init.sh`
- [x] A — `_enqueue_on_commit` wraps the four `.delay()` calls (`collection.py`)
- [x] B + C — `notify_status_change` posts for `.update()`-set statuses; `PRODUCTION_INDEXING → PROD_*` pairs added
- [x] D — `_mark_scrape_failed` leaves the live `workflow_status` alone on the re-scrape path (clears the reindexing request + Slack alert so the poller doesn't loop)
- [x] E — settings guard in `send_job_to_crawler`
- [x] Template leftovers removed from `collection_detail.html` (and `generate_deployment_message.py`)
- [x] Placeholder account ID in `test_indexing_dispatch.py`
- [x] `gitleaks-config.toml` created (extends defaults) — `pre-commit run gitleaks --all-files` passes
- [ ] Commit `.pre-commit-config.yaml` (with the rest of these changes)
- [ ] Decide whether `INDEXING_HANDOFF_TODO.md`, `IMPLEMENTATION_PLAN.md`, `LOCAL_VERIFICATION_GUIDE.md` (instance IDs, IPs, ARNs) belong in a public repo, or move to the wiki
- [x] Release notes (`RELEASE_NOTES.md` "Unreleased") + `CHANGELOG.md` entry
- [x] G (in-crawl URL de-dup), H (explicit `PROD_STATUS_FOR_QC_STATUS`; unknown entry status holds at `PRODUCTION_INDEXING` + Slack), I (`logging` in `tasks.py`/`slack_utils.py`), tests for `signals.py` and both mgmt commands
- [x] K — `INDEXING_ASSIGN_PUBLIC_IP` setting; subnets/SGs validated together (`indexing/dispatch.py`, `base.py`, `.env_sample`)
- [x] `IndexDispatch.TARGET_TEST/TARGET_PROD` constants used in `tasks.py`
- [ ] F (streaming ingest) — not done; needs a crawler-side JSONL contract or `ijson`
- [ ] L (clock skew in `results_ready`) — not done; see §4 for the migration-based fix
- [ ] G, cross-collection duplicate URLs — design decision (skip vs fail), see §10
- [ ] Indexes on `IndexDispatch.run_id` / `ScrapeDispatch.collection` — later, needs a migration
- Out of band: **rotate the prod DB credential**

**Indexer**
- [ ] R0 — rebase/delete local `web-indexing`
- [ ] Commit `COSMOS_INDEX_REAL_RUN.md` and the tracker update
- [ ] R1 — endpoint into `APIOpenSearchUploader` (before any test/prod tier deploy)
- [ ] R2 — settle `export_incomplete` semantics with COSMOS
- [ ] R5 — restore/rewrite the collision remediation text

---

## 7. Deployment runbook (dev, staging host only)

**Standing rule:** all COSMOS work runs on **staging `i-08f9b2175b70fa05c`** (`ssh staging_cosmos`,
`ec2-user@18.215.146.207`, key `~/.ssh/sde-indexing-helper-staging.pem`). Never the production box
`i-02b3d3e1ac0671952`. `i-0178c998e868792d7` (`COSMOS_Staging_Refresh`) has no instance profile and cannot
dispatch. The COSMOS boxes are not SSM-registered — use SSH. Note `indexing-helper-role` is shared by staging and
production, so the C.1 `sts:AssumeRole` grant already exists on production's role too.

### Prerequisites — all in place (account `998871305517`, `us-east-1`, profile `sde-dev`)

| Resource | Value | Status |
|---|---|---|
| Indexing bucket | `sde-cosmos-indexing-dev` | ✅ NS.2 |
| Dispatch role | `arn:aws:iam::998871305517:role/CosmosIndexingDispatchRole-dev` | ✅ NS.2 |
| COSMOS role grant | inline `CosmosIndexingDispatch-dev` on `indexing-helper-role` | ✅ C.1 / NS.6 done 2026-08-20 (the scrapers tracker row is stale) |
| ECS | cluster `api-scrapers-cluster-dev`, family `web_cosmos-scraper-dev:1`, container `WEB_COSMOSContainer` | ✅ |
| ECR | `…/api-scrapers-dev:latest` = `c2aebad` | ✅ |
| Network | VPC `vpc-0265394c8c285afba`, SG `sg-01817cfe4f3629986`, 6 public subnets (below) | ✅ NS.3 values known |
| Index | `sde-web-subset` (59 docs; mapping verified) | ✅ OOB.3 |
| Crawler | `i-0b6a61d95888886f4`, bucket `sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy`, inbox `/opt/sde-crawler/jobs/incoming` | ✅ |

### C.2 — wire the staging host

1. `ssh staging_cosmos`, `cd` to the checkout, `git fetch && git checkout cosmos-rewiring` (or the merged `dev`).
2. Append to `.envs/.production/.django` (from `INDEXING_HANDOFF_TODO.md:293-299`):
   ```
   AWS_REGION=us-east-1
   SDE_S3_BUCKET=sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy
   CRAWLER_INSTANCE_ID=i-0b6a61d95888886f4
   CRAWLER_INBOX_PATH=/opt/sde-crawler/jobs/incoming
   SCRAPE_POLL_ENABLED=true
   INFERENCE_ENABLED=False

   SDE_INDEX_BUCKET=sde-cosmos-indexing-dev
   INDEXING_ECS_CLUSTER=api-scrapers-cluster-dev
   INDEXING_TASK_FAMILY=web_cosmos-scraper-dev
   INDEXING_CONTAINER_NAME=WEB_COSMOSContainer
   INDEXING_DISPATCH_ROLE_ARN=arn:aws:iam::998871305517:role/CosmosIndexingDispatchRole-dev
   INDEXING_SUBNETS=subnet-0268b60265d9d6e87,subnet-0c29076fe7de10791,subnet-030a3a47fa10c76b2,subnet-0a6c6c437ed87dda3,subnet-09355979ab5496a50,subnet-0f3a7b40152e63be3
   INDEXING_SECURITY_GROUPS=sg-01817cfe4f3629986
   INDEX_POLL_ENABLED=true
   ```
   Leave `SDE_AWS_*` blank so the instance role is used. Keep `SCRAPE_POLL_ENABLED=false` if you only want to
   exercise the indexing loop first.
3. Build + migrate + recreate — **order matters; `migrate` is required** (beat rows come from `post_migrate`,
   and the production start script does not migrate):
   ```
   docker compose -f production.yml build django
   docker compose -f production.yml run --rm django python manage.py migrate --noinput
   docker compose -f production.yml up -d --force-recreate django celeryworker celerybeat
   ```
4. Verify:
   ```
   docker compose -f production.yml run --rm django python manage.py shell -c \
     "from django.conf import settings as s; print(s.INDEXING_DISPATCH_ROLE_ARN, s.INDEXING_SUBNETS, s.INDEX_POLL_ENABLED)"
   docker compose -f production.yml run --rm django python manage.py shell -c \
     "from django_celery_beat.models import PeriodicTask; print(list(PeriodicTask.objects.filter(task__startswith='sde_collections.tasks.poll').values_list('name','enabled')))"
   docker compose -f production.yml exec celeryworker celery -A config.celery_app inspect ping
   ```
   Expect `Poll index runs (every 2 min)` / `Poll crawler S3 results (every 5 min)` with the expected `enabled`.
   Confirm migrations `0078`, `0079`, `0080` applied (`showmigrations sde_collections | tail`).

### C.3 — pre-flight from the staging host
```
aws s3 cp /etc/hostname s3://sde-cosmos-indexing-dev/curated_collections/_preflight/x/probe.txt
aws s3 cp s3://sde-cosmos-indexing-dev/curated_collections/_preflight/x/probe.txt -
aws s3api list-objects-v2 --bucket sde-cosmos-indexing-dev --prefix index_runs/   # AccessDenied is acceptable
aws sts assume-role --role-arn arn:aws:iam::998871305517:role/CosmosIndexingDispatchRole-dev --role-session-name preflight
```
Then from a Django shell, on a **scratch** collection (e.g. `config_folder='verify_web'`):
`from sde_collections.indexing.dispatch import run_index_task; run_index_task(c, 'test', 'preflight-1')`
→ expect a `taskArn`; `aws ecs list-tasks --cluster api-scrapers-cluster-dev --family web_cosmos-scraper-dev`.
The task will fail on a missing export — that is the wiring proof.

### C.4 — closed loop (the indexer's E2E.10)
Pick a small collection **not** in the id-collision set (avoid `gcn_circulars`, `CODE_NASA_API`); the two already
in `sde-web-subset` are `astromaterials_data_system` and `aurorasaurus_reporting_auroras_from_the_ground_up`.
1. Admin → set `workflow_status = Curated`. Confirm: `IndexDispatch` row; objects under
   `s3://sde-cosmos-indexing-dev/curated_collections/{cf}/{run_id}/` with `manifest.json` last; ECS task running;
   status `TEST_INDEXING`. Watch `/ecs/api-scrapers-dev` in CloudWatch.
2. Wait for `index_runs/{cf}/{run_id}/status.json` (≤ a few minutes). Poller posts `validation.json` to
   `#sde-data-curation`; collection **stays** `TEST_INDEXING`.
3. Set `QC Perfect` → prod dispatch (`--target prod`, same collection in dev) → `PRODUCTION_INDEXING` → `PROD_PERFECT`.
4. Failure path: re-curate, delete `manifest.json` before the task reads it (or dispatch against an empty
   export) → `INDEXING_FAILED_ON_TEST`, Slack alert.
5. Optional scrape leg: `SCRAPE_POLL_ENABLED=true` + migrate, set a collection to *Ready for Engineering*,
   confirm the job JSON lands in the crawler inbox via SSM and the ingest reaches *Ready for Curation*.
6. Tick E2E.2–E2E.10 in the scrapers tracker and "Closed loop verified" / NS.3 in `IMPLEMENTATION_PLAN.md`.

### Rollback
- Code: `git checkout <previous sha>` and repeat step 3. Migrations 0078–0080 are additive — leave them applied.
- Disable the pipeline without rolling back: set `INDEX_POLL_ENABLED=false` / `SCRAPE_POLL_ENABLED=false`,
  run `migrate` (not just restart — see J), recreate `celerybeat`. Or blank `INDEXING_DISPATCH_ROLE_ARN` to make
  dispatch raise on the settings guard.
- Indexer: `git revert -m 1 <merge>` on `develop` and push; CD redeploys.

---

## 8. Cutover and later
- **OOB.1** — add `version: keyword` to live `sde-web` mapping *before* the first write (dynamic mapping would
  create it as `text` and the differ never works). Backfilling `version` arms the 431k blast radius — do it with
  the deletion guards understood.
- Flip `WEB_INDEX_NAME` `sde-web-subset → sde-web` in `infrastructure/config/settings.py` + task def. No COSMOS change.
- R1 must be fixed before any test/prod tier deploy of the indexer.
- NS.5 — test/prod COSMOS account IDs (`COSMOS_AWS_ACCOUNT_ID[TEST|PROD]`) so the dispatch role + bucket policy
  synth for those tiers.
- COSMOS Phase 9 CI/CD (0/8): `validate_deploy_env`/`preflight_aws` commands, `scripts/deploy.sh`, staging/prod
  workflows gated on `CD_ENABLED`, `/healthz`, rollback rehearsal. Explicitly not a gate for the loop.
- COSMOS never calls `ecs:DescribeTasks`; a task that dies before writing `status.json` is invisible for
  `INDEX_STALL_TIMEOUT_HOURS` (6 h). Consider a `DescribeTasks` check in `poll_index_runs` later.

---

## 9. Doc discrepancies to fix
1. `INDEXING_HANDOFF_TODO.md` / `IMPLEMENTATION_PLAN.md` cite HEAD `9e18ced8` and "uncommitted" state; actual HEAD is `c1505d36`, tree clean.
2. `INDEXING_HANDOFF_TODO.md` says P7 "10 of 14" in one place and "11 of 14" in another.
3. `IMPLEMENTATION_PLAN.md` NS.1 prose and the scrapers tracker still call `i-02b3d3e1ac0671952` (production) "the COSMOS host"; the loop runs on staging.
4. Scrapers `COSMOS_INDEX_REAL_RUN.md` §0 lists NS.3/NS.6 open and COSMOS env "all blank" — NS.6 done 2026-08-20; its worked example uses `nasa_applied_sciences`, which is not in `sde-web-subset`.
5. Deletion guard threshold: `> 0.90` (handoff, tracker, E2E.7a) vs `≥ 0.90` (`COSMOS_INDEX_REAL_RUN.md` §4). Code is `>`.
6. `sde-web-copy` vs `sde-web-subset` — pre-2026-08-19 verifications were against `-copy`; `IMPLEMENTATION_PLAN.md` NS.8 still says so.
7. `sde_collections/DEPLOYMENT.md` says `validate_deploy_env` must refuse identical endpoints; `IMPLEMENTATION_PLAN.md` Phase 9 says tier separation is indexer-side only.
8. `DEPLOYMENT.md` puts the COSMOS ECR repo in "the SMCE account"; all indexing resources are in `998871305517`.
9. Scrapers `infrastructure/DEPLOYMENT.md` `run-task` example lacks the command override.
10. `WORKFLOW.md` omits statuses 22/26 and says the collection moves to QC after validation; the code holds at `TEST_INDEXING` and QC is curator-set.
11. Scrapers `DESIGN.md` (deleted) and `API_SCRAPERS_ARCHITECTURE_REVIEW.md` describe cross-account / 3-source / `us-west-1` — stale.

---

## 10. Open questions for the review
- Should the 12 id-collision collections be enforced in COSMOS code (denylist / override flag) rather than by agreement?
- `export_incomplete` → `succeeded` with `error` (R2): does COSMOS want to treat that as failure, or surface it as a distinct status?
- `tdamm_tag` is exported by COSMOS but dropped by the indexer — intentional for now, or should the mapping carry it?
- Static `SDE_AWS_*` keys vs instance role as the long-term model; env-file source of truth (hand-maintained per host vs SSM Parameter Store / Secrets Manager).
- Do the planning docs with instance IDs / IPs stay in the public repo?
- Fargate networking: dev runs `INDEXING_ASSIGN_PUBLIC_IP=True` on public subnets; is a private subnet + NAT (`False`) the target for prod?
- G, cross-collection duplicates: `BaseUrl.url` is globally unique, so a URL already in another collection's `DumpUrl` rows aborts an ingest. Skip the row (and log), or fail the collection so a curator notices the overlap?
- L: should `ScrapeDispatch` snapshot the previous summary's `LastModified` at dispatch time (migration) so completion detection stops depending on the Django host clock?
