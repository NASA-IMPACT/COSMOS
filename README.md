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

### Loading Fixtures

To load collections:

```bash
$ docker-compose -f local.yml run --rm django python manage.py loaddata sde_collections/fixtures/collections.json
```

### Manually Creating and Loading a ContentTypeless Backup
Navigate to the server running prod, then to the project folder. Run the following command to create a backup:

```bash
docker-compose -f production.yml run --rm --user root django python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.Permission --indent 2 --output /app/backups/prod_backup-20240812.json
```
This will have saved the backup in a folder outside of the docker container. Now you can copy it to your local machine.

```bash
mv ~/prod_backup-20240812.json <project_path>/prod_backup-20240812.json
scp sde:/home/ec2-user/sde_indexing_helper/backups/prod_backup-20240812.json prod_backup-20240812.json
```

Finally, load the backup into your local database:

```bash
docker-compose -f local.yml run --rm django python manage.py loaddata prod_backup-20240812.json
```

### Loading the Database from an Arbitrary Backup

1. Build the project and run the necessary containers (as documented above).
2. Clear out content types using the Django shell:

```bash
$ docker-compose -f local.yml run --rm django python manage.py shell
>>> from django.contrib.contenttypes.models import ContentType
>>> ContentType.objects.all().delete()
>>> exit()
```

3. Load your backup database:

```bash
$ docker cp /path/to/your/backup.json container_name:/path/inside/container/backup.json
$ docker-compose -f local.yml run --rm django python manage.py loaddata /path/inside/the/container/backup.json
$ docker-compose -f local.yml run --rm django python manage.py migrate
```

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

1. Start with a [GitHub issue](https://github.com/NASA-IMPACT/sde-indexing-helper/issues).
2. Use the GitHub CLI to create branches and pull requests (`gh issue develop -c <issue_number>`).

## Job Creation

Eventually, job creation will be done seamlessly by the webapp. Until then, edit the `config.py` file with the details of what sources you want to create jobs for, then run `generate_jobs.py`.

## Code Structure for SDE_INDEXING_HELPER

- Frontend pages:
  - HTML: `/sde_indexing_helper/templates/`
  - JavaScript: `/sde_indexing_helper/static/js`
  - CSS: `/sde_indexing_helper/static/css`
  - Images: `/sde_indexing_helper/static/images`
