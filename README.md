# SDE Indexing Helper

Web application to keep track of collections indexed in SDE and help decide what exactly to index from each collection.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Building The Project

    ```bash
    $ docker-compose -f local.yml build
    ```

### Running The Necessary Containers

    ```bash
    $ docker-compose -f local.yml up
    ```

### Non-docker Local Setup

If you want to run the project without docker, you will need the following:

- Postgres

Run the following commands:

````
$ psql postgres
postgres=# create database <some database>;
postgres=# create user <some username> with password '<some password>';
postgres=# grant all privileges on database <some database> to <some username>;

# This next one is optional, but it will allow the user to create databases for testing

postgres=# alter role <some username> with superuser;
```

Now copy .env_sample in the root directory to .env. Note that in this setup we don't end up using the .envs/ directory, but instead we use the .env file.

Replace the variables in this line in the .env file: `DATABASE_URL='postgresql://<user>:<password>@localhost:5432/<database>'` with your user, password and database. Change the port if you have a different one.

You don't need to change any other variable, unless you want to use specific modules (like the GitHub code will require a GitHub token etc).

There is a section in `config/settings/base.py` which reads environment variables from this file. The line should look like `READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)`. Make sure either the default is True here (which it should already be), or run `export DJANGO_READ_DOT_ENV_FILE=True` in your terminal.

Run `python manage.py runserver` to test if your setup worked. You might have to run an initial migration with `python manage.py migrate`.

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:
    ```bash
    $ docker-compose -f local.yml run -rm django python manage.py createsuperuser
    ```

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Loading fixtures
Please note that currently loading fixtures will not create a fully working database. If you are starting the project from scratch, it is probably preferable to skip to the Loading the DB from a Backup section.
- To load collections
    ```bash
    $ docker-compose -f local.yml run --rm django python manage.py loaddata sde_collections/fixtures/collections.json
    ```

### Loading scraped URLs into CandidateURLs

- First make sure there is a folder in scraper/scraped_urls. There should already be an example folder.

- Then create a new spider for your Collection. An example is mast_spider.py in spiders. In the future, this will be replaced by base_spider.py

- Run the crawler with `scrapy crawl <name of your spider> -o scraped_urls/<config_folder>/urls.jsonl

- Then run this:
    ```bash
    $ docker-compose -f local.yml run --rm django python manage.py load_scraped_urls <config_folder_name>
    ```

### Loading The DB From A Backup

- If a database backup is made available, you wouldn't have to load the fixtures or the scrapped URLs anymore. This changes a few steps necessary to get the project running.

- Step 1 : Build the project (Documented Above)

- Step 2 : Run the necessary containers (Documented Above)

- Step 3 : Clear Out Contenet Types Using Django Shell

    -- Enter the Django shell in your Docker container.
        ```bash
        $ docker-compose -f local.yml run --rm django python manage.py shell
        ```

    -- In the Django shell, you can now delete the content types.
        ```bash
        from django.contrib.contenttypes.models import ContentType
        ContentType.objects.all().delete()
        ```

    -- Exit the shell.

- Step 4 : Load Your Backup Database

    Assuming your backup is a `.json` file from `dumpdata`, you'd use `loaddata` command to populate your database.

    -- If the backup file is on the local machine, make sure it's accessible to the Docker container. If the backup is outside the container, you will need to copy it inside first.
        ```bash
        $ docker cp /path/to/your/backup.json container_name:/path/inside/container/backup.json
        ```

    -- Load the data from your backup.
        ```bash
        $ docker-compose -f local.yml run --rm django python manage.py loaddata /path/inside/the/container/backup.json
        ```

    -- Once loaded, you may want to run migrations to ensure everything is aligned.
        ```bash
        $ docker-compose -f local.yml run -rm django python manage.py migrate
        ```


### Type checks

Running type checks with mypy:
    ```bash
    $ mypy sde_indexing_helper
    ```

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:
    ```bash
    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html
    ```

#### Running tests with pytest

    ```bash
    $ pytest
    ```

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Install Celery

Make sure Celery is installed in your environment. To install :
    ```bash
    $ pip install celery
    ```

### Install all requirements

Install all packages listed in a 'requirements' file
    ```bash
    pip install -r requirements/*.txt
    ```

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd sde_indexing_helper
celery -A config.celery_app worker -l info
````

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd sde_indexing_helper
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd sde_indexing_helper
celery -A config.celery_app worker -B -l info
```

### Pre-Commit Hook Instructions

Hooks have to be run on every commit to automatically take care of linting and structuring.

To install pre-commit package manager :

    ```bash
    $ pip install pre-commit
    ```

Install the git hook scripts :

    ```bash
    $ pre-commit install
    ```

Run against the files :

    ```bash
    $ pre-commit run --all-files
    ```

    It's usually a good idea to run the hooks against all of the files when adding new hooks (usually `pre-commit` will only run on the chnages files during git hooks).

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).

### How to import candidate URLs from the test server

Documented [here](https://github.com/NASA-IMPACT/sde-indexing-helper/wiki/How-to-bring-in-Candidate-URLs-from-the-test-server).

## Adding New Features/Fixes

New features and bugfixes should start with a [GitHub issue](https://github.com/NASA-IMPACT/sde-indexing-helper/issues). Then on local, ensure that you have the [GitHub CLI](https://cli.github.com/). Branches are made based off of existing issues, and no other way. Use the CLI to reference your issue number, like so `gh issue develop -c <issue_number>`. This will create a local branch linked to the issue, and allow GitHub to handle all the relevant linking.

Once on the branch, create a PR with `gh pr create`. You can leave the PR in draft if it's still WIP. When done, take it out of draft with `gh pr ready`.

## Job Creation

Eventually, job creation will be done seamlessly by the webapp. Until then, edit the `config.py` file with the details of what sources you want to create jobs for, then run `generate_jobs.py`.
