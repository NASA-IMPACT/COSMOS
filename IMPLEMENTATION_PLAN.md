# COSMOS Rewiring — Implementation Plan & Progress Tracker

> **Status legend:** `[ ]` not started · `[~]` in progress · `[x]` done · `[D]` deferred by decision
>
> Update the checkboxes in this file as work lands. This document is the progress tracker.
>
> Companion documents: [`WORKFLOW.md`](./WORKFLOW.md) (what the pipeline does),
> [`sde_collections/DEPLOYMENT.md`](./sde_collections/DEPLOYMENT.md) (how it deploys),
> [`rewiring_decisions.md`](./rewiring_decisions.md) (why).

---

## Context

COSMOS today drives collection curation through **Sinequa**: workflow-status changes generate
Sinequa scraper/indexer XML configs, push them to a GitHub configs repo, and pull scraped full
text back out of the Sinequa API. Sinequa is being retired.

The replacement, specified in [`WORKFLOW.md`](./WORKFLOW.md), is:

```
COSMOS ──SSM job JSON──► crawl4ai scraper on EC2 ──► S3 ──► COSMOS DumpUrl
   └──► DeltaUrl ──curation──► CuratedUrl ──► OpenSearch (test) ──QC──► OpenSearch (prod)
```

`sde_collections/DEPLOYMENT.md` is the companion CI/CD spec. Both, plus
`rewiring_decisions.md` and `WORKFLOW_DIAGRAM.png`, are currently **untracked** files on branch
`cosmos-rewiring`, which has no commits of its own.

**Intended outcome:** COSMOS dispatches scrape jobs, ingests results from S3, drives curation to
`CuratedUrl`, and hands curated content to an indexing pipeline — with Sinequa removed, the
inference pipeline dormant, and a repeatable deploy path.

### Confirmed decisions

| Decision | Choice |
|---|---|
| Scope | Pipeline rewiring **+** the CI/CD machinery from `DEPLOYMENT.md` |
| Sinequa | **Delete outright** (unwire first, then remove the files) |
| Indexing pipeline (chunk → SageMaker → AOSS) | **Built as a `WEB_COSMOS` source inside `sde-api-scrapers`** (branch `web-indexing`) — supersedes the earlier "separate repo" call: the quantization math must stay byte-identical to what built the live index, so `uploader/` is reused, not forked. Event-triggered from COSMOS via cross-account `ecs:RunTask`. Its phases W0–W3 + W5 are **code-complete** (209 offline tests, `cdk synth` clean); this plan owns only the COSMOS side — its Phase 7 = that repo's **W4** |
| Validation per phase | pytest with mocked AWS; manual smoke tests against the real `sde-dev` account |

### Decisions added after plan review (2026-08-11) — confirm with team

| Decision | Choice |
|---|---|
| **Reindexing (re-scrape) flow** | `create_configs_on_status_change` has a second, `reindexing_status`-keyed block (`REINDEXING_FINISHED_ON_DEV → fetch_full_text`, `REINDEXING_CURATED → promote_to_curated`) that the original plan didn't account for — P6 deletes `fetch_full_text`, which would sever re-scrapes. **Rewire it onto the same dispatch/poll path**: dispatch on `REINDEXING_NEEDED_ON_DEV` (P3), poll it (P4), ingest flips to `REINDEXING_FINISHED_ON_DEV`, and the migrate task's existing `→ REINDEXING_READY_FOR_CURATION` transition takes over. Keep `REINDEXING_CURATED → promote_to_curated`. |
| **Dispatch record & result freshness** | S3 objects persist between runs, so on any re-dispatch the poller would instantly "complete" against the **previous run's** output, and the stall timeout has nothing to measure from. Add a small **`ScrapeDispatch`** model (P3): `collection` FK, `dispatched_at`, `ssm_command_id`. `results_ready()` requires the S3 summary's `LastModified > dispatched_at`; the stall timeout is measured from `dispatched_at`. |
| **Web indexing pipeline: `WEB_COSMOS` in `sde-api-scrapers`, event-triggered** *(updated 2026-08-13 from the built `web-indexing` branch — supersedes the earlier separate-repo / container-env / `describe_tasks` sketch)* | The pipeline is a **`WEB_COSMOS` source inside `sde-api-scrapers`** (ECS Fargate: chunk → SageMaker vectorize → AOSS bulk upsert, `uploader/` reused with parameterized `chunk_field`/filtered scans; `schedule=None` in every env — fired only by COSMOS, per collection, the moment curation completes via the P5 triggers: `CURATED` → test, `QC_PERFECT`/`QC_MINOR` → prod). The hand-off is **S3 both ways** through a dedicated bucket `sde-cosmos-indexing-{env}`: COSMOS exports `CuratedUrl`s as `documents.jsonl` + `manifest.json` (manifest written **last** = export complete) under `curated_collections/{config_folder}/{run_id}/`, then assumes `CosmosIndexingDispatchRole-{env}` and calls `ecs:RunTask` with a **command override** (`--source WEB_COSMOS --collection <config_folder> --target test\|prod --run-id <run_id>`). Completion is observed by **polling S3 `index_runs/{config_folder}/{run_id}/status.json`** (written by the indexer last and unconditionally, incl. on failure) — **not** `ecs.describe_tasks`; an **`IndexDispatch`** record (`collection`, `run_id`, `target`, `task_arn`, `dispatched_at`) provides the stall timeout, and the COSMOS-minted `run_id` namespaces every artifact, so no `LastModified` freshness rule is needed. No callback endpoint into COSMOS. |

### Hard constraints

- **Do not modify `DumpUrl`, `DeltaUrl`, or `CuratedUrl`** (`sde_collections/models/delta_url.py`),
  nor `migrate_dump_to_delta()` / `promote_to_curated()` in `collection.py`. The rewiring changes
  what *feeds* those models, never the models themselves.
- Every migration must stay additive and backward-safe so an image rollback is a complete rollback.

---

## Key reuse points (found during exploration — prefer these over new code)

| Seam | Location | Why it matters |
|---|---|---|
| `create_configs_on_status_change` | `sde_collections/models/collection.py:871` | The single `post_save` dispatcher for all status-triggered side effects. Four of its five branches are Sinequa. **This is the main rewiring surface.** |
| `fetch_full_text` | `sde_collections/tasks.py:159` | The only writer of `DumpUrl`. Its contract is just `{url, title, full_text}` → `DumpUrl(url=, scraped_title=, scraped_text=)`. Swap the source from Sinequa to S3 and everything downstream is unchanged. |
| `migrate_dump_to_delta_and_handle_status_transistions` | `sde_collections/tasks.py:200` | Already does delta migration + status transition. Its `pre_workflow_statuses` list is where new statuses slot in. |
| `queue_necessary_classifications` | `sde_collections/models/collection.py:692` | The inference on/off switch; its `else` branch already calls migration directly. |
| `inference/signals.py:5` | `post_migrate` → `PeriodicTask` | The exact pattern to copy for the new `poll_scrape_jobs` schedule. There is **no `CELERY_BEAT_SCHEDULE`** in this repo — all schedules are DB rows. |
| `send_detailed_import_notification` | `sde_collections/utils/slack_utils.py:62` | Already written, **never called**. A ready-made ingest-summary Slack hook. |
| `STATUS_CHANGE_NOTIFICATIONS` | `sde_collections/utils/slack_utils.py:12` | `(old, new)` → message map. Already covers `QC:Perfect→Prod:Perfect` and `QC:Minor→Prod:Minor`. |
| `s3_keys_for_collection` | `sde-crawl4ai-scraper-v1/sde_crawler/job.py:65` | Authoritative S3 key layout — mirror it, don't reinvent it. |
| `JOB_DEFAULTS` / `merge_job` | `sde-crawl4ai-scraper-v1/sde_crawler/job.py` | Job JSON contract. `None` values are skipped, so COSMOS should emit only non-null overrides. |

---

## Repo structure after this work

```
COSMOS/
├── WORKFLOW.md                       ← tracked (was untracked)
├── WORKFLOW_DIAGRAM.png              ← tracked
├── rewiring_decisions.md             ← tracked
├── ecr.override.yml                  ★ P9
├── scripts/deploy.sh                 ★ P9
├── .github/workflows/
│   ├── ci.yml                        ★ P9  (replaces run_full_test_suite.yml)
│   ├── deploy-staging.yml            ★ P9
│   ├── deploy-production.yml         ★ P9
│   ├── rollback.yml                  ★ P9
│   └── secret-scan-history.yml       ★ P9
├── sde_collections/
│   ├── DEPLOYMENT.md                 ← tracked
│   ├── apps.py                       ✎ add ready() → import signals
│   ├── signals.py                    ★ P4  post_migrate → poll_scrape_jobs PeriodicTask
│   ├── tasks.py                      ✎ scrape dispatch / poll / ingest; Sinequa tasks removed
│   ├── sinequa_api.py                ✖ DELETED (P6)
│   ├── models/
│   │   ├── collection.py             ✎ triggers rewired, Sinequa methods removed
│   │   ├── collection_choice_fields.py  ✎ statuses 21–26
│   │   ├── scraper_config.py         ★ P3  ScraperConfigOverride + ScrapeDispatch
│   │   ├── indexing.py               ★ P7  IndexDispatch
│   │   └── delta_url.py              ✔ UNCHANGED (hard constraint)
│   ├── scraping/                     ★ P3/P4  new subpackage
│   │   ├── job_builder.py            ★ build_job_json(collection) -> dict
│   │   ├── ssm_dispatch.py           ★ send_job_to_crawler(collection)
│   │   └── s3_results.py             ★ fetch summary + documents from S3
│   ├── indexing/                     ★ P7  new subpackage (mirrors sde-api-scrapers W4)
│   │   ├── export.py                 ★ export_curated_to_s3(collection, target, run_id)
│   │   └── dispatch.py               ★ run_index_task(collection, target, run_id)
│   ├── utils/
│   │   ├── aws.py                    ★ P0  get_boto3_session() — shared credential chain
│   │   ├── slack_utils.py            ✎ new transitions
│   │   ├── github_helper.py          ✖ DELETED (P6)
│   │   ├── bulk_github_push.py       ✖ DELETED (P6)
│   │   └── health_check.py           ✖ DELETED (P6)
│   └── management/commands/
│       ├── preflight_aws.py          ★ P9
│       ├── validate_deploy_env.py    ★ P9
│       ├── dispatch_scrape.py        ★ P3  manual re-dispatch
│       ├── ingest_scrape_results.py  ★ P4  manual ingest
│       ├── import_from_sinequa.py    ✖ DELETED (P6)
│       ├── push_to_github.py         ✖ DELETED (P6)
│       ├── sync_all_with_github.py   ✖ DELETED (P6)
│       ├── load_urls_from_api.py     ✖ DELETED (P6)
│       └── generate_configs.py       ✖ DELETED (P6 — already dead code)
├── config_generation/                ✖ DELETED ENTIRELY (P6)
├── default_scraper.xml               ✖ DELETED (P6)
├── inference/                        ✎ P2 gated off, NOT deleted
└── config/settings/base.py           ✎ new AWS / crawler / flag settings
```

`★` new · `✎` modified · `✖` deleted · `✔` explicitly untouched

---

## Phase 0 — Foundations: settings, AWS session helper, doc tracking

**Goal:** land the shared plumbing every later phase needs, with zero behavior change.

### Files

| File | Change |
|---|---|
| `config/settings/base.py` | Add the settings block below (near `SLACK_WEBHOOK_URL`, ~L346) |
| `sde_collections/utils/aws.py` | **New.** `get_boto3_session()` |
| `.env_sample`, `.envs/.local/.django` | Document the new vars |
| `requirements/base.txt` | No change yet (boto3 already pinned at `1.34.31`) |
| `git add` the four untracked docs | Bring `WORKFLOW.md`, `WORKFLOW_DIAGRAM.png`, `rewiring_decisions.md`, `sde_collections/DEPLOYMENT.md` under version control |

### New settings

```python
# --- SDE curation pipeline ---
AWS_REGION            = env("AWS_REGION", default="us-east-1")
SDE_S3_BUCKET         = env("SDE_S3_BUCKET", default="")          # crawler output bucket
CRAWLER_INSTANCE_ID   = env("CRAWLER_INSTANCE_ID", default="")    # i-0b6a61d95888886f4 on dev
CRAWLER_INBOX_PATH    = env("CRAWLER_INBOX_PATH", default="/opt/sde-crawler/jobs/incoming")
SCRAPE_POLL_ENABLED   = env.bool("SCRAPE_POLL_ENABLED", default=False)
INFERENCE_ENABLED     = env.bool("INFERENCE_ENABLED", default=False)
# pipeline-scoped credentials for local dev ONLY; blank in AWS (instance role takes over)
SDE_AWS_ACCESS_KEY_ID     = env("SDE_AWS_ACCESS_KEY_ID", default="")
SDE_AWS_SECRET_ACCESS_KEY = env("SDE_AWS_SECRET_ACCESS_KEY", default="")
# COSMOS never talks to OpenSearch or SageMaker: chunk/vectorize/index AND the QC validation
# report are produced by the WEB_COSMOS task in sde-api-scrapers (branch web-indexing), which
# holds the AOSS credentials. The P7 dispatch/poll settings — SDE_INDEX_BUCKET (distinct from
# SDE_S3_BUCKET), INDEXING_ECS_CLUSTER, INDEXING_TASK_FAMILY, INDEXING_DISPATCH_ROLE_ARN,
# INDEX_POLL_ENABLED — land with P7, all with defaults so config.settings.test keeps booting.
```

> **Naming note:** existing settings use the `DJANGO_AWS_*` prefix for the *static assets*
> bucket/credentials. `SDE_S3_BUCKET` and `SDE_AWS_*` are deliberately distinct names — do not
> merge the two. In particular the helper below must **not** read `settings.AWS_ACCESS_KEY_ID`:
> that is the django-storages static-assets credential, it is defined only in `local.py:63` and
> `production.py:48` (not `base.py`), so referencing it under `test.py` raises `AttributeError` —
> and it is the wrong credential scope anyway.

### `sde_collections/utils/aws.py`

Existing COSMOS AWS code passes **static access keys** (`tasks.py:143`, `health_check.py:199`),
but `DEPLOYMENT.md` assumes the deployed host's **instance role**. Reconcile with one helper:

```python
def get_boto3_session():
    """Default credential chain (instance role in AWS); explicit SDE keys only if set (local dev)."""
    if settings.SDE_AWS_ACCESS_KEY_ID and settings.SDE_AWS_SECRET_ACCESS_KEY:
        return boto3.Session(
            aws_access_key_id=settings.SDE_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SDE_AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    return boto3.Session(region_name=settings.AWS_REGION)
```

All new SSM/S3/AOSS/SageMaker code uses this. Do not add new static-key call sites.

### Validation

```bash
docker-compose -f local.yml build
docker-compose -f local.yml up -d
docker-compose -f local.yml run --rm django python manage.py check
docker-compose -f local.yml run --rm django pytest        # full suite must still pass
```

New test `sde_collections/tests/test_aws_utils.py`: asserts the session falls back to the default
chain when the `SDE_AWS_*` keys are blank (their `base.py` default, so no `override_settings`
gymnastics needed), and uses explicit keys when set (mock `boto3.Session`).

### Done when
- [x] Settings added; `manage.py check` clean with all new vars unset (defaults hold)
- [x] `get_boto3_session()` exists with tests
- [x] Four rewiring docs committed
- [x] Full existing test suite green

---

## Phase 1 — Workflow statuses 21–26, UI colour maps, Slack transitions

**Goal:** make the new statuses selectable and renderable everywhere. **No triggers yet.**

### Files

| File | Change |
|---|---|
| `sde_collections/models/collection_choice_fields.py:80` | Add the six members below to `WorkflowStatusChoices` |
| `sde_collections/models/collection.py:333` | Add keys `24, 25, 26` to `Collection.workflow_status_button_color` |
| `sde_collections/models/collection.py:797` | Add keys `24, 25, 26` to `WorkflowHistory.workflow_status_button_color` |
| `sde_indexing_helper/static/js/collection_list.js:317` | Extend `color_choices` — it currently covers **only 1–16** |
| `sde_collections/utils/slack_utils.py:12` | Add the new transitions |
| `sde_collections/models/README_STATUS_TRIGGERS.md` | Document the new statuses |
| new migration `0078_*` | Choices-only `AlterField` (additive, reversible) |

```python
SCRAPING_SUCCESSFUL     = 21, "Scraping Successful"
TEST_INDEXING           = 22, "Test Indexing"
SCRAPING_FAILED         = 23, "Scraping Failed"
INDEXING_FAILED_ON_TEST = 24, "Indexing Failed on Test"
INDEXING_FAILED_ON_PROD = 25, "Indexing Failed on Prod"
PRODUCTION_INDEXING     = 26, "Production Indexing"
```

> **Latent bug this phase must fix:** both Python colour maps do a bare
> `color_choices[self.workflow_status]` — an unmapped status raises `KeyError` and breaks the
> collection list *and* detail pages. Keys 21–23 already exist; 24–26 do not. Change the lookups to
> `color_choices.get(self.workflow_status, "btn-light")` so this class of failure cannot recur.
> The JS map is worse: statuses 17–20 already render colourless today. Fill 17–26 in the same pass.
>
> While in there: key `23` (Scraping Failed) is pre-provisioned as `btn-light` in both Python maps
> (`collection.py:357,821`) — change it to `btn-danger`, and use `btn-danger` for 24/25 too.
> Failure statuses must not render as neutral.

New Slack transitions to add:

| Transition | Message |
|---|---|
| `READY_FOR_ENGINEERING → SCRAPING_SUCCESSFUL` | scrape finished, counts included |
| `READY_FOR_ENGINEERING → SCRAPING_FAILED` | alert, mention devs |
| `CURATED → INDEXING_FAILED_ON_TEST` | alert |
| `* → INDEXING_FAILED_ON_PROD` | alert, mention devs |

### Validation

```bash
docker-compose -f local.yml run --rm django python manage.py makemigrations
docker-compose -f local.yml run --rm django python manage.py migrate
docker-compose -f local.yml run --rm django pytest sde_collections/tests/
```

New tests in `sde_collections/tests/test_workflow_status_triggers.py`:
- Every `WorkflowStatusChoices` member resolves a colour on `Collection` **and** `WorkflowHistory`
  (parametrised — this is the regression guard for the `KeyError`).
- Setting each new status writes a `WorkflowHistory` row.

### Manual verification
1. `docker-compose -f local.yml up`, open `http://localhost:8001/`.
2. The per-row workflow dropdown lists all 26 statuses; the filter panel shows them.
3. Select **Scraping Successful** on a collection — the button re-colours, no console error,
   and the detail page **Workflow History** tab shows the transition.

### Done when
- [x] Six statuses added, migration applied
- [x] Both Python colour maps use `.get(...)` with a default; JS map covers 1–26
- [x] Slack map has the four new transitions
- [x] Parametrised colour test passes for every enum member
- [x] Dropdowns/filters render all statuses with no JS console errors

---

## Phase 2 — Disable the inference pipeline (do not delete)

**Goal:** `rewiring_decisions.md` item 1 — path of least resistance, keep the functionality.

### The trap

`queue_necessary_classifications()` (`collection.py:692`) routes **three hard-coded collections**
(`imagine_the_universe`, `physics_of_the_cosmos`, `stsci_space_telescope_science_institute`)
through `InferenceJob`; only the `else` branch calls the migration task directly. Disabling only
the beat schedule would leave those three collections with a queued job that never runs, so they
**never reach `Ready for Curation`**. The flag must short-circuit the branch itself.

### Files

| File | Change |
|---|---|
| `sde_collections/models/collection.py:692` | Early return in `queue_necessary_classifications()` when `not settings.INFERENCE_ENABLED` → call `migrate_dump_to_delta_and_handle_status_transistions.delay(self.id)` and return |
| `inference/signals.py:33,49` | Pass `enabled=settings.INFERENCE_ENABLED` on `PeriodicTask.objects.create(...)`, and set `.enabled` in both update branches |
| `inference/tasks.py:8` | Belt-and-braces early return when the flag is off |

> `inference/signals.py` currently re-asserts `crontab` and `task` on **every** `post_migrate`, so
> disabling the rows by hand in the admin does not survive a deploy. Setting `enabled` in the
> signal is what makes the disable durable — exactly the failure mode `DEPLOYMENT.md` warns about.

Leave `inference` in `INSTALLED_APPS`, leave models and migrations alone —
`candidate_url.py:70` (`inferenced_by`), the paired ML/manual fields, and
`test_import_fulltexts.py` all still import from it.

### Validation

```bash
docker-compose -f local.yml run --rm django pytest inference/ sde_collections/tests/
docker-compose -f local.yml run --rm django python manage.py migrate   # re-run: rows stay disabled
docker-compose -f local.yml logs -f celerybeat                          # no inference queue ticks
```

New tests:
- With `INFERENCE_ENABLED=False`, a collection whose `config_folder` is in the TDAMM list still
  calls the migration task and creates **no** `InferenceJob`. *(This is the regression guard.)*
- With the flag on, the TDAMM path still creates an `InferenceJob`.
- After `post_migrate`, both `PeriodicTask` rows have `enabled == INFERENCE_ENABLED`.

> **Test fidelity:** the existing suite patches `queue_necessary_classifications` wholesale
> (`test_workflow_status_triggers.py:428`). The two flag tests above must call the **real** method
> under `override_settings(INFERENCE_ENABLED=...)` (patching only `migrate_dump_to_delta_…​.delay`),
> or they guard nothing.

### Manual verification
`shell_plus` → `PeriodicTask.objects.filter(task__startswith="inference").values("name","enabled")`
→ both `False`. Confirm `celerybeat` logs show no inference ticks over ~10 min.

### Done when
- [x] Flag added and honoured at all three sites
- [x] TDAMM collections still migrate to `Ready for Curation` with inference off
- [x] `PeriodicTask.enabled` survives a re-run of `migrate`

---

## Phase 3 — Scrape dispatch: overrides model + job JSON + SSM

**Goal:** `Ready for Engineering` writes a job JSON into the crawler's inbox via SSM.
(WORKFLOW.md steps 5–7.)

### `collection_id` decision

The scraper derives `collection_id` from the seed host when absent, and uses it for both the output
filename and the S3 key. COSMOS will **always send `config_folder`** as `collection_id`:
it is unique, `editable=False`, already the AOSS `collection_key`, and stable across renames.
Do not use the numeric PK.

### Files

| File | Change |
|---|---|
| `sde_collections/models/scraper_config.py` | **New.** `ScraperConfigOverride` **and `ScrapeDispatch`** (below) |
| `sde_collections/models/__init__.py` | Export both |
| `sde_collections/admin.py` | Register both (WORKFLOW.md step 6: curators edit overrides in the admin console; `ScrapeDispatch` read-only for debugging) |
| `sde_collections/scraping/job_builder.py` | **New.** `build_job_json(collection) -> dict` |
| `sde_collections/scraping/ssm_dispatch.py` | **New.** `send_job_to_crawler(collection) -> str` (SSM command id) |
| `sde_collections/tasks.py` | **New task** `dispatch_scrape_job(collection_id)` — records a `ScrapeDispatch` row on send |
| `sde_collections/models/collection.py:887` | `READY_FOR_ENGINEERING` branch: replace `create_scraper_config`/`create_scraper_job` with `dispatch_scrape_job.delay(instance.id)`. **Also** add `REINDEXING_NEEDED_ON_DEV → dispatch_scrape_job.delay(instance.id)` in the `reindexing_status` block (per the reindexing decision above — this replaces the engineer manually re-running a Sinequa job) |
| `sde_collections/management/commands/dispatch_scrape.py` | **New.** Manual re-dispatch |
| new migration `0079_*` | Creates `ScraperConfigOverride` + `ScrapeDispatch` (additive) |

```python
class ScraperConfigOverride(models.Model):
    """Per-collection overrides merged onto the crawler's own defaults.
    All fields nullable: only non-null values are emitted into the job JSON,
    because crawl4ai's merge_job() skips None."""
    collection           = models.OneToOneField(Collection, on_delete=models.CASCADE,
                                                related_name="scraper_config")
    max_pages            = models.PositiveIntegerField(null=True, blank=True)   # cap 100_000
    depth_limit          = models.PositiveIntegerField(null=True, blank=True)
    delay                = models.FloatField(null=True, blank=True)             # default 0.25
    concurrent_requests  = models.PositiveSmallIntegerField(null=True, blank=True)
    obey_robots          = models.BooleanField(null=True, blank=True)
    include_subdomains   = models.BooleanField(null=True, blank=True)


class ScrapeDispatch(models.Model):
    """One row per SSM dispatch. Two jobs: (1) give the poller a freshness reference —
    S3 results older than dispatched_at belong to a previous run and must be ignored;
    (2) give the stall timeout a start time. Never deleted; latest row per collection wins."""
    collection     = models.ForeignKey(Collection, on_delete=models.CASCADE,
                                       related_name="scrape_dispatches")
    dispatched_at  = models.DateTimeField(auto_now_add=True)
    ssm_command_id = models.CharField(max_length=64)
```

`build_job_json` emits `{"seed": collection.url, "collection_id": collection.config_folder}` plus
**only the non-null** override fields. Validate `max_pages <= 100_000` before dispatch —
the crawler raises `ValueError` above the cap and the job would land in `jobs/failed/`.

`send_job_to_crawler` mirrors `scripts/drop_job.sh`: `ssm.send_command`,
`DocumentName="AWS-RunShellScript"`, writing to
`{CRAWLER_INBOX_PATH}/{config_folder}.json` and `chown ec2-user`. JSON must be shell-quoted with
`shlex.quote` — seed URLs contain characters that will otherwise break the heredoc.

### Validation

```bash
docker-compose -f local.yml run --rm django python manage.py makemigrations
docker-compose -f local.yml run --rm django python manage.py migrate
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_dispatch.py
```

New `sde_collections/tests/test_scrape_dispatch.py` (all AWS mocked):
- `build_job_json` with no overrides → exactly `{seed, collection_id}`.
- With `max_pages=5000, delay=None` → `delay` **absent**, `max_pages` present.
- `max_pages=200_000` raises before any SSM call.
- Status → `READY_FOR_ENGINEERING` calls `dispatch_scrape_job.delay` once (patch at
  `sde_collections.tasks.dispatch_scrape_job.delay`).
- `reindexing_status → REINDEXING_NEEDED_ON_DEV` also calls `dispatch_scrape_job.delay` once.
- A successful dispatch creates a `ScrapeDispatch` row carrying the SSM command id.
- SSM failure sets `SCRAPING_FAILED`, creates **no** `ScrapeDispatch` row, and does not raise out
  of the task.

### Manual verification (real dev AWS, `sde-dev` profile)
```bash
docker-compose -f local.yml run --rm django python manage.py dispatch_scrape --collection <config_folder>
aws ssm send-command --instance-ids i-0b6a61d95888886f4 \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["ls -la /opt/sde-crawler/jobs/incoming/"]' --profile sde-dev
# then confirm the watcher picked it up:
#   tail /opt/sde-crawler/logs/watch.log   and   ls /opt/sde-crawler/jobs/{done,failed}/
```

### Done when
- [x] `ScraperConfigOverride` + `ScrapeDispatch` created, admin-visible, migration applied
- [x] Job JSON omits null overrides and rejects `max_pages > 100_000`
- [x] `READY_FOR_ENGINEERING` **and** `REINDEXING_NEEDED_ON_DEV` dispatch via SSM; Sinequa scraper-config calls gone from those branches
- [x] Every dispatch records `dispatched_at` + `ssm_command_id`
- [x] A real job JSON lands in the dev crawler inbox and moves to `jobs/done/`

---

## Phase 4 — Poll for results and ingest S3 → `DumpUrl`

**Goal:** WORKFLOW.md steps 9–11. This is where `fetch_full_text` is functionally replaced.

### Completion contract

The crawler writes **no status file**. The reliable signal is S3, **filtered for freshness** —
S3 objects persist between runs, so every check below only counts an object whose `LastModified`
is **after the collection's latest `ScrapeDispatch.dispatched_at`** (P3). Without this, any
re-dispatch would instantly "complete" against the previous run's output.

| Object | Meaning |
|---|---|
| `failure_logs/{cid}_failures_summary.json` | Written **only** at the end of a completed run — this is the completion marker |
| `scraped_collections/{cid}.json` | The documents array |
| `failure_logs/{cid}_failures.jsonl` | Per-URL failures |

Fresh summary + `documents_scraped > 0` → **`SCRAPING_SUCCESSFUL`**.
Fresh summary + `documents_scraped == 0` → **`SCRAPING_FAILED`** (a zero-page crawl otherwise
"succeeds" and would silently produce an empty collection).
No fresh summary after the stall timeout (measured from `dispatched_at`) → **`SCRAPING_FAILED`**
(died mid-run, or the job never started).

Document shape is exactly seven fields — `{url, title, full_text, content_type, seed, host, depth}` —
which maps cleanly onto `DumpUrl(url=, scraped_title=, scraped_text=)`, the same contract
`fetch_full_text` already satisfies.

### Files

| File | Change |
|---|---|
| `sde_collections/scraping/s3_results.py` | **New.** `fetch_summary(cid)`, `fetch_documents(cid)`, `results_ready(cid)` |
| `sde_collections/tasks.py` | **New tasks** `poll_scrape_jobs()` and `ingest_scraped_collection(collection_id)` |
| `sde_collections/signals.py` | **New.** `post_migrate` → `poll_scrape_jobs` `PeriodicTask` (every 5 min), `enabled=settings.SCRAPE_POLL_ENABLED` |
| `sde_collections/apps.py` | Add `ready()` → `import signals` (currently 6 lines, no `ready()`) |
| `sde_collections/management/commands/ingest_scrape_results.py` | **New.** Manual ingest |
| `sde_collections/utils/slack_utils.py` | Wire the **already-written, never-called** `send_detailed_import_notification` into the ingest task |

`poll_scrape_jobs` scans collections in `READY_FOR_ENGINEERING` **or** `ENGINEERING_IN_PROGRESS`
(engineers flip to the latter while a crawl runs — a collection must not strand there), **plus**
collections with `reindexing_status == REINDEXING_NEEDED_ON_DEV` (the re-scrape path from P3),
checks S3 with the freshness rule above, and enqueues `ingest_scraped_collection`.

`ingest_scraped_collection` claims the collection **first**, then mirrors `fetch_full_text`'s body:

1. **Atomic claim** — the status transition is the lock, executed as a compare-and-swap:
   `Collection.objects.filter(id=..., workflow_status__in=[READY_FOR_ENGINEERING,
   ENGINEERING_IN_PROGRESS]).update(workflow_status=SCRAPING_SUCCESSFUL)`; if it returns 0, another
   ingest already claimed it — exit. (For the re-scrape path the CAS is on
   `reindexing_status: REINDEXING_NEEDED_ON_DEV → REINDEXING_FINISHED_ON_DEV` instead.)
   Claiming *before* the write matters: ingest can outrun the 5-minute poll, and `BaseUrl.url` is
   globally `unique=True`, so two concurrent ingests would die on `IntegrityError` mid-write.
2. Delete existing `DumpUrl`s → `bulk_create` in batches.
3. `collection.queue_necessary_classifications()` (which, with inference off from P2, calls
   `migrate_dump_to_delta_and_handle_status_transistions` → `READY_FOR_CURATION`; on the re-scrape
   path the migrate task's existing reindexing transition promotes to
   `REINDEXING_READY_FOR_CURATION`).
4. On ingest failure after a successful claim, set `SCRAPING_FAILED` — never leave a claimed
   collection stuck in `SCRAPING_SUCCESSFUL` with no `DumpUrl`s.

`tasks.py:216` `pre_workflow_statuses` must gain `SCRAPING_SUCCESSFUL` so the migration task
promotes to `READY_FOR_CURATION` from the new status.

> Replay stays safe: a manual re-run via `ingest_scrape_results` skips the CAS (explicit operator
> intent) but still deletes existing `DumpUrl`s first, so it is idempotent.

### Validation

```bash
docker-compose -f local.yml run --rm django python manage.py migrate    # creates the beat row
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_ingest.py
docker-compose -f local.yml logs -f celeryworker
```

New `sde_collections/tests/test_scrape_ingest.py` — S3 mocked with a fixture built from the real
7-field document shape:
- Happy path: N documents → N `DumpUrl`s with `scraped_title`/`scraped_text` populated →
  status `SCRAPING_SUCCESSFUL`.
- `documents_scraped == 0` → `SCRAPING_FAILED`, no `DumpUrl`s.
- Missing summary → collection stays `READY_FOR_ENGINEERING`, nothing enqueued.
- **Stale results:** summary `LastModified` **before** the latest `ScrapeDispatch.dispatched_at` →
  treated as absent; nothing enqueued. *(Re-dispatch regression guard.)*
- **Stall timeout:** no fresh summary and `dispatched_at` older than the timeout → `SCRAPING_FAILED`.
- **Concurrent claim:** second `ingest_scraped_collection` on an already-claimed collection exits
  without touching `DumpUrl`s (CAS returns 0).
- Re-running manual ingest twice yields N (not 2N) `DumpUrl`s — idempotency.
- Re-scrape path: `reindexing_status == REINDEXING_NEEDED_ON_DEV` + fresh results → ingest →
  `REINDEXING_READY_FOR_CURATION`.
- With inference disabled, ingest reaches `READY_FOR_CURATION`. *(End-to-end P2+P4 check.)*

### Manual verification (real dev AWS)
```bash
aws s3 ls s3://sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy/scraped_collections/ --profile sde-dev
docker-compose -f local.yml run --rm django python manage.py ingest_scrape_results --collection <config_folder>
docker-compose -f local.yml run --rm django python manage.py shell_plus
>>> c = Collection.objects.get(config_folder="<cf>")
>>> c.dump_urls.count(), c.delta_urls.count(), c.get_workflow_status_display()
```
Expect dump count to match `documents_scraped` in the summary, deltas created, status
`Ready for Curation`.

### Done when
- [x] S3 completion contract implemented, including the zero-document failure case **and the
      `dispatched_at` freshness rule**
- [x] `poll_scrape_jobs` beat row created via `post_migrate`, gated on `SCRAPE_POLL_ENABLED`
- [x] Ingest claims via CAS before writing, is idempotent, and populates `DumpUrl` without touching the model
- [x] Re-scrape path (`REINDEXING_NEEDED_ON_DEV`) polls and ingests end to end
- [x] A real dev collection goes seed URL → `Ready for Curation` end to end
- [ ] Slack posts an ingest summary *(wired in the migrate task + unit-asserted with counts; a real
      post is blocked until P5 removes the Sinequa `READY_FOR_CURATION → create_indexer_config`
      branch, which currently raises after the status save and cuts the task short — re-verify in P5)*

---

## Phase 5 — Curation triggers and the indexing hand-off seam

**Goal:** WORKFLOW.md steps 12–18, and a clean boundary for the deferred indexing work.

### Files

| File | Change |
|---|---|
| `sde_collections/models/collection.py:871` | Rewrite `create_configs_on_status_change`: drop the `READY_FOR_CURATION` indexer-config branch and the `INDEXING_FINISHED_ON_DEV` branch; keep `CURATED → promote_to_curated()`; replace `QC_PERFECT/QC_MINOR → add_to_public_query()` with the prod-indexing hand-off. **In the `reindexing_status` block:** drop `REINDEXING_FINISHED_ON_DEV → fetch_full_text` (the P4 ingest sets that status itself — a trigger here would double-fire); keep `REINDEXING_CURATED → promote_to_curated()`; `REINDEXING_NEEDED_ON_DEV → dispatch_scrape_job` was already added in P3 |
| `sde_collections/tasks.py` | **New stub tasks** `index_collection_to_test(collection_id)` and `index_collection_to_prod(collection_id)` |
| `sde_collections/models/collection.py:733` | Move the Slack block out of `save()` into the `post_save` signal |

The rewired dispatcher:

```
workflow_status:
  READY_FOR_ENGINEERING    -> dispatch_scrape_job.delay(id)          (from P3)
  CURATED                  -> promote_to_curated(); index_collection_to_test.delay(id)
  QC_PERFECT / QC_MINOR    -> index_collection_to_prod.delay(id)

reindexing_status:
  REINDEXING_NEEDED_ON_DEV -> dispatch_scrape_job.delay(id)          (from P3)
  REINDEXING_CURATED       -> promote_to_curated()
```

> **Rename the dispatcher.** `create_configs_on_status_change` no longer creates configs.
> Rename to `handle_workflow_status_change` and update
> `sde_collections/models/README_STATUS_TRIGGERS.md`.

> **Move the Slack call.** It currently sits in `Collection.save()` **before** `super().save()`
> and issues its own extra `Collection.objects.get()` query — so a message can be sent for a save
> that then fails. Moving it into the existing `post_save` receiver (which already has
> `old_workflow_status`) removes the extra query and the false-positive notification.

In this phase `index_collection_to_test` / `index_collection_to_prod` are **stubs**: they set
`TEST_INDEXING` / `PRODUCTION_INDEXING`, log, and return. Statuses 22/24/25/26 are therefore
defined and wired but not yet driven to completion.

These stubs are the **event-trigger seam for the `WEB_COSMOS` pipeline** (built in
`sde-api-scrapers`, branch `web-indexing` — see the decisions table). Phase 7 turns them into
export-then-dispatch tasks: mint a `run_id`, export the curated set to S3
(`documents.jsonl` + `manifest.json`, manifest last), assume the dispatch role, and `ecs:RunTask`
with a command override (`--source WEB_COSMOS --collection <config_folder> --target test|prod
--run-id <run_id>`) — they never index in-process. This is what replaces the api pipeline's
EventBridge schedule: indexing runs as soon as a collection is curated, not on a timer.

### Validation

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_workflow_status_triggers.py
```

Rewrite that file for the new trigger table — the existing tests assert Sinequa behaviour and
**will fail by design**. Cover: `CURATED` promotes **and** enqueues test indexing; `QC_*` enqueues
prod indexing; `REINDEXING_FINISHED_ON_DEV` triggers **nothing** (P4's ingest owns that
transition); `REINDEXING_CURATED` still promotes; no Sinequa method is called on any transition;
the re-entrancy guard (`_handling_status_change`) still prevents recursion.

### Manual verification
Drive a collection through `Ready for Curation → Curation in Progress → Curated` in the UI.
Confirm `CuratedUrl`s appear, `DeltaUrl`s are cleared, status lands on `Test Indexing`,
and Slack posts the curation message.

### Done when
- [ ] Dispatcher renamed and rewired; no Sinequa calls remain in the trigger path
- [ ] Slack moved into `post_save`
- [ ] Indexing stubs enqueue and set the in-flight statuses
- [ ] `test_workflow_status_triggers.py` rewritten and green

---

## Phase 6 — Delete Sinequa

**Goal:** `rewiring_decisions.md` items 4–5. Nothing in the pipeline path depends on Sinequa after
Phase 5, so this is now a pure removal.

### Delete outright

| Category | Paths |
|---|---|
| API client | `sde_collections/sinequa_api.py` |
| Config generation | `config_generation/` (**entire directory**, incl. `xmls/`, `plugins/`, `tests/`) |
| XML templates | `default_scraper.xml`, `sde_collections/xml_templates/` |
| GitHub push | `sde_collections/utils/github_helper.py`, `sde_collections/utils/bulk_github_push.py` |
| Health check | `sde_collections/utils/health_check.py` (built on `_get_data_to_import`) |
| Commands | `import_from_sinequa.py`, `push_to_github.py`, `sync_all_with_github.py`, `load_urls_from_api.py`, `generate_configs.py` |
| Tests | `sde_collections/tests/test_sinequa_api.py`, `sde_collections/tests.py` (legacy), `config_generation/tests/` |
| Docs | `docs/documentation/sinequa_api.rst` + its `docs/index.rst` toctree entry |
| Scripts | `scripts/push_curated_collections_to_github.py`, `scripts/update_has_sinequa_config.py` |

### Edit

| File | Removal |
|---|---|
| `collection.py` | `_scraper_config_path`, `_indexer_config_path`, `_indexer_job_path`, `_scraper_job_path`, `add_to_public_query`, `server_url_prod`, `server_url_secret_prod`, `_write_to_github`, `create_scraper_config`, `create_indexer_config`, `create_scraper_job`, `create_indexer_job`, `update_config_xml`, `import_metadata_from_sinequa_config`, `sinequa_configuration`, `_process_exclude_list`/`_include`/`_title`/`_document_type`, and the `XmlEditor`/`GitHubHandler` imports |
| `tasks.py` | `_get_data_to_import`, `import_candidate_urls_from_api`, `push_to_github_task`, `pull_latest_collection_metadata_from_github`, **`fetch_full_text`** (replaced in P4 — safe to delete only because P5 already removed both of its trigger sites, `INDEXING_FINISHED_ON_DEV` and `REINDEXING_FINISHED_ON_DEV`; verify no import of it remains in `collection.py`) |
| `views.py` | `PushToGithubView` (L509), `IndexingInstructionsView` (L517), the health-check/consolidation view; plus their `urls.py` routes |
| `config/settings/base.py` | `GITHUB_ACCESS_TOKEN`, `SINEQUA_CONFIGS_*`, `XLI_*`, `LRM_DEV_*`, `LRM_QA_*` — note these are all `env(...)` with **no defaults** (`base.py:341–354`), so today the app cannot even boot without dummy Sinequa secrets. Removing them is what makes clean-host deploys possible, which is why **P6 must land before P9's first deploy to a fresh host** |
| `requirements/base.txt` | `PyGithub`, `xmltodict`; check `lxml` for other consumers before dropping |
| Templates / JS | Sinequa config link in `collection_detail.html`; matching handler in `static/js/project.js` |

### Keep (deliberately)

- `SourceChoices.ONLY_IN_SINEQUA_CONFIGS` — a historical **data** value on existing rows.
  Removing it would need a data migration; leave it.
- `Collection.config_folder` — now the crawler `collection_id` and the AOSS `collection_key`.
- `scraper/` (legacy Scrapy project) — **out of scope**; unrelated to the Sinequa retirement.
  Flag for a separate cleanup.

> `utils/health_check.py` calls `WorkflowStatusChoices.get_status_string()` (L90, L119), which does
> not exist on that enum — a latent `AttributeError`. Deleting the file resolves it. If any part of
> health-check is worth keeping, the method must be added to the enum first.

### Validation

```bash
docker-compose -f local.yml run --rm django python manage.py check
docker-compose -f local.yml run --rm django pytest
grep -ri "sinequa\|XmlEditor\|GitHubHandler\|PyGithub" --include='*.py' --include='*.html' --include='*.js' .
```
The grep should return only `SourceChoices.ONLY_IN_SINEQUA_CONFIGS` and changelog/history text.

Unset every deleted env var in `.envs/.local/.django` **before** running — `config/settings/test.py`
inherits `base.py`, so a lingering required var would mask a missed reference.

### Done when
- [ ] All listed files deleted; `manage.py check` clean
- [ ] Full test suite green with the Sinequa env vars **unset**
- [ ] Grep is clean apart from the retained enum member
- [ ] `requirements/base.txt` pruned; image rebuilds

---

## Phase 7 — Indexing hand-off: export, dispatch, poll (= `sde-api-scrapers` Phase W4)

**No longer "deferred until the pipeline exists" — the pipeline exists.** It landed as a
`WEB_COSMOS` source on the **`web-indexing` branch of `sde-api-scrapers`** (its phases W0
foundations, W1 shared-component parameterization, W2 web pipeline, W3 infrastructure, and W5 tests
are code-complete: 209 offline tests green, `cdk synth` clean for dev/test/prod — but **nothing has
run against real AWS yet**, and all runtime defaults there target the disposable **`sde-web-copy`**
index until an explicit cutover). What remains here is exactly that repo's **Phase W4 — the
COSMOS side**: export, dispatch, poll, Slack. Authoritative docs on that branch: `DESIGN.md`,
`Web Indexing - Task Plan & Tracking.md`, `Update.md`, `open_questions.md` (decision record).

**Still blocked on Phase 5** (the stubs this phase fills in). Everything indexer-side is
independent of COSMOS and is exercised from its own CLI against hand-written exports.

### The contract (fixed by the built indexer — do not re-negotiate silently)

1. **Export (COSMOS → S3).** Write to the dedicated bucket **`sde-cosmos-indexing-{env}`**
   (cross-account; **not** the crawler's `SDE_S3_BUCKET`):

   ```
   curated_collections/{config_folder}/{run_id}/documents.jsonl
   curated_collections/{config_folder}/{run_id}/manifest.json   ← written LAST = "export complete"
   ```

   `run_id` is minted by COSMOS and threaded through every artifact. Each JSONL line:
   `{url, title, full_text, document_type, division, tdamm_tag, is_metadata_viewer}` — per-URL
   `division`/`document_type` only when they differ from the collection default. The manifest:
   `{schema_version, run_id, collection_key (= config_folder), collection_name, division, target,
   document_count, exported_at, cosmos_workflow_status}`. The indexer verifies line count against
   `document_count` and skips deletions on mismatch, so the count must be exact.

2. **Dispatch.** Assume **`CosmosIndexingDispatchRole-{env}`** (cross-account), then `ecs:RunTask`
   with a **command override**: `--source WEB_COSMOS --collection {config_folder}
   --target test|prod --run-id {run_id}`. (Not container-env overrides — the earlier
   `COLLECTION_ID`/`TARGET` sketch is superseded. Target→endpoint resolution is tier-capped on the
   indexer side, so a dev dispatch can never reach prod AOSS.)

3. **Completion (S3 poll — not `ecs.describe_tasks`).** The indexer writes
   `index_runs/{config_folder}/{run_id}/status.json` **last and unconditionally, including on
   failure**; on `test` runs it also writes `validation.json` (count + title diff vs the manifest —
   the WORKFLOW.md steps 22–25 QC report, produced indexer-side because only it holds AOSS
   credentials). `status.json` carries `state ∈ succeeded|failed`, counts, `deletion_ratio`,
   `deletion_mode` (deletes are **tombstones** — `public_visibility: false`, reversible), and a
   machine-readable `error`: `export_not_found | export_incomplete | foreign_documents_in_scan |
   scope_filter_ineffective | deletion_threshold_exceeded | deletion_budget_exceeded |
   opensearch_error`. **Treat unknown `state` values as failure** — `needs_confirmation` is
   reserved for future two-phase deletion.

### What COSMOS must NOT do

- **No `id`/`version` minting** — the indexer mints `id = /SDE/{config_folder}/|{url}` and a
  content-hash `version` itself (`web/web_processor.py` is the sole owner of identity). COSMOS
  exports raw curated fields only.
- **No AOSS, SageMaker, mapping, or deletion-guard concerns** — all live indexer-side. COSMOS gains
  no ML or OpenSearch dependencies; only S3 writes, one `sts:AssumeRole`, and one `ecs:RunTask`.

### Export traps (verified against the COSMOS models by the indexer team)

- **`excluded` is a queryset annotation, not a field** — export with
  `CuratedUrl.objects.filter(collection=c).exclude(excluded=True).iterator()`, or curator
  exclusions get published.
- **`tdamm_tag` is a `PairedFieldDescriptor`** (manual over ML), not a column — `.values()` /
  `.only()` on it fail; iterate instances. It is **exported but not indexed** (dropped by the
  indexer's allow-list, excluded from its version hash, so a tag-only edit never re-vectorizes).
- `title = generated_title or scraped_title`, resolved at export time.
- `document_type` / `division` are **nullable ints** — resolve `DocumentTypes(v).label` /
  `Divisions(v).label`, falling back to the collection's value.

### Files (mirrors `sde-api-scrapers` W4.1–W4.7)

| File | Change |
|---|---|
| `sde_collections/indexing/export.py` | **New.** `export_curated_to_s3(collection, target, run_id)` — stream `CuratedUrl`s per the traps above; write `documents.jsonl`, then `manifest.json` **last** |
| `sde_collections/indexing/dispatch.py` | **New.** `run_index_task(collection, target, run_id)` — assume the dispatch role, `ecs:RunTask` with the command override, return `taskArn` |
| `sde_collections/models/indexing.py` | **New** `IndexDispatch` (`collection` FK, `run_id`, `target`, `task_arn`, `dispatched_at`) — stall-timeout reference mirroring `ScrapeDispatch` (P3). Required because `CELERY_RESULT_BACKEND = None` means Celery task state cannot be polled |
| `sde_collections/tasks.py` | Fill the P5 stubs: `index_collection_to_test/prod` = mint `run_id` → export → dispatch → record `IndexDispatch` → set `TEST_INDEXING`/`PRODUCTION_INDEXING`. **New** `poll_index_runs()` |
| `sde_collections/signals.py` | `poll_index_runs` `PeriodicTask` every 2 min, gated on `INDEX_POLL_ENABLED` (same `post_migrate` pattern as P4's poller) |
| `sde_collections/utils/slack_utils.py` | Post `validation.json` to `sde-data-curation` (WORKFLOW.md step 24) |
| `config/settings/base.py` | `SDE_INDEX_BUCKET`, `INDEXING_ECS_CLUSTER`, `INDEXING_TASK_FAMILY`, `INDEXING_DISPATCH_ROLE_ARN`, `INDEX_POLL_ENABLED` — all **with defaults** so `config.settings.test` keeps booting |
| new migration | Creates `IndexDispatch` (additive) |

`poll_index_runs` status mapping: `succeeded` + `test` → stay at `TEST_INDEXING`, post the
validation report to Slack, curator sets QC; `succeeded` + `prod` → `PROD_PERFECT` / `PROD_MINOR`
mirroring the QC status it entered with (WORKFLOW.md step 30); `failed`, unknown state, or stall
timeout (measured from `dispatched_at`) → `INDEXING_FAILED_ON_TEST` / `INDEXING_FAILED_ON_PROD`.
The `run_id` namespacing means an old run's `status.json` can never satisfy a newer dispatch — no
`LastModified` freshness rule needed (unlike the P4 crawler contract).

### Cross-repo blockers (hand these over early — they gate the closed loop, not the coding)

- [ ] **Give the `sde-api-scrapers` team the COSMOS AWS account id** (per environment).
      `settings.COSMOS_AWS_ACCOUNT_ID` is empty there, and until it is filled the cross-account
      bucket policy and `CosmosIndexingDispatchRole` are deliberately **not synthesized** —
      dispatch cannot work. One dict entry + redeploy on their side; nothing else changes.
- [ ] Indexer stacks deployed to dev and the AOSS data-access policy granted (their OOB.2), plus
      `version` added as `keyword` to live `sde-web` before cutover (their OOB.1).
- [ ] **Cutover awareness:** flipping the indexer's `WEB_INDEX_NAME` from `sde-web-copy` to
      `sde-web` *is* the production cutover; COSMOS needs no change for it. Their open
      id-scheme-collision finding (12 collections, incl. 100% of `gcn_circulars`) is an
      indexer-side guard/repair — COSMOS is unaffected but should not onboard those collections
      until it lands.

### Validation

New `sde_collections/tests/test_indexing_dispatch.py` (AWS mocked): export writes the manifest
last; excluded URLs absent from the JSONL; tdamm/label resolution correct; `document_count` exact;
dispatch records an `IndexDispatch` row; the poller maps every `status.json` state (including
unknown-state-as-failure) and enforces the stall timeout; a stale run's `status.json` never
completes a newer dispatch.

### Done when
- [ ] Export/dispatch/poll implemented per the contract; `IndexDispatch` migration applied
- [ ] P5 stubs replaced: a `CURATED` collection reaches `TEST_INDEXING`, and on `succeeded` the
      validation report posts to Slack
- [ ] `QC_PERFECT`/`QC_MINOR` dispatches a prod run and lands on `PROD_PERFECT`/`PROD_MINOR`
- [ ] Failure/stall paths land on `INDEXING_FAILED_ON_TEST`/`INDEXING_FAILED_ON_PROD`
- [ ] Closed loop verified against dev (their E2E.10): Curated → export → `RunTask` → poller → Slack

---

## Phase 8 — QC reporting: resolved, folded into Phase 7

**The validation script no longer needs to be authored — the indexer produces it.** On every
`--target test` run, the `WEB_COSMOS` task writes `validation.json`
(`expected_count`, `indexed_count`, `count_matches`, `titles_missing_in_index`,
`titles_only_in_index`, `title_match_rate` — exactly the WORKFLOW.md steps 22–25 count/title
comparison) next to `status.json`. It lives indexer-side by design: the indexer already holds AOSS
credentials and COSMOS has none. Its counts exclude tombstoned documents.

COSMOS's entire share of this phase is inside P7: `poll_index_runs` reads `validation.json` and
posts it to `sde-data-curation`. The QC statuses stay **curator-set from the report**, so nothing
else is needed on the status side after Phase 1.

### Done when
- [ ] Covered by P7's done-when (validation report posted to Slack on test runs) — no separate work

---

## Phase 9 — CI/CD: deploy, rollback, preflight

**Goal:** implement `sde_collections/DEPLOYMENT.md`. Independent of Phases 3–8 — **authoring can
run in parallel once Phase 1 lands**, but the first deploy to a *fresh* host requires Phase 6:
the Sinequa settings are required env vars with no defaults (see P6), so until they're deleted a
clean host needs dummy Sinequa secrets to boot.

> **Note:** the earlier draft of this machinery is **not recoverable**. This clone has a 2-entry
> reflog, no stashes, and zero hits for `preflight_aws` / `validate_deploy_env` / `ecr.override` /
> `OPENSEARCH_ENDPOINT` across every commit in every ref. The only prior art is commit
> `08c3ef30` on the unmerged branch `94-add-cicd-…`, a 51-line `deploy.yml` stub with a placeholder
> role ARN and everything after the AWS-credentials step commented out. Write from scratch.

### Files

| File | Content |
|---|---|
| `sde_collections/management/commands/validate_deploy_env.py` | **New.** Fails if required settings are missing. Once P7 lands, it must also require the indexing settings (`SDE_INDEX_BUCKET`, `INDEXING_ECS_CLUSTER`, `INDEXING_TASK_FAMILY`, `INDEXING_DISPATCH_ROLE_ARN`) non-empty on deployed hosts. (Test/prod endpoint separation is enforced **indexer-side** — its target→endpoint resolution is tier-capped — so COSMOS has no endpoint-equality check to make) |
| `sde_collections/management/commands/preflight_aws.py` | **New.** SSM reachability to the crawler instance and S3 read on `SDE_S3_BUCKET`, using `get_boto3_session()` from P0. Reports each check independently rather than aborting on the first failure. P7 adds checks on `SDE_INDEX_BUCKET` (write `curated_collections/*`, read `index_runs/*`) and an `sts:AssumeRole` on the dispatch role; COSMOS never gets AOSS/SageMaker access, so no such checks exist here |
| `config/urls.py` + a `healthz` view | **New.** There is **no health endpoint in the repo today**; the deploy smoke checks need one. Minimal 200 + DB connectivity, unauthenticated |
| `.pre-commit-config.yaml` | **Fix:** the gitleaks hook passes `--config=gitleaks-config.toml`, but that file does not exist and is not tracked — the hook fails instead of scanning. Add the config or drop the arg |
| `scripts/deploy.sh` | **New.** The single definition of a deploy, in `DEPLOYMENT.md`'s order: fetch artifact → `validate_deploy_env` → backup (prod only) → `migrate` → `docker compose up -d` → smoke checks → rollback on failure |
| `ecr.override.yml` | **New.** Compose override pulling the Django image from ECR |
| `.github/workflows/ci.yml` | **New.** `run-tests` and `django-checks` (`check --deploy`, `makemigrations --check --dry-run`) on PRs into `dev`, `staging`, **and** `production` — today only `dev` is covered, so the release path itself is untested. Drop `init.sh`'s per-file loop (a process per test file, re-paying Django setup each time) in favour of a single `pytest` run |
| `.github/workflows/deploy-staging.yml` | build → ECR → SSM → `deploy.sh --environment staging` |
| `.github/workflows/deploy-production.yml` | staging-digest check → SSM → `deploy.sh --environment production`, gated on the `production` GitHub Environment |
| `.github/workflows/rollback.yml` | Manual redeploy of a named image tag |
| `.github/workflows/secret-scan-history.yml` | Weekly full-history gitleaks, report-only |
| `.github/workflows/run_full_test_suite.yml` | **Delete** — superseded by `ci.yml` |

All `deploy-*` and `rollback` workflows gate on repo variable **`CD_ENABLED`**; until it is `true`
they skip.

> **Ordering matters:** `validate_deploy_env` runs *before* anything mutates. A host missing
> `INDEXING_DISPATCH_ROLE_ARN` must fail there, not inside a Celery task that has already exported
> a collection it can never dispatch.

> **`celerybeat` must be recreated on every deploy.** The inference `PeriodicTask` rows (P2) and the
> `poll_scrape_jobs` schedule (P4) are written by `post_migrate`; a beat process left running on the
> old schedule silently ignores them.

### Validation

```bash
docker-compose -f local.yml run --rm django python manage.py validate_deploy_env   # expect clear failure locally
docker-compose -f local.yml run --rm django python manage.py preflight_aws         # against sde-dev
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_deploy_commands.py
bash -n scripts/deploy.sh && shellcheck scripts/deploy.sh
```

Tests (AWS mocked): `validate_deploy_env` exits non-zero on any missing required setting;
`preflight_aws` reports each check independently and does not abort on the first failure.

### Manual verification
1. `aws ssm describe-instance-information --filters "Key=InstanceIds,Values=<staging-id>" --query 'InstanceInformationList[0].PingStatus'` → `Online`
2. `aws ecr describe-repositories --repository-names cosmos` → no error
3. Deploy to **staging** only, then **rehearse a rollback on staging** before trusting production.

### Done when
- [ ] Both management commands exist with tests
- [ ] `scripts/deploy.sh` passes `shellcheck`; runs end to end on staging
- [ ] Five workflows added, `run_full_test_suite.yml` removed, CI runs on all three branches
- [ ] `/healthz` endpoint added and asserted by the deploy smoke checks
- [ ] gitleaks hook actually runs (missing `gitleaks-config.toml` resolved)
- [ ] **Production DB credential rotated** — it is live in committed `HEAD` at `SQLDumpRestoration.md:101,117` along with the RDS hostname; scrub the file after rotating
- [ ] A rollback rehearsed successfully on staging
- [ ] `CD_ENABLED` prerequisites documented as met (or explicitly pending)

---

## End-to-end verification (after Phases 0–6)

```bash
docker-compose -f local.yml build && docker-compose -f local.yml up -d
docker-compose -f local.yml run --rm django python manage.py migrate
docker-compose -f local.yml run --rm django pytest
```

Then, against the dev AWS account:

1. Create a collection in the admin with a real `seed_url` and a `division`.
2. Set **Research in Progress → Ready for Engineering**.
3. Confirm the job JSON reaches `/opt/sde-crawler/jobs/incoming/<config_folder>.json` and moves to
   `jobs/done/`.
4. Confirm `s3://<SDE_S3_BUCKET>/scraped_collections/<config_folder>.json` and the
   `_failures_summary.json` both appear.
5. Watch `docker-compose -f local.yml logs -f celeryworker` — the poller ingests, status becomes
   **Scraping Successful**, then **Ready for Curation**.
6. `shell_plus`: `c.dump_urls.count()` matches `documents_scraped`; `c.delta_urls.count() > 0`.
7. Curate, set **Curated**, confirm `CuratedUrl`s exist and `DeltaUrl`s are cleared.
8. Confirm Slack received the ingest summary and the curation message.
9. **Re-scrape:** set `reindexing_status` to **Re-Indexing Needed** on the same collection —
   confirm a *new* `ScrapeDispatch` row, that the poller ignores the old S3 output until fresh
   results land, and that the collection reaches **Ready for Re-Curation**.

Steps beyond 8 (test indexing, validation, prod indexing) need **Phase 7**. The indexer side is
code-complete on `sde-api-scrapers`' `web-indexing` branch, but the closed loop additionally needs
the COSMOS AWS account id recorded there, its stacks deployed, and the AOSS data-access policy
granted. Until then status stops at `Test Indexing`.

---

## Cross-cutting risks

| Risk | Mitigation |
|---|---|
| Colour-map `KeyError` breaks the collection list/detail pages | P1 converts both lookups to `.get(..., "btn-light")` and adds a parametrised test over every enum member |
| Three TDAMM collections stall forever when inference is disabled | P2 short-circuits `queue_necessary_classifications()` itself, not just the beat schedule; regression test included |
| Credential-model mismatch (static keys in code vs instance role in `DEPLOYMENT.md`) | P0's `get_boto3_session()` is the single entry point; no new static-key call sites. Helper reads `SDE_AWS_*`, never the django-storages `AWS_ACCESS_KEY_ID` (absent from `base.py` → `AttributeError` under test, and wrong credential scope) |
| Zero-page crawl silently produces an empty collection | P4 treats `documents_scraped == 0` as `SCRAPING_FAILED` |
| **Stale S3 results ingested after a re-dispatch** | P3's `ScrapeDispatch.dispatched_at` + P4's freshness rule: results with `LastModified` before the latest dispatch are invisible to the poller |
| **Re-scrape (reindexing) flow severed when `fetch_full_text` is deleted** | P3 dispatches on `REINDEXING_NEEDED_ON_DEV`; P4 polls it and flips `REINDEXING_FINISHED_ON_DEV` itself; P5 removes the old trigger branch; P6's deletion is then safe |
| Duplicate ingest from the 5-minute poller | Ingest claims via an atomic status CAS **before** writing (ingest can outrun the poll interval, and `BaseUrl.url` is globally unique — concurrent writes would `IntegrityError`); manual re-ingest stays idempotent by deleting `DumpUrl`s first |
| Deleting Sinequa breaks unrelated GitHub metadata sync | P6 keeps `sync_with_production_webapp` (COSMOS prod webapp) and removes only the Sinequa-configs-repo paths |
| `config/settings/test.py` inherits `base.py`, so stale env vars mask missed references | P6 validation runs with the deleted vars unset |
| **Cross-account dispatch silently unbuildable** — `sde-api-scrapers` has no COSMOS account id, so its bucket policy and `CosmosIndexingDispatchRole` are (deliberately) not synthesized | Hand the account id over as a P7 precondition — one dict entry (`settings.COSMOS_AWS_ACCOUNT_ID`) + redeploy on their side |
| Curator-excluded URLs published to search | P7 export uses `.exclude(excluded=True)` — `excluded` is a queryset annotation, not a field; test asserts exclusions never reach the JSONL |
| Truncated export read as a mass deletion | Indexer-side guard: line count vs `manifest.document_count` → `export_incomplete`, deletions skipped. COSMOS's job is writing the manifest **last** with an exact count |
| Stale `status.json` completes a newer index dispatch | Every artifact is namespaced by the COSMOS-minted `run_id` (`index_runs/{cf}/{run_id}/`), so cross-run staleness is structurally impossible — unlike the P4 crawler contract, which needs the `LastModified` freshness rule |
| `factories.py:49` has a suspect `tracker = factory.Maybe("workflow_status")` | Watch during P1/P5 test rewrites; fix if it interferes with `FieldTracker` |
| Migration rollback safety | All migrations here are additive (new model, choices-only `AlterField`); `DEPLOYMENT.md`'s "image rollback is a complete rollback" property holds |
