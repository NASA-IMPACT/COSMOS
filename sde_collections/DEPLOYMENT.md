# COSMOS CI/CD — Design

> Companion to [WORKFLOW.md](../WORKFLOW.md) (the curation pipeline) and
> [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) (phased delivery, where this is Phase 9).
> Database backup and restore are covered in [SQLDumpRestoration.md](../SQLDumpRestoration.md).

**This document is a design, not a runbook.** Nothing described under "Proposed pipeline" exists
in the repo. Deploys today are manual. Current state is recorded below and was verified against the
tree on 2026-08-11 — keep the two sections distinct as the design lands.

---

## Current state

| Area | What exists today |
|---|---|
| Deploy mechanism | Manual: `ssh` to the host, then rebuild in place. No deploy script, no image registry, no automation in the repo. |
| Branches | `dev`, `staging`, `production` all exist on `origin`. |
| CI | One workflow, `.github/workflows/run_full_test_suite.yml`, triggered **only** on PRs into `dev` (`paths-ignore: '**/*.md'`). |
| CI test runner | `init.sh` — finds every `test_*.py` and runs each in its **own** `coverage run --append -m pytest` process, counting failures. Excludes `document_classifier` and `functional_tests`. |
| Other workflows | `.github/workflows/issue-formatter.yml` (issue body templating). Nothing else. |
| Pre-commit | `.pre-commit-config.yaml` with black, isort, flake8, pyupgrade, bandit, mypy (excluded), and gitleaks. `pre-commit.ci` is enabled with weekly autoupdate. |
| Compose stacks | `local.yml` and `production.yml`. Four services share the Django image: `django`, `celeryworker`, `celerybeat`, `flower`. `production.yml` adds `traefik`, `postgres`, `awscli`. |
| Backup tooling | `manage.py database_backup` and `manage.py database_restore` exist in `sde_collections/management/commands/`. |
| Beat schedules | No `CELERY_BEAT_SCHEDULE` setting anywhere. All schedules are `django_celery_beat` **database rows**, written by a `post_migrate` receiver — today only `inference/signals.py`. |
| Credentials in code | AWS access is via static keys (`DJANGO_AWS_ACCESS_KEY_ID` / `DJANGO_AWS_SECRET_ACCESS_KEY`), not instance roles. Env files (`.envs/.production/.django`) are maintained by hand on each host. |
| Health endpoint | **None.** There is no `/healthz` or equivalent. |

### Two defects worth fixing regardless of CI/CD

1. **The gitleaks hook cannot run.** `.pre-commit-config.yaml` passes
   `--config=gitleaks-config.toml`, but that file does not exist and is not tracked. The hook
   fails rather than scanning. Either add the config or drop the argument to use gitleaks' defaults.
2. **A live production credential is committed.** `SQLDumpRestoration.md` contains the production
   Postgres password and the RDS endpoint hostname in the current `HEAD` (lines 101 and 117) — not
   only in history. **Rotate the credential, then scrub the file.** Rotation is the part that
   matters; history rewriting is optional once the secret is dead.

---

## Why automate this

Three reasons, in order of weight:

1. **The release path is untested.** CI runs only on PRs into `dev`. Merges into `staging` and
   `production` are exercised by nothing, so the branches that actually ship are the least verified.
2. **Manual deploys are not reversible.** `ssh` + rebuild-on-host leaves no artifact to roll back
   to and no record of what is running. Recovery means rebuilding from a guess about the last-good
   commit.
3. **The rewiring adds automated side effects.** Once [WORKFLOW.md](../WORKFLOW.md) lands, a
   workflow-status change dispatches an SSM command to a live EC2 crawler and triggers a Celery
   task that deletes and rebuilds a collection's `DumpUrl` rows. A bad deploy stops being a broken
   UI and becomes unwanted writes to shared infrastructure.

> The indexing pipeline (writes to the `sde-web` OpenSearch index) is **deferred** and likely lands
> in a separate repo. When it arrives, add its endpoints to `validate_deploy_env` and its
> reachability to `preflight_aws` — the hooks below are shaped to accept it, but do not write
> checks for machinery that is not here.

---

## Proposed pipeline

### Branch and environment model

```
feature branch ──PR──► dev ──PR──► staging ──PR──► production
                        │           │                 │
                        │           │                 └─► prod host    (manual approval)
                        │           └───────────────────► staging host (automatic)
                        └─ CI only
```

CI should run on pull requests into **all three** branches, closing the gap in point 1 above.

### Workflows

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | PR into `dev`, `staging`, `production` | `run-tests`, `django-checks` (`check --deploy`, `makemigrations --check --dry-run`) |
| `deploy-staging.yml` | push to `staging` | build → ECR → SSM → `scripts/deploy.sh --environment staging` |
| `deploy-production.yml` | push to `production` | staging-digest check → SSM → `scripts/deploy.sh --environment production` |
| `rollback.yml` | manual dispatch | redeploy a named image tag to either environment |
| `secret-scan-history.yml` | weekly + manual | full-history gitleaks, report-only |

`ci.yml` replaces `run_full_test_suite.yml`. Take the opportunity to drop the per-file loop in
`init.sh` and run `pytest` once — the loop spawns a process per test file and re-pays Django setup
each time, for no isolation benefit that `--reuse-db` does not already provide.

All `deploy-*` and `rollback` workflows gate on repository variable **`CD_ENABLED`**. Until it is
`true`, they skip. This lets the workflows merge and be reviewed before they can touch a host.

### What a deploy does

`scripts/deploy.sh` runs on the host and is the single definition of a deploy — GitHub Actions only
decides *when* to call it and *with which tag*. Order matters:

1. **Fetch the artifact** — pull the image from ECR (`--image-tag`), or check out and rebuild on the
   host (`--git-ref`, the fallback mode that needs no registry).
2. **Validate the environment** (`manage.py validate_deploy_env`) — *before* anything mutates.
   A host missing required settings must fail here, not inside a Celery task that has already
   half-completed its work.
3. **Back up** — `manage.py database_backup` plus an RDS snapshot. Production only.
4. **Migrate** — `manage.py migrate --noinput`.
5. **Swap containers** — `docker compose up -d`, recreating all four services that share the Django
   image. **`celerybeat` especially:** beat schedules are database rows written by `post_migrate`,
   and a beat process left running on the old schedule silently ignores them.
6. **Smoke checks** — `check --deploy`, `celery inspect ping`, an assertion that the expected
   `PeriodicTask` rows exist with the expected `enabled` state, and `manage.py preflight_aws`.
7. **On failure** — redeploy the previously recorded tag and post to Slack.

### Two new management commands

Both belong in `sde_collections/management/commands/`, alongside the existing backup commands.

- **`validate_deploy_env`** — fails fast when required settings are missing or contradictory.
  Once test and prod search endpoints exist, it must refuse a host where the two are identical;
  that misconfiguration would make the QC gate decorative while appearing to pass.
- **`preflight_aws`** — checks AWS reachability from the deployed host's own credentials
  (SSM to the crawler instance, S3 read on the crawler bucket, and later the search and embedding
  endpoints). Running it on every deploy stops it being a step someone remembers to do. It should
  report every check independently rather than aborting on the first failure.

### Prerequisite: a health endpoint

Smoke checks need one and the repo has none. Add a minimal `/healthz` view returning 200 plus a
database connectivity check. Keep it unauthenticated and cheap enough for a load balancer.

---

## Rollback

```bash
gh workflow run rollback.yml \
  -f environment=production \
  -f image_tag=sha-<previous> \
  -f git_sha=<previous-commit>
```

Migrations are **not** reversed. That is safe only while every migration is additive and
backward-compatible — old code ignoring new columns and new tables. The rewiring's migrations are
designed to hold that property, so rolling the image back is a complete rollback.

If a future migration breaks it (drops a column, renumbers an enum, backfills destructively), the PR
introducing it must say so, and rollback for that release becomes restore-from-backup instead.

---

## Prerequisites before enabling CD

| Item | Where |
|---|---|
| ECR repository | SMCE account, `us-east-1` |
| GitHub OIDC → IAM deploy role | secret `AWS_DEPLOY_ROLE_ARN` |
| SSM agent + instance role on both COSMOS hosts | verify with `aws ssm describe-instance-information` |
| Repo variables | `CD_ENABLED`, `AWS_REGION`, `ECR_REPOSITORY`, `STAGING_INSTANCE_ID`, `PRODUCTION_INSTANCE_ID`, `PRODUCTION_RDS_INSTANCE_ID` |
| GitHub Environment `production` | required reviewers configured |
| Branch protection | required checks on `dev`, `staging`, `production` (needs a repo admin) |

The **deploy role** needs `ecr:*` on the repository plus `ssm:SendCommand` and
`ssm:GetCommandInvocation` scoped to the two instances. The **hosts' own roles** need whatever the
curation pipeline uses — initially SSM to the crawler instance and S3 read on the crawler bucket.

Verify before flipping `CD_ENABLED`:

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=<cosmos-staging-instance-id>" \
  --query 'InstanceInformationList[0].PingStatus' --output text     # expect: Online
aws ecr describe-repositories --repository-names cosmos             # expect: no error
```

Then rehearse a rollback **on staging** before trusting it on production.

---

## Open questions

- **Credential model.** The codebase passes static AWS keys; this design assumes host instance
  roles. Pick one. Instance roles are the better target, but the migration has to be deliberate
  rather than a side effect of a deploy change.
- **Env-file source of truth.** `.envs/.production/.django` is hand-maintained per host, so
  `validate_deploy_env` can only check whatever that host happens to hold. Moving it to SSM
  Parameter Store or Secrets Manager and rendering it at deploy time would make the check meaningful.
- **Build-on-host vs registry.** The fallback `--git-ref` mode avoids standing up ECR entirely.
  If ECR is slow to obtain, shipping the fallback first is a viable staged path — it still gives a
  scripted, validated, reversible deploy.
