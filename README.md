# COSMOS: Curated Organizational System for Metadata and Science

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

COSMOS is a web application designed to manage collections indexed in NASA's Science Discovery Engine (SDE), facilitating precise content selection and allowing metadata modification before indexing.

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

### Database Backup and Restore

COSMOS provides dedicated management commands for backing up and restoring your PostgreSQL database. These commands handle both compressed and uncompressed backups and automatically detect your server environment from your configuration.

#### Creating a Database Backup

To create a backup of your database:

```bash
# Create a compressed backup (recommended)
docker-compose -f local.yml run --rm django python manage.py database_backup

# Create an uncompressed backup
docker-compose -f local.yml run --rm django python manage.py database_backup --no-compress

# Specify custom output location
docker-compose -f local.yml run --rm django python manage.py database_backup --output /path/to/output.sql
```

The backup command will automatically:
- Detect your server environment (Production/Staging/Local)
- Use database credentials from your environment settings
- Generate a dated filename if no output path is specified
- Compress the backup by default (can be disabled with --no-compress)

#### Restoring from a Database Backup

To restore your database from a backup:

```bash
# Restore from a backup (handles both .sql and .sql.gz files)
docker-compose -f local.yml run -v local/path/to/directory:/backups --rm django python manage.py database_restore /backups/backup_file_name.sql[.gz]
```

The restore command will:
- Automatically detect if the backup is compressed (.gz)
- Terminate existing database connections
- Drop and recreate the database
- Restore all data from the backup
- Handle all database credentials from your environment settings

#### Working with Remote Servers

When working with production or staging servers:

1. First, SSH into the appropriate server:
```bash
# For production
ssh user@production-server
cd /path/to/project

# For staging
ssh user@staging-server
cd /path/to/project
```

2. Then run the backup command with the production configuration:
```bash
docker-compose -f production.yml run --rm django python manage.py database_backup
```

3. Copy the backup to your local machine:
```bash
scp user@remote-server:/path/to/backup.sql.gz ./local-backup.sql.gz
```

4. Finally, restore locally:
```bash
docker-compose -f local.yml run --rm django python manage.py database_restore local-backup.sql.gz
```

#### Alternative Methods

While the database_backup and database_restore commands are the recommended approach, there are alternative methods available:

##### Using JSON Fixtures (for smaller datasets)
If you're working with a smaller dataset, you can use Django's built-in fixtures:

```bash
# Create a backup excluding content types
docker-compose -f production.yml run --rm --user root django python manage.py dumpdata \
    --natural-foreign --natural-primary \
    --exclude=contenttypes --exclude=auth.Permission \
    --indent 2 \
    --output /app/backups/prod_backup-$(date +%Y%m%d).json

# Restore from a fixture
docker-compose -f local.yml run --rm django python manage.py loaddata /path/to/backup.json
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

```bash
$ cd sde_indexing_helper
$ celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important where the celery commands are run. If you are in the same folder with manage.py, you should be right.

### Running Celery Beat Scheduler

```bash
$ cd sde_indexing_helper
$ celery -A config.celery_app beat
```

### Pre-Commit Hook Instructions

To install pre-commit hooks:

```bash
$ pip install pre-commit
$ pre-commit install
$ pre-commit run --all-files
```

### Sentry Setup

Sign up for a free account at [Sentry](https://sentry.io/signup/?code=cookiecutter) and set the DSN URL in production.

## Deployment

Refer to the detailed [Cookiecutter Django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

## Importing Candidate URLs from the Test Server

Documented [here](https://github.com/NASA-IMPACT/sde-indexing-helper/wiki/How-to-bring-in-Candidate-URLs-from-the-test-server).

## Adding New Features/Fixes

We welcome contributions to improve the project! Before you begin, please take a moment to review our [Contributing Guidelines](./CONTRIBUTING.md). These guidelines will help you understand the process for submitting new features, bug fixes, and other improvements.

## Job Creation

Eventually, job creation will be done seamlessly by the webapp. Until then, edit the `config.py` file with the details of what sources you want to create jobs for, then run `generate_jobs.py`.

## Code Structure for SDE_INDEXING_HELPER

- Frontend pages:
  - HTML: `/sde_indexing_helper/templates/`
  - JavaScript: `/sde_indexing_helper/static/js`
  - CSS: `/sde_indexing_helper/static/css`
  - Images: `/sde_indexing_helper/static/images`


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
