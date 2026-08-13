# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_inference_flag.py

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import override_settings

from inference.models import InferenceJob
from inference.signals import create_periodic_tasks
from inference.tasks import process_inference_job_queue
from sde_collections.models.collection import Collection
from sde_collections.tests.factories import CollectionFactory

TDAMM_FOLDER = "imagine_the_universe"

# These tests call the REAL queue_necessary_classifications (patching only the migration
# task's delay) — patching the whole method, as the older trigger tests do, would guard
# nothing about the flag behaviour.


def _collection_with_folder(config_folder):
    collection = CollectionFactory()
    Collection.objects.filter(id=collection.id).update(config_folder=config_folder)
    collection.refresh_from_db()
    return collection


@pytest.mark.django_db
@override_settings(INFERENCE_ENABLED=False)
@patch("sde_collections.models.collection.migrate_dump_to_delta_and_handle_status_transistions.delay")
def test_tdamm_collection_migrates_directly_when_inference_disabled(mock_migrate):
    """Regression guard: with the flag off, a TDAMM-listed collection must NOT get an
    InferenceJob (it would queue forever and never reach Ready for Curation)."""
    collection = _collection_with_folder(TDAMM_FOLDER)

    collection.queue_necessary_classifications()

    mock_migrate.assert_called_once_with(collection.id)
    assert not InferenceJob.objects.filter(collection=collection).exists()


@pytest.mark.django_db
@override_settings(INFERENCE_ENABLED=False)
@patch("sde_collections.models.collection.migrate_dump_to_delta_and_handle_status_transistions.delay")
def test_regular_collection_migrates_directly_when_inference_disabled(mock_migrate):
    collection = _collection_with_folder("some_regular_collection")

    collection.queue_necessary_classifications()

    mock_migrate.assert_called_once_with(collection.id)
    assert not InferenceJob.objects.filter(collection=collection).exists()


@pytest.mark.django_db
@override_settings(INFERENCE_ENABLED=True)
@patch("sde_collections.models.collection.migrate_dump_to_delta_and_handle_status_transistions.delay")
def test_tdamm_collection_creates_inference_job_when_enabled(mock_migrate):
    collection = _collection_with_folder(TDAMM_FOLDER)

    collection.queue_necessary_classifications()

    assert InferenceJob.objects.filter(collection=collection).exists()
    mock_migrate.assert_not_called()


def _run_post_migrate_handler():
    create_periodic_tasks(sender=SimpleNamespace(name="inference"))


@pytest.mark.django_db
@pytest.mark.parametrize("flag", [False, True])
def test_periodic_task_rows_follow_the_flag(flag):
    from django_celery_beat.models import PeriodicTask

    with override_settings(INFERENCE_ENABLED=flag):
        _run_post_migrate_handler()

    rows = PeriodicTask.objects.filter(task="inference.tasks.process_inference_job_queue")
    assert rows.count() == 2
    assert all(row.enabled is flag for row in rows)


@pytest.mark.django_db
@override_settings(INFERENCE_ENABLED=False)
def test_periodic_task_disable_survives_re_migrate():
    """A hand-enable in the admin must not survive a deploy's migrate step: the signal
    re-asserts enabled from the flag on every post_migrate."""
    from django_celery_beat.models import PeriodicTask

    _run_post_migrate_handler()
    PeriodicTask.objects.filter(task="inference.tasks.process_inference_job_queue").update(enabled=True)

    _run_post_migrate_handler()

    rows = PeriodicTask.objects.filter(task="inference.tasks.process_inference_job_queue")
    assert rows.count() == 2
    assert all(row.enabled is False for row in rows)


@override_settings(INFERENCE_ENABLED=False)
def test_process_inference_job_queue_short_circuits_when_disabled():
    """Belt and braces: even a manually-triggered run must refuse to process the queue.
    (No django_db marker: the early return must not touch the database at all.)"""
    assert process_inference_job_queue() == "Inference pipeline disabled (INFERENCE_ENABLED=False)"
