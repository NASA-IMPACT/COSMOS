# COSMOS Local Verification Guide — Phases 0–7

This guide verifies the rewired COSMOS pipeline (branch `cosmos-rewiring`, Phases 0–7) by
**walking one real collection through the entire workflow on your machine**:
*Aurorasaurus — Reporting Auroras from the Ground Up*
(`config_folder: aurorasaurus_reporting_auroras_from_the_ground_up`).

Why this collection: the crawl4ai scraper **already crawled it for real** — its output (25
documents from `aurorasaurus.org`) sits in the dev S3 bucket. That lets the demo ingest *genuine
scraped data* through the *genuine production code path*, no mocks. Only one thing stays
simulated: the WEB_COSMOS indexer's responses. Its AWS stacks *are* deployed in the dev account
(the `sde-cosmos-indexing-dev` bucket, the `CosmosIndexingDispatchRole-dev` role, and the
`web_cosmos-scraper-dev` task family) — simulating its replies is a choice of this local
walkthrough, which runs COSMOS on your machine and deliberately starts no real Fargate tasks.

Each step of the walkthrough has the same shape:

- **Where we are** — what this hop means in the curation workflow, and which phase built it.
- **Do this** — exact commands / clicks.
- **Expect this** — the observed outcome (this walkthrough was executed successfully on
  2026-08-14; every expected output below is what actually happened).
- **Phase tests** — the pytest suite that locks the behavior in.

*No dev-AWS access?* Appendix A has a fully-offline variant of the ingest using mocked S3.

---

## The workflow you are about to walk

```
Research in Progress
      │  curator finishes research, sets…
      ▼
Ready for Engineering ──────► COSMOS builds a job JSON and SSM-sends it     (Phase 3)
      │                        to the crawl4ai crawler on EC2
      ▼
   [crawler runs; writes results + a completion summary to S3]
      │
      ▼
Scraping Successful ────────► COSMOS polls S3, ingests documents into       (Phase 4)
      │                        DumpUrls, then migrates them to DeltaUrls
      ▼                        (inference is dormant — Phase 2 — so the
Ready for Curation             migration runs immediately)
      │  curator reviews/edits the deltas in the UI, sets…
      ▼
Curated ────────────────────► promote_to_curated(): deltas become           (Phase 5)
      │                        CuratedUrls; COSMOS exports them to S3 and
      ▼                        fires the WEB_COSMOS indexer (test target)   (Phase 7)
Test Indexing ──────────────► poller reads the indexer's status.json;
      │                        validation report posts to Slack
      │  curator QCs the test index, sets…
      ▼
QC: Perfect / QC: Minor ────► same hand-off, prod target                    (Phase 7)
      ▼
Production Indexing ────────► poller resolves; final status mirrors QC:
      ▼
Prod: Perfect / Prod: Minor Issues        ← the finish line
```

Failure at any dispatch/poll lands on a red status (**Scraping Failed**, **Indexing Failed on
Test/Prod**) instead of raising — which this guide uses deliberately: with the indexer's AWS
settings blank, its two dispatch hops fail *gracefully*, and that graceful failure is itself the
proof the trigger fired. Phase 0 supplies the shared settings/credentials plumbing, Phase 1 the
six new statuses, Phase 6 removed the old Sinequa machinery entirely.

---

## 0. Setup

### Prerequisites

- Docker Desktop running.
- Repo on branch `cosmos-rewiring`.
- A local database restored from production (the Aurorasaurus collection must exist — checked in
  Step A below).
- For the real-S3 ingest: `aws sso login --profile sde-dev` (account 998871305517). Everything
  else works without it.

### Environment — `.envs/.local/.django`

All pipeline vars already exist in this file. For this walkthrough the AWS-facing ones stay
**blank** and the pollers **off**:

| Var | Value | Why |
|---|---|---|
| `SLACK_WEBHOOK_URL` | any non-empty dummy, e.g. `http://localhost/dummy` | **Required to boot** (no default). Dummy → every Slack post prints a caught error and continues. Real webhook → messages actually post on every status change. |
| `SDE_S3_BUCKET`, `CRAWLER_INSTANCE_ID` | blank | The scrape-dispatch hop then fails gracefully (Step 3's wiring proof). The real bucket is injected per-command in Step 4, not set here. |
| `SDE_INDEX_BUCKET`, `INDEXING_*` | blank (keep `INDEXING_CONTAINER_NAME` default) | The indexing hops then fail gracefully (Steps 5 & 7). Deliberate: the dev stacks are live, and a local run should not export to their bucket or start real Fargate tasks. |
| `SCRAPE_POLL_ENABLED`, `INDEX_POLL_ENABLED`, `INFERENCE_ENABLED` | `False` | With blank buckets the pollers would only log S3 errors every 2–5 min; the inference-off state is itself verified in Step 2. |
| `SDE_AWS_ACCESS_KEY_ID`, `SDE_AWS_SECRET_ACCESS_KEY` | blank | Keeps `get_boto3_session()` on the default credential chain — which is exactly how Step 4 injects short-lived SSO credentials. |

### Build and start

```bash
docker-compose -f local.yml build
docker-compose -f local.yml up -d          # django, postgres, redis, celeryworker, celerybeat, flower
docker-compose -f local.yml run --rm django python manage.py createsuperuser   # first time only
```

Migrations run automatically on startup. Confirm the rewiring migrations are in:

```bash
docker-compose -f local.yml run --rm django python manage.py showmigrations sde_collections | tail -3
# [X] 0078_alter_collection_workflow_status_and_more   ← statuses 21–26 (Phase 1)
# [X] 0079_scraperconfigoverride_scrapedispatch        ← Phase 3 models
# [X] 0080_indexdispatch                               ← Phase 7 model
```

### URLs

> **Gotcha:** the django log says `Starting development server at http://0.0.0.0:8000/` — that is
> the address *inside the container*. On your host the app is on **8001** (`local.yml` maps
> `8001:8000`; host port 8000 usually belongs to the inference API, which answers
> `{"detail": "Not Found"}` if you hit it by mistake). First visit redirects to the login page —
> sign in with your superuser.

| What | URL |
|---|---|
| Collection list (main UI) | `http://localhost:8001/` |
| Collection detail | `http://localhost:8001/<id>/` |
| Django admin | `http://localhost:8001/admin/` |
| Flower (Celery monitor) | `http://localhost:5555/` |

### Running the tests

> **Important — test isolation from the live worker:** `config/settings/test.py` forces
> `CELERY_BROKER_URL=memory://` (both the setting *and* the env var — Celery gives the env var
> precedence). Without it, tests that change workflow statuses publish real task messages onto
> the same Redis your celeryworker consumes, and the worker executes them against your **local
> database** — test-DB collection ids can collide with real rows and silently flip their
> statuses. If you ever see a burst of `dispatch_scrape_job` / `DoesNotExist` noise in the
> worker log right after a pytest run, check that override is still in place.

```bash
# Everything in sde_collections (expect: 308 passed):
docker-compose -f local.yml run --rm django pytest sde_collections/tests/

# Just the rewiring suites (expect: 129 passed = 4 + 74 + 7 + 10 + 15 + 19):
docker-compose -f local.yml run --rm django pytest \
  sde_collections/tests/test_aws_utils.py \
  sde_collections/tests/test_workflow_status_triggers.py \
  sde_collections/tests/test_inference_flag.py \
  sde_collections/tests/test_scrape_dispatch.py \
  sde_collections/tests/test_scrape_ingest.py \
  sde_collections/tests/test_indexing_dispatch.py
```

### Shell for the paste-in snippets

Every Python snippet below runs in:

```bash
docker-compose -f local.yml run --rm django python manage.py shell_plus
```

---

## Step A — Meet the demo collection (baseline)

**Where we are.** Before touching anything, establish what exists: the collection in your local
DB, and its finished crawl in the dev S3 bucket.

**Do this** — in `shell_plus`:

```python
from sde_collections.models.collection import Collection
c = Collection.objects.get(config_folder="aurorasaurus_reporting_auroras_from_the_ground_up")
print(c.id, "|", c.name)
print("status:", c.get_workflow_status_display())
print("dump:", c.dump_urls.count(), "| delta:", c.delta_urls.count(), "| curated:", c.curated_urls.count())
```

**Expect this:** the collection exists (id `1431` on the 2026-08 restore) with **25 curated
URLs** — it has been through curation before, which makes the Step 4 diff meaningful. Its status
may be anything; the walkthrough sets what it needs at each step, and the whole run is
**repeatable** (re-ingesting replaces dumps and re-diffs; nothing accumulates).

And, if you have `sde-dev` access, confirm the crawl output (the completion marker is the
`_failures_summary.json` — the crawler writes it only at the end of a completed run):

```bash
aws s3 ls s3://sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy/scraped_collections/ --profile sde-dev | grep aurorasaurus
aws s3 ls s3://sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy/failure_logs/ --profile sde-dev | grep aurorasaurus
# aurorasaurus_reporting_auroras_from_the_ground_up.json                    (25 documents, 2026-08-13)
# aurorasaurus_reporting_auroras_from_the_ground_up_failures_summary.json   (the completion marker)
```

---

## Step 0 — Foundations hold (Phase 0)

**Where we are.** Phase 0 added the `SDE_*` settings block (every var with a safe default) and
`get_boto3_session()` — the single credential entry point for all pipeline AWS code: explicit
`SDE_AWS_*` keys if both are set, otherwise the default chain (instance role in AWS, env vars
locally). The fact that your stack booted with everything blank *is* the core guarantee.

**Do this / expect this:**

```bash
docker-compose -f local.yml run --rm django python manage.py check
# → "System check identified no issues"
```

```python
from django.conf import settings
from sde_collections.utils.aws import get_boto3_session
s = get_boto3_session()
print(s.region_name)                         # → us-east-1
print(bool(settings.SDE_AWS_ACCESS_KEY_ID))  # → False — default-chain branch taken
```

**Phase tests** — expect `4 passed`:

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_aws_utils.py -v
```

---

## Step 1 — The status vocabulary (Phase 1)

**Where we are.** The workflow diagram above needs six statuses that didn't exist before:
`Scraping Successful` (21), `Test Indexing` (22), `Scraping Failed` (23), `Indexing Failed on
Test` (24), `Indexing Failed on Prod` (25), `Production Indexing` (26). Phase 1 added them,
fixed both colour maps to never `KeyError` on an unmapped status, and made failure statuses
render **red** instead of neutral.

**Do this** — at `http://localhost:8001/`, find *Aurorasaurus — Reporting Auroras from the Ground
Up* in the list (search box helps):

1. Open its **workflow status dropdown** — all 26 statuses are listed; the filter panel shows
   them too.
2. Open its detail page → **Workflow History** tab. Every transition the walkthrough makes from
   here on will appear in this tab — check back after each step.

**Expect this:** dropdown renders with no JS console errors; failure statuses show as red
buttons (`btn-danger`).

**Spot-check in shell:**

```python
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.models.collection import Collection
print(len(WorkflowStatusChoices.choices))    # → 26
c = Collection(workflow_status=WorkflowStatusChoices.SCRAPING_FAILED)
print(c.workflow_status_button_color)        # → btn-danger
```

**Phase tests** — expect `74 passed` (parametrized over every status × both colour maps; also
covers the Phase 5 trigger table):

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_workflow_status_triggers.py -v
```

---

## Step 2 — Inference is dormant, not dead (Phase 2)

**Where we are.** The old pipeline routed three hard-coded TDAMM collections through an ML
inference job between scraping and curation. That pipeline is now gated off
(`INFERENCE_ENABLED=False`): `queue_necessary_classifications()` short-circuits straight to the
delta migration for *every* collection. This matters for Step 4 — it's why the ingest reaches
*Ready for Curation* in seconds instead of stranding behind a queued inference job that never
runs.

**Do this / expect this:**

```python
from django_celery_beat.models import PeriodicTask
print(list(PeriodicTask.objects.filter(task__startswith="inference").values("name", "enabled")))
# → both rows enabled=False
```

The disable is durable: re-running `manage.py migrate` re-asserts `enabled` from the flag (the
`post_migrate` signal owns these rows — a hand-edit in the admin does not survive a deploy, by
design). Optionally watch `docker-compose -f local.yml logs -f celerybeat` — no inference ticks.

**Phase tests** — expect `7 passed`:

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_inference_flag.py -v
```

---

## Step 3 — Requesting a scrape (Phase 3)

**Where we are.** In production, a curator sets **Ready for Engineering** and COSMOS reacts:
`build_job_json()` merges the collection's seed URL with any per-collection
`ScraperConfigOverride` (only non-null fields are emitted — the crawler supplies its own
defaults), and `send_job_to_crawler()` drops the JSON into the crawler's inbox on EC2 via SSM,
recording a `ScrapeDispatch` row (the poller's freshness reference). For Aurorasaurus **this
already happened** — the Aug-13 crawl in the bucket *is* the output of this hop. So locally we
verify the machinery two ways: the job-builder logic in the shell, and the trigger via its
graceful failure path.

**Do this (1) — job-builder spot-checks:**

```python
from sde_collections.models.collection import Collection
from sde_collections.models.scraper_config import ScraperConfigOverride
from sde_collections.scraping.job_builder import build_job_json

c = Collection.objects.get(config_folder="aurorasaurus_reporting_auroras_from_the_ground_up")
print(build_job_json(c))
# → {"seed": "https://aurorasaurus.org/", "collection_id": "aurorasaurus_reporting_auroras_from_the_ground_up"}

ScraperConfigOverride.objects.update_or_create(collection=c, defaults={"max_pages": 25, "delay": None})
print(build_job_json(c))
# → adds "max_pages": 25; "delay" ABSENT (null overrides are never emitted)
# (max_pages=25 is exactly the override the real Aug-13 crawl ran with — see its summary)

ScraperConfigOverride.objects.filter(collection=c).update(max_pages=200_000)
try:
    build_job_json(c)
except ValueError as e:
    print("cap enforced:", e)   # → the crawler rejects >100_000, so COSMOS refuses to send it

ScraperConfigOverride.objects.filter(collection=c).delete()   # clean up
```

**Do this (2) — the trigger, via its failure path.** In the UI set the collection to
**Ready for Engineering**, then watch:

```bash
docker-compose -f local.yml logs -f celeryworker
```

**Expect this:** within seconds —
`Scrape dispatch failed for aurorasaurus_reporting_auroras_from_the_ground_up: Unable to locate credentials`
and the status flips to **Scraping Failed** (red). That failure *is* the proof: the trigger
fired, the SSM call was attempted, and the error path held (no exception escaped, no
`ScrapeDispatch` row recorded — check Admin → **Scrape dispatches**, a read-only list). With
real crawler settings this same click lands a job JSON in `/opt/sde-crawler/jobs/incoming/`.

Also verifiable: Admin → **Scraper config overrides** is the curator-facing override editor, and
`manage.py dispatch_scrape --collection <cf>` is the manual CLI re-dispatch (same code path;
locally it exits with a `CommandError` after marking *Scraping Failed* — expected).

**Phase tests** — expect `10 passed`:

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_dispatch.py -v
```

---

## Step 4 — Ingesting the real crawl (Phase 4) ★ the centerpiece

**Where we are.** In production, `poll_scrape_jobs` (a beat task, every 5 min) notices the fresh
completion summary in S3 and enqueues `ingest_scraped_collection`, which:

1. **claims** the collection with an atomic compare-and-swap
   (*Ready for Engineering / Engineering in Progress → Scraping Successful*) so two ingests can
   never write concurrently;
2. replaces its `DumpUrl`s with the scraped documents;
3. hands off to the delta migration, which diffs the new dump against the existing `CuratedUrl`s
   and promotes the status to **Ready for Curation**.

We run exactly that path — real S3, real documents, `claim=True` — injecting your short-lived
SSO credentials and the real bucket into a one-shot container (the env file stays untouched;
`SDE_AWS_*` stay blank so the default chain picks up the session token).

**Do this** — from the repo root, after `aws sso login --profile sde-dev`:

```bash
eval "$(aws configure export-credentials --profile sde-dev --format env)"
docker-compose -f local.yml run --rm \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
  -e SDE_S3_BUCKET=sdecrawlerstack-crawlbucket0d63eba8-lhkxqnh8ophy \
  django python manage.py shell -c "
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.tasks import ingest_scraped_collection

c = Collection.objects.get(config_folder='aurorasaurus_reporting_auroras_from_the_ground_up')
c.workflow_status = WorkflowStatusChoices.ENGINEERING_IN_PROGRESS   # claimable; no trigger
c.save()

print(ingest_scraped_collection(c.id))   # claim=True: the full production path
c.refresh_from_db()
print('status:', c.get_workflow_status_display())
print('dump_urls:', c.dump_urls.count())
"
```

**Expect this** (observed on the 2026-08-14 run):

```
Ingested 25 documents for aurorasaurus_reporting_auroras_from_the_ground_up (replaced 0).
status: Scraping Successful
dump_urls: 25
```

The ingest ends by enqueueing the migration, which the **celeryworker** executes (no S3 needed
there). Give it a few seconds, then:

```python
from sde_collections.models.collection import Collection
c = Collection.objects.get(config_folder="aurorasaurus_reporting_auroras_from_the_ground_up")
print(c.get_workflow_status_display())   # → Ready for Curation
print(c.dump_urls.count(), c.delta_urls.count(), c.curated_urls.count())
```

**Expect this:** `Ready for Curation`, dumps `0` (cleared by the migration), curated still `25`
— and deltas **`0`**. Zero is the *correct* real-world answer here: the Aug-13 crawl matches the
already-curated set exactly, so the differ found nothing new, changed, or deleted. A re-crawl
with actual site changes would surface exactly those pages as deltas. In the worker log you'll
also see the ingest-summary Slack attempt (caught error with a dummy webhook).

**Verify in the UI:** the collection shows **Ready for Curation**; **Workflow History** now has
*Engineering in Progress → Scraping Successful → Ready for Curation*.

Two failure modes worth knowing (both unit-tested): a completed crawl with
`documents_scraped == 0` is marked **Scraping Failed** (an empty crawl must never silently
publish an empty collection), and stale S3 results older than the latest `ScrapeDispatch` are
invisible to the poller (re-dispatch safety).

**Phase tests** — expect `15 passed`:

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_ingest.py -v
```

---

## Step 5 — Curation and the hand-off to test indexing (Phase 5)

**Where we are.** *Ready for Curation → Curated* is the human part of the workflow: curators
review the deltas (exclude URLs, fix titles, tag divisions) in the UI. Setting **Curated** fires
the rewired dispatcher (`handle_workflow_status_change`), which does two things: promotes the
deltas into `CuratedUrl`s, and fires `index_collection_to_test` — the Phase 7 hand-off. With the
indexer's settings blank, that second hop fails gracefully: the wiring proof again.

**Do this** — in the UI (or shell), walk the collection
*Ready for Curation → Curation in Progress → Curated*. With zero deltas there is nothing to
review this time — which is itself the honest outcome — so this step is mostly about the
trigger. Watch the worker log as you set **Curated**.

**Expect this:**

- `CuratedUrl`s: still 25, `DeltaUrl`s: 0 (promote with an empty delta set is a no-op — the
  curated data is never touched unnecessarily).
- Worker log: `Index dispatch (test) failed for aurorasaurus_…: SDE_INDEX_BUCKET is not
  configured — cannot export`, and the status lands on **Indexing Failed on Test** (red).
- With the `INDEXING_*` settings filled in from the dev stacks, this same click would export
  `curated_collections/{cf}/{run_id}/documents.jsonl` + `manifest.json` to S3, `ecs:RunTask` the
  WEB_COSMOS indexer, and land on **Test Indexing**.

**Phase tests:** the trigger table lives in the same suite as Step 1 (`74 passed`); it asserts
`CURATED` promotes *and* enqueues test indexing, `QC_*` enqueues prod indexing, and no Sinequa
method is called on any transition.

---

## Step 6 — Sinequa is gone (Phase 6)

**Where we are.** Everything the old pipeline used — the Sinequa API client, XML config
generation, the GitHub configs push — was deleted outright in Phase 6. The whole walkthrough you
just did ran without any of it; this step proves the removal is total.

**Do this / expect this:**

```bash
ls sde_collections/sinequa_api.py config_generation default_scraper.xml 2>&1
# → "No such file or directory" for each

grep -ri "sinequa_api\|XmlEditor\|GitHubHandler\|PyGithub" \
  --include='*.py' --include='*.html' --include='*.js' sde_collections/ config/
# → empty  (a plain grep for "sinequa" still hits comments/help_text — historical, retained
#           deliberately, plus the SourceChoices.ONLY_IN_SINEQUA_CONFIGS data value)

docker-compose -f local.yml run --rm django python manage.py check    # boots with NO Sinequa env vars
docker-compose -f local.yml run --rm django pytest sde_collections/tests/   # → 308 passed
```

**In the UI:** no Sinequa config link on the collection detail page; no
`import_from_sinequa` / `push_to_github` in `manage.py --help`.

---

## Step 7 — The indexing hand-off, resolved (Phase 7)

**Where we are.** Phase 7 filled the Phase 5 stubs with the real contract: mint a `run_id`,
export curated docs to `curated_collections/{cf}/{run_id}/` (manifest written **last** = export
complete), assume the cross-repo dispatch role, `ecs:RunTask` the WEB_COSMOS indexer with a
command override, record an `IndexDispatch` row, and let `poll_index_runs` (beat, every 2 min)
resolve the run by reading `index_runs/{cf}/{run_id}/status.json` from S3 — never
`ecs.describe_tasks`. The `run_id` namespacing means an old run's status can never satisfy a
newer dispatch.

The indexer is live in the dev account, but a local walkthrough has no business starting real
Fargate tasks — so here we simulate **its half only** — the `status.json` responses — while
running COSMOS's poller for real. Three outcomes, continuing from *Indexing Failed on Test*:

**Do this** — paste into `shell_plus`:

```python
from unittest import mock
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.models.indexing import IndexDispatch
from sde_collections import tasks

c = Collection.objects.get(config_folder="aurorasaurus_reporting_auroras_from_the_ground_up")

# --- Outcome 1: test run SUCCEEDS → status holds at Test Indexing; the indexer-produced
#     validation report (count/title QC) is posted to Slack for the curator to judge ---
c.workflow_status = WorkflowStatusChoices.TEST_INDEXING   # no trigger on this status
c.save()
IndexDispatch.objects.create(collection=c, run_id="aurora-e2e-1", target="test",
                             task_arn="arn:demo", previous_workflow_status=WorkflowStatusChoices.CURATED)
validation = {"expected_count": 25, "indexed_count": 25, "count_matches": True,
              "title_match_rate": 1.0, "titles_missing_in_index": [], "titles_only_in_index": []}
with mock.patch.object(tasks, "fetch_run_status", return_value={"state": "succeeded"}), \
     mock.patch.object(tasks, "fetch_validation_report", return_value=validation):
    print(tasks.poll_index_runs())        # → "Resolved 1 index run(s)."
c.refresh_from_db()
print(c.get_workflow_status_display())    # → Test Indexing  (curator now sets QC from the report)
```

**Now the QC trigger, for real.** In the UI (or shell) set **QC: Minor Issues** and watch the
worker: `Index dispatch (prod) failed … SDE_INDEX_BUCKET is not configured` → status
**Indexing Failed on Prod**. That's the `QC_* → index_collection_to_prod` trigger, proven the
same way as Step 5. Then resolve the prod run:

```python
# --- Outcome 2: prod run SUCCEEDS → final status mirrors the QC status it entered with ---
c.refresh_from_db()
c.workflow_status = WorkflowStatusChoices.PRODUCTION_INDEXING
c.save()
IndexDispatch.objects.create(collection=c, run_id="aurora-e2e-2", target="prod",
                             task_arn="arn:demo",
                             previous_workflow_status=WorkflowStatusChoices.QUALITY_CHECK_MINOR)
with mock.patch.object(tasks, "fetch_run_status", return_value={"state": "succeeded"}):
    print(tasks.poll_index_runs())
c.refresh_from_db()
print(c.get_workflow_status_display())    # → Prod: Minor Issues   ← THE FINISH LINE

# --- Outcome 3 (optional): an UNKNOWN state is a failure, never a success ---
c.workflow_status = WorkflowStatusChoices.TEST_INDEXING
c.save()
IndexDispatch.objects.create(collection=c, run_id="aurora-e2e-3", target="test",
                             task_arn="arn:demo", previous_workflow_status=WorkflowStatusChoices.CURATED)
with mock.patch.object(tasks, "fetch_run_status",
                       return_value={"state": "needs_confirmation", "error": None}):
    print(tasks.poll_index_runs())
c.refresh_from_db()
print(c.get_workflow_status_display())    # → Indexing Failed on Test
```

**Expect this** (all three observed on the 2026-08-14 run): `Test Indexing` held with the
validation report posted (caught Slack error on a dummy webhook); `Prod: Minor Issues` as the
finish line; `Indexing Failed on Test` for the unknown state. In Admin → **Index dispatches**
the `aurora-e2e-*` rows are read-only with `completed_at` stamped.

**Phase tests** — expect `19 passed`:

```bash
docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_indexing_dispatch.py -v
```

---

## The finish line — what you just proved

Open the collection's **Workflow History** tab. The full journey reads:

> … → Ready for Engineering → **Scraping Failed** *(Step 3: dispatch wiring, graceful failure)*
> → Engineering in Progress → **Scraping Successful** *(Step 4: real S3 ingest, CAS claim)*
> → **Ready for Curation** *(Step 4: migration + zero-delta diff)*
> → Curation in Progress → **Curated** *(Step 5: promote + test hand-off)*
> → **Indexing Failed on Test** *(Step 5: graceful failure = trigger proof)*
> → **Test Indexing** *(Step 7: simulated indexer success, validation posted)*
> → **QC: Minor Issues** → **Indexing Failed on Prod** *(Step 7: prod trigger proof)*
> → **Production Indexing** → **Prod: Minor Issues** *(Step 7: QC mirroring — done)*

Everything COSMOS-side ran for real: settings/credential plumbing (P0), the status vocabulary
(P1), inference-off migration (P2), dispatch triggers and job building (P3), real-S3 ingest with
claim semantics (P4), curation triggers and promote (P5), a Sinequa-free codebase (P6), and the
export/dispatch/poll machinery (P7). The only simulated piece was the indexer's `status.json`.
Its dev stacks are already deployed, so nothing further has to be built: fill a COSMOS
environment's `INDEXING_*` values from those stack outputs and Steps 5 and 7 stop failing
gracefully — this same collection is the natural first candidate for the fully-real closed loop.

The walkthrough is repeatable end to end: Step 4's ingest replaces dumps and re-diffs, promote
is idempotent, and each `IndexDispatch` gets a fresh `run_id`.

---

## Appendix A — Fully-offline ingest (no dev-AWS access)

If you can't reach the dev bucket, Step 4 can run with mocked S3 instead. The only S3 read in the
ingest path is `sde_collections/scraping/s3_results.py::_get_object` — patch it with an in-memory
fake and call the task synchronously.

> **⚠️ Use a scratch collection, never a real curated one.** The migration diffs the fake dump
> against the existing `CuratedUrl`s — on a collection with a real curated set, 5 fake documents
> produce a *deletion-marker delta for every real URL*. Create a throwaway collection in the
> admin (name + seed URL + division; `config_folder` auto-generates) and use its `config_folder`
> below.

```python
CONFIG_FOLDER = "<your scratch collection>"   # ⚠️ EDIT FIRST

import io, json
from datetime import datetime, timezone as tz
from unittest import mock
from botocore.exceptions import ClientError

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.tasks import ingest_scraped_collection

c = Collection.objects.get(config_folder=CONFIG_FOLDER)
c.workflow_status = WorkflowStatusChoices.ENGINEERING_IN_PROGRESS
c.save()

# 5 fake documents in the crawler's exact 7-field shape; URLs must be globally unique
DOCS = [
    {"url": f"https://{c.config_folder}.demo.local/page{i}",
     "title": f"Demo Page {i}", "full_text": f"Body text for demo page {i}.",
     "content_type": "text/html", "seed": "https://demo.local",
     "host": "demo.local", "depth": 1}
    for i in range(1, 6)
]
SUMMARY = {"collection_id": c.config_folder, "documents_scraped": len(DOCS)}

def fake_get_object(key):
    payload = {
        f"scraped_collections/{c.config_folder}.json": DOCS,
        f"failure_logs/{c.config_folder}_failures_summary.json": SUMMARY,
    }.get(key)
    if payload is None:
        raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
    return {"Body": io.BytesIO(json.dumps(payload).encode()),
            "LastModified": datetime.now(tz.utc)}

with mock.patch("sde_collections.scraping.s3_results._get_object", side_effect=fake_get_object):
    print(ingest_scraped_collection(c.id))   # → "Ingested 5 documents for …"

c.refresh_from_db()
print(c.get_workflow_status_display())   # → Scraping Successful; worker then → Ready for Curation
print(c.dump_urls.count())               # → 5
```

From there the walkthrough continues identically at Step 5 (you'll have 5 fake deltas to
"curate" instead of zero). The zero-document failure case: rerun with
`SUMMARY = {..., "documents_scraped": 0}` (status reset to *Engineering in Progress* first) →
**Scraping Failed**. Idempotency: rerun with `ingest_scraped_collection(c.id, claim=False)` —
twice yields 5 DumpUrls, not 10 (this is also what
`manage.py ingest_scrape_results --collection <cf>` calls; that command always reads real S3, so
locally it fails on the blank bucket by design).

---

## Appendix B — What this guide deliberately does NOT verify

These need real AWS beyond the crawler bucket. Nothing here is blocked on infrastructure — the
crawler stack and the indexer's dev stacks both exist — they are simply out of scope for a local
run, and are checked by hand against dev AWS instead:

- A real SSM `send-command` reaching the crawler inbox on `i-0b6a61d95888886f4` (the Step 3
  success path — its output for Aurorasaurus already exists, which is what Step 4 consumed).
- The real export → `sts:AssumeRole` → `ecs:RunTask` → `status.json` loop against
  `sde-cosmos-indexing-dev` (Step 5/7 success paths), which runs from a COSMOS host whose instance
  role may assume `CosmosIndexingDispatchRole-dev`.
- Slack delivery, if you ran with a dummy webhook.
- The stall-timeout paths in real time (both unit-tested; live simulation means waiting
  `SCRAPE_STALL_TIMEOUT_HOURS` / `INDEX_STALL_TIMEOUT_HOURS`).
- The beat pollers firing on schedule (`SCRAPE_POLL_ENABLED` / `INDEX_POLL_ENABLED=True`) — with
  blank buckets they would only log S3 errors; their rows' existence and flag-gating are
  verified in Steps 2/4/7.
