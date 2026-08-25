# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_signals.py

from types import SimpleNamespace

import pytest
from django.test import override_settings

from sde_collections.signals import (
    POLL_INDEX_TASK,
    POLL_INDEX_TASK_NAME,
    POLL_SCRAPE_TASK,
    POLL_SCRAPE_TASK_NAME,
    create_periodic_tasks,
)


def _run_post_migrate_handler(app_label="sde_collections"):
    create_periodic_tasks(sender=SimpleNamespace(name=app_label))


def _rows():
    from django_celery_beat.models import PeriodicTask

    return {row.name: row for row in PeriodicTask.objects.filter(task__in=[POLL_SCRAPE_TASK, POLL_INDEX_TASK])}


@pytest.mark.django_db
@pytest.mark.parametrize("scrape_flag,index_flag", [(False, False), (True, False), (False, True), (True, True)])
def test_poller_rows_follow_their_flags(scrape_flag, index_flag):
    with override_settings(SCRAPE_POLL_ENABLED=scrape_flag, INDEX_POLL_ENABLED=index_flag):
        _run_post_migrate_handler()

    rows = _rows()
    assert rows[POLL_SCRAPE_TASK_NAME].enabled is scrape_flag
    assert rows[POLL_SCRAPE_TASK_NAME].crontab.minute == "*/5"
    assert rows[POLL_INDEX_TASK_NAME].enabled is index_flag
    assert rows[POLL_INDEX_TASK_NAME].crontab.minute == "*/2"


@pytest.mark.django_db
@override_settings(SCRAPE_POLL_ENABLED=False, INDEX_POLL_ENABLED=False)
def test_flag_is_reasserted_on_every_migrate():
    """The flag, not an admin hand-edit, is the source of truth: a hand-enable is
    reverted by the next deploy's migrate step (and vice versa)."""
    from django_celery_beat.models import PeriodicTask

    _run_post_migrate_handler()
    PeriodicTask.objects.filter(task__in=[POLL_SCRAPE_TASK, POLL_INDEX_TASK]).update(enabled=True)

    _run_post_migrate_handler()

    assert all(row.enabled is False for row in _rows().values())
    assert len(_rows()) == 2  # updated in place, never duplicated


@pytest.mark.django_db
@override_settings(SCRAPE_POLL_ENABLED=True, INDEX_POLL_ENABLED=True)
def test_handler_ignores_other_apps():
    from django_celery_beat.models import PeriodicTask

    # Test-DB setup already ran the real post_migrate; start from a clean slate.
    PeriodicTask.objects.filter(task__in=[POLL_SCRAPE_TASK, POLL_INDEX_TASK]).delete()

    _run_post_migrate_handler(app_label="inference")

    assert _rows() == {}
