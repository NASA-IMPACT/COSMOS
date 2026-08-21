# COSMOS: Curated Organizational System for Metadata and Science

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

COSMOS is a web application designed to manage collections indexed in NASA's Science Discovery Engine (SDE), facilitating precise content selection and allowing metadata modification before indexing.

## How the pipeline works

A collection moves through scrape → curate → index. COSMOS orchestrates that flow but does not
crawl or index anything itself: it hands work to two external systems and watches S3 for results.
Every hop is a file in S3 plus a poller — there are no callbacks.

```
 COSMOS (Django + Celery)          crawl4ai host              sde-api-scrapers (ECS Fargate)
 ────────────────────────          ───────────────            ──────────────────────────────
 Ready for Engineering ──SSM──▶ crawl ──▶ S3
 Scraping Successful ◀──S3─── poll_scrape_jobs (5 min)
 Ready for Curation → (curator works in the UI)
 Curated ──S3 export + ecs:RunTask──────────────────────────▶ index into OpenSearch
 Test Indexing ◀──S3─── poll_index_runs (2 min) ◀────────────  status.json / validation.json
 QC: Perfect / QC: Minor Issues ──▶ prod run ──▶ Prod: Perfect / Prod: Minor Issues
```

The curator drives this by changing `workflow_status` in the admin; a `post_save` handler
(`sde_collections/models/collection.py::handle_workflow_status_change`) fires the matching Celery
task. Failures land on **Scraping Failed**, **Indexing Failed on Test**, or **Indexing Failed on
Prod** rather than silently stalling.

COSMOS holds no OpenSearch or SageMaker credentials. Chunking, vectorizing, indexing, and the QC
validation report all happen in the indexer repo (`sde-api-scrapers`). COSMOS only writes exports
to S3, assumes one IAM role, and calls `ecs:RunTask`.

### Where things are documented

| Doc | What it covers |
|---|---|
| [`WORKFLOW.md`](./WORKFLOW.md) | The curation workflow end to end, with a diagram |
| [`sde_collections/DEPLOYMENT.md`](./sde_collections/DEPLOYMENT.md) | How deploys actually work today, and the CI/CD gaps |
| [`LOCAL_VERIFICATION_GUIDE.md`](./LOCAL_VERIFICATION_GUIDE.md) | Verifying the pipeline locally, phase by phase |
| [`sde_collections/models/README_STATUS_TRIGGERS.md`](./sde_collections/models/README_STATUS_TRIGGERS.md) | What each status change triggers |
| [`sde_collections/models/README_LIFECYCLE.md`](./sde_collections/models/README_LIFECYCLE.md) | Dump → Delta → Curated URL lifecycle |

> **Note on configuration:** every setting that gates a dispatch (S3 buckets, ECS cluster, task
> family, IAM role ARN, subnets, security groups, and both `*_POLL_ENABLED` flags) defaults to
> blank or off in `config/settings/base.py`. Nothing dispatches until a host is explicitly wired.
> The pollers are `django_celery_beat` database rows written by a `post_migrate` receiver
> (`sde_collections/signals.py`), so enabling a poller requires `manage.py migrate` — restarting
> the services alone will not do it.

## Basic Commands

### Building the Project

```bash
$ docker-compose -f local.yml build
```

### Running the Necessary Containers

```bash
$ docker-compose -f local.yml up
```
### Non-Docker Local Setup

If you prefer to run the project without Docker, follow these steps:

#### Postgres Setup

```bash
$ psql postgres
postgres=# create database <some database>;
postgres=# create user <some username> with password '<some password>';
postgres=# grant all privileges on database <some database> to <some username>;

# This next one is optional, but it will allow the user to create databases for testing

postgres=# alter role <some username> with superuser;
```

#### Environment Variables

Copy `.env_sample` to `.env` and update the `DATABASE_URL` variable with your Postgres credentials.

```plaintext
DATABASE_URL='postgresql://<user>:<password>@localhost:5432/<database>'
```

Ensure `READ_DOT_ENV_FILE` is set to `True` in `config/settings/base.py`.

### Running the Application

```bash
$ python manage.py runserver
```

Run initial migration if necessary:

```bash
$ python manage.py migrate
```

### Setting Up Users

#### Creating a Superuser Account

```bash
$ docker-compose -f local.yml run --rm django python manage.py createsuperuser
```

#### Creating Additional Users

Create additional users through the admin interface (/admin).
## Database Backup and Restore

COSMOS provides dedicated management commands for backing up and restoring your PostgreSQL database. These commands handle both compressed and uncompressed backups and work seamlessly in both local and production environments using Docker.

### Backup Directory Structure

All backups are stored in the `/backups` directory at the root of your project. This directory is mounted as a volume in both local and production Docker configurations, making it easy to manage backups across different environments.

- Local development: `./backups/`
- Production server: `/path/to/project/backups/`

If the directory doesn't exist, create it:
```bash
mkdir backups
```

### Creating a Database Backup

To create a backup of your database:

```bash
# Create a compressed backup (recommended)
docker-compose -f local.yml run --rm django python manage.py database_backup

# Create an uncompressed backup
docker-compose -f local.yml run --rm django python manage.py database_backup --no-compress

# Specify custom output location within backups directory
docker-compose -f local.yml run --rm django python manage.py database_backup --output my_custom_backup.sql
```

The backup command will automatically:
- Detect your server environment (Production/Staging/Local)
- Use database credentials from your environment settings
- Generate a dated filename if no output path is specified
- Save the backup to the mounted `/backups` directory
- Compress the backup by default (can be disabled with --no-compress)

### Restoring from a Database Backup

To restore your database from a backup, it will need to be in the `/backups` directory. You can then run the following command:

```bash
# Restore from a backup (handles both .sql and .sql.gz files)
docker-compose -f local.yml run --rm django python manage.py database_restore backups/backup_file_name.sql.gz
```

The restore command will:
- Automatically detect if the backup is compressed (.gz)
- Terminate existing database connections
- Drop and recreate the database
- Restore all data from the backup
- Handle all database credentials from your environment settings

### Working with Remote Servers

When working with production or staging servers:

1. First, SSH into the appropriate server:
```bash
# For production
ssh user@production-server
cd /path/to/project
```

2. Create a backup on the remote server:
```bash
docker-compose -f production.yml run --rm django python manage.py database_backup
```

3. Copy the backup from the remote server's backup directory to your local machine:
```bash
scp user@remote-server:/path/to/project/backups/backup_name.sql.gz ./backups/
```

4. Restore locally:
```bash
docker-compose -f local.yml run --rm django python manage.py database_restore backups/backup_name.sql.gz
```

### Alternative Methods

While the database_backup and database_restore commands are the recommended approach, you can also use Django's built-in fixtures for smaller datasets:

```bash
# Create a backup excluding content types
docker-compose -f production.yml run --rm django python manage.py dumpdata \
    --natural-foreign --natural-primary \
    --exclude=contenttypes --exclude=auth.Permission \
    --indent 2 \
    --output backups/prod_backup-$(date +%Y%m%d).json

# Restore from a fixture
docker-compose -f local.yml run --rm django python manage.py loaddata backups/backup_name.json
```

Note: For large databases (>1.5GB), the database_backup and database_restore commands are strongly recommended over JSON fixtures as they handle large datasets more efficiently.

## Additional Commands

### Type Checks

```bash
$ mypy sde_indexing_helper
```

### Test Coverage

To run tests and check coverage:

```bash
$ coverage run -m pytest
$ coverage html
$ open htmlcov/index.html
```

#### Running Tests with Pytest

```bash
$ pytest
```

### Live Reloading and Sass CSS Compilation

Refer to the [Cookiecutter Django documentation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Installing Celery

```bash
$ pip install celery
```

### Running a Celery Worker

Run these from the **repository root** — the folder containing `manage.py` and `config/`. For
Celery's import magic to work, the working directory matters.

```bash
$ celery -A config.celery_app worker -l info
```

### Running Celery Beat Scheduler

```bash
$ celery -A config.celery_app beat
```

Note that beat schedules in this project are `django_celery_beat` **database rows**, not a
`CELERY_BEAT_SCHEDULE` setting — see the configuration note at the top of this file.

### Pre-Commit Hook Instructions

To install pre-commit hooks:

```bash
$ pip install pre-commit
$ pre-commit install
$ pre-commit run --all-files
```
For detailed information on the coding standards and conventions we enforce, please see our [Coding Standards and Conventions](CODE_STANDARDS.md).

### Sentry Setup

Sign up for a free account at [Sentry](https://sentry.io/signup/?code=cookiecutter) and set the DSN URL in production.

## Deployment

See [`sde_collections/DEPLOYMENT.md`](./sde_collections/DEPLOYMENT.md) for how deploys work on this
project — the compose stacks, the branch flow (`dev` → `staging` → `production`), the hand-maintained
per-host env files, and the current CI/CD gaps. Deployment is manual today: SSH to the host and
rebuild in place.

Background on the underlying Docker setup is in the
[Cookiecutter Django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

## Adding New Features/Fixes

We welcome contributions to improve the project! Before you begin, please take a moment to review our [Contributing Guidelines](./CONTRIBUTING.md). These guidelines will help you understand the process for submitting new features, bug fixes, and other improvements.

## Dispatching a Scrape

Scrapes are normally triggered by setting a collection's `workflow_status` to **Ready for
Engineering** in the admin, which dispatches a job to the crawl4ai host over AWS SSM.

To dispatch one by hand:

```shell
docker-compose -f local.yml run --rm django python manage.py dispatch_scrape --collection <config_folder>
```

Results are picked up automatically by the `poll_scrape_jobs` beat task (every 5 minutes, gated by
`SCRAPE_POLL_ENABLED`). To ingest a completed scrape manually instead:

```shell
docker-compose -f local.yml run --rm django python manage.py ingest_scrape_results --collection <config_folder>
```

## Code Structure

The Django project package is still named `sde_indexing_helper/` (COSMOS is the product name; the
package was not renamed).

- Frontend pages:
  - HTML: `/sde_indexing_helper/templates/`
  - JavaScript: `/sde_indexing_helper/static/js`
  - CSS: `/sde_indexing_helper/static/css`
  - Images: `/sde_indexing_helper/static/images`

- Pipeline code, all under `sde_collections/`:
  - `scraping/` — dispatching crawls and reading their results:
    `job_builder.py` (job JSON), `ssm_dispatch.py` (SSM send-command to the crawl4ai host),
    `s3_results.py` (freshness checks and result fetch)
  - `indexing/` — the hand-off to the indexer:
    `export.py` (writes `documents.jsonl`, then `manifest.json` last),
    `dispatch.py` (`sts:AssumeRole` → `ecs:RunTask`), `run_status.py` (reads `status.json`)
  - `tasks.py` — the Celery tasks, including both pollers
  - `signals.py` — the `post_migrate` receiver that writes the beat schedule rows
  - `models/` — collections, URL lifecycle, and patterns (see the `README_*.md` files there)


## Running Long Scripts on the Server
```shell
tmux new -s docker_django
```
Once you are inside, you can run dmshell or for example a managment command:

```shell
docker-compose -f production.yml run --rm django python manage.py deduplicate_urls
```

Later, you can do this to get back in.
```shell
tmux attach -t docker_django
```

To delete the session:
```shell
tmux kill-session -t docker_django
```
