# SDE Indexing Helper

Web application to keep track of collections indexed in SDE and help decide what exactly to index from each collection.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Loading fixtures

- To load collections

      docker-compose -f local.yml run --rm django python manage.py loaddata sde_collections/fixtures/collections.json

### Loading scraped URLs into CandidateURLs

- First make sure there is a folder in scraper/scraped_urls. There should already be an example folder.

- Then create a new spider for your Collection. An example is mast_spider.py in spiders. In the future, this will be replaced by base_spider.py

- Run the crawler with `scrapy crawl <name of your spider> -o scraped_urls/<config_folder>/urls.jsonl

- Then run this:

      $ docker-compose -f local.yml run --rm django python manage.py load_scraped_urls <config_folder_name>

### Type checks

Running type checks with mypy:

    $ mypy sde_indexing_helper

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Install Celery

Make sure Celery is installed in your environment.
To install,
pip install celery

### Install all requirements

Install all packages listed in a 'requirements' file

    pip install -r requirements/*.txt

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd sde_indexing_helper
celery -A config.celery_app worker -l info
```

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

editing readme here
