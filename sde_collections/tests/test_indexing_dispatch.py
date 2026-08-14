# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_indexing_dispatch.py

import io
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.test import override_settings
from django.utils import timezone

from sde_collections.indexing.dispatch import run_index_task
from sde_collections.indexing.export import export_curated_to_s3
from sde_collections.indexing.run_status import (
    fetch_run_status,
    fetch_validation_report,
)
from sde_collections.models.collection_choice_fields import (
    Divisions,
    DocumentTypes,
    WorkflowStatusChoices,
)
from sde_collections.models.delta_patterns import DeltaExcludePattern
from sde_collections.models.indexing import IndexDispatch
from sde_collections.tasks import (
    index_collection_to_prod,
    index_collection_to_test,
    poll_index_runs,
)
from sde_collections.tests.factories import CollectionFactory, CuratedUrlFactory

RUN_ID = "2026-08-13T20-00-00Z-abc123"

INDEXING_SETTINGS = dict(
    SDE_INDEX_BUCKET="sde-cosmos-indexing-dev",
    INDEXING_ECS_CLUSTER="api-scrapers-cluster-dev",
    INDEXING_TASK_FAMILY="web_cosmos-scraper-dev",
    INDEXING_DISPATCH_ROLE_ARN="arn:aws:iam::998871305517:role/CosmosIndexingDispatchRole-dev",
)


class ExportCapture:
    """Mock S3 client capturing the export write sequence and payloads."""

    def __init__(self):
        self.calls = []  # ordered (kind, key)
        self.jsonl_lines = None
        self.manifest = None
        self.client = MagicMock()
        self.client.upload_fileobj.side_effect = self._upload_fileobj
        self.client.put_object.side_effect = self._put_object

    def _upload_fileobj(self, fileobj, bucket, key):
        content = fileobj.read().decode("utf-8")
        self.jsonl_lines = [json.loads(line) for line in content.splitlines() if line]
        self.calls.append(("documents", key))

    def _put_object(self, Bucket, Key, Body, **kwargs):
        self.manifest = json.loads(Body)
        self.calls.append(("manifest", Key))


@pytest.fixture
def s3_export():
    capture = ExportCapture()
    session = MagicMock()
    session.client.return_value = capture.client
    with patch("sde_collections.indexing.export.get_boto3_session", return_value=session):
        yield capture


@pytest.mark.django_db
class TestExportCuratedToS3:
    @pytest.fixture(autouse=True)
    def indexing_settings(self):
        with override_settings(**INDEXING_SETTINGS):
            yield

    def test_manifest_written_last_with_exact_count_and_keys(self, s3_export):
        collection = CollectionFactory()
        CuratedUrlFactory.create_batch(3, collection=collection)

        count = export_curated_to_s3(collection, "test", RUN_ID)

        assert count == 3
        assert [kind for kind, _ in s3_export.calls] == ["documents", "manifest"]
        prefix = f"curated_collections/{collection.config_folder}/{RUN_ID}"
        assert s3_export.calls[0][1] == f"{prefix}/documents.jsonl"
        assert s3_export.calls[1][1] == f"{prefix}/manifest.json"
        assert s3_export.manifest["document_count"] == 3
        assert s3_export.manifest["collection_key"] == collection.config_folder
        assert s3_export.manifest["run_id"] == RUN_ID
        assert s3_export.manifest["target"] == "test"
        assert s3_export.manifest["schema_version"] == 1

    def test_excluded_urls_are_not_exported(self, s3_export):
        collection = CollectionFactory()
        CuratedUrlFactory(collection=collection, url="https://keep.nasa.gov/a")
        excluded_url = CuratedUrlFactory(collection=collection, url="https://exclude.nasa.gov/b")
        pattern = DeltaExcludePattern.objects.create(collection=collection, match_pattern="https://exclude.nasa.gov/b")
        # The excluded annotation reads this M2M; population is the pattern system's job
        # (covered in test_promote_collection) — here we only care that export honours it.
        pattern.curated_urls.add(excluded_url)

        count = export_curated_to_s3(collection, "test", RUN_ID)

        assert count == 1
        assert s3_export.manifest["document_count"] == 1
        assert [line["url"] for line in s3_export.jsonl_lines] == ["https://keep.nasa.gov/a"]

    def test_title_and_label_resolution(self, s3_export):
        collection = CollectionFactory(division=Divisions.ASTROPHYSICS, document_type=DocumentTypes.DATA)
        CuratedUrlFactory(
            collection=collection,
            generated_title="Generated wins",
            scraped_title="Scraped loses",
            document_type=DocumentTypes.IMAGES,  # differs from collection default -> exported
            division=Divisions.ASTROPHYSICS,  # equals collection default -> omitted
        )

        export_curated_to_s3(collection, "test", RUN_ID)

        line = s3_export.jsonl_lines[0]
        assert line["title"] == "Generated wins"
        assert line["document_type"] == "Images"  # label, not the int
        assert "division" not in line
        assert line["is_metadata_viewer"] is False
        assert s3_export.manifest["division"] == "Astrophysics"
        assert s3_export.manifest["document_type"] == "Data"

    @override_settings(SDE_INDEX_BUCKET="")
    def test_blank_bucket_refuses_to_export(self, s3_export):
        collection = CollectionFactory()

        with pytest.raises(ValueError, match="SDE_INDEX_BUCKET"):
            export_curated_to_s3(collection, "test", RUN_ID)


@pytest.mark.django_db
class TestRunIndexTask:
    def test_unconfigured_settings_refuse_to_dispatch(self):
        """Dev-only guard: with the blank defaults, no dispatch can leave the box."""
        collection = CollectionFactory()

        with pytest.raises(ValueError, match="INDEXING_DISPATCH_ROLE_ARN"):
            run_index_task(collection, "test", RUN_ID)

    @override_settings(**INDEXING_SETTINGS)
    @patch("sde_collections.indexing.dispatch.boto3.client")
    @patch("sde_collections.indexing.dispatch.get_boto3_session")
    def test_dispatch_assumes_role_and_runs_task(self, mock_session, mock_boto3_client):
        collection = CollectionFactory()
        sts = MagicMock()
        sts.assume_role.return_value = {
            "Credentials": {"AccessKeyId": "AK", "SecretAccessKey": "SK", "SessionToken": "TOK"}
        }
        mock_session.return_value.client.return_value = sts
        ecs = MagicMock()
        ecs.run_task.return_value = {"tasks": [{"taskArn": "arn:aws:ecs:task/1"}], "failures": []}
        mock_boto3_client.return_value = ecs

        arn = run_index_task(collection, "test", RUN_ID)

        assert arn == "arn:aws:ecs:task/1"
        assert sts.assume_role.call_args.kwargs["RoleArn"] == INDEXING_SETTINGS["INDEXING_DISPATCH_ROLE_ARN"]
        run_kwargs = ecs.run_task.call_args.kwargs
        assert run_kwargs["cluster"] == "api-scrapers-cluster-dev"
        assert run_kwargs["taskDefinition"] == "web_cosmos-scraper-dev"
        command = run_kwargs["overrides"]["containerOverrides"][0]["command"]
        # The executable must lead the list: a container override replaces the task
        # definition's command wholesale, and the indexer image has no ENTRYPOINT.
        assert command == [
            "python3",
            "api_scraper.py",
            "--source",
            "WEB_COSMOS",
            "--collection",
            collection.config_folder,
            "--target",
            "test",
            "--run-id",
            RUN_ID,
        ]

    @override_settings(**INDEXING_SETTINGS)
    @patch("sde_collections.indexing.dispatch.boto3.client")
    @patch("sde_collections.indexing.dispatch.get_boto3_session")
    def test_runtask_failures_raise(self, mock_session, mock_boto3_client):
        collection = CollectionFactory()
        mock_session.return_value.client.return_value.assume_role.return_value = {
            "Credentials": {"AccessKeyId": "AK", "SecretAccessKey": "SK", "SessionToken": "TOK"}
        }
        mock_boto3_client.return_value.run_task.return_value = {
            "tasks": [],
            "failures": [{"reason": "MISSING"}],
        }

        with pytest.raises(RuntimeError, match="failures"):
            run_index_task(collection, "test", RUN_ID)


@pytest.mark.django_db
class TestIndexDispatchTasks:
    @patch("sde_collections.tasks.run_index_task", return_value="arn:aws:ecs:task/1")
    @patch("sde_collections.tasks.export_curated_to_s3", return_value=25)
    def test_test_dispatch_records_and_sets_status(self, mock_export, mock_run):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.CURATED)

        run_id = index_collection_to_test(collection.id)

        dispatch = IndexDispatch.objects.get(collection=collection)
        assert dispatch.run_id == run_id
        assert dispatch.target == "test"
        assert dispatch.task_arn == "arn:aws:ecs:task/1"
        assert dispatch.previous_workflow_status == WorkflowStatusChoices.CURATED
        assert dispatch.completed_at is None
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.TEST_INDEXING
        # export happens before dispatch, with the same run_id
        assert mock_export.call_args.args[1] == "test"
        assert mock_export.call_args.args[2] == run_id

    @patch("sde_collections.tasks.run_index_task")
    @patch("sde_collections.tasks.export_curated_to_s3", side_effect=Exception("S3 down"))
    def test_export_failure_lands_on_failed_status_without_raising(self, mock_export, mock_run):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.CURATED)

        assert index_collection_to_test(collection.id) is None

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.INDEXING_FAILED_ON_TEST
        assert not IndexDispatch.objects.filter(collection=collection).exists()
        mock_run.assert_not_called()

    @patch("sde_collections.tasks.run_index_task")
    @patch("sde_collections.tasks.export_curated_to_s3", return_value=0)
    def test_empty_curated_set_fails_before_dispatch(self, mock_export, mock_run):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.CURATED)

        index_collection_to_test(collection.id)

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.INDEXING_FAILED_ON_TEST
        mock_run.assert_not_called()

    @patch("sde_collections.tasks.run_index_task", return_value="arn:aws:ecs:task/2")
    @patch("sde_collections.tasks.export_curated_to_s3", return_value=10)
    def test_prod_dispatch_remembers_entering_qc_status(self, mock_export, mock_run):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.QUALITY_CHECK_MINOR)

        index_collection_to_prod(collection.id)

        dispatch = IndexDispatch.objects.get(collection=collection)
        assert dispatch.target == "prod"
        assert dispatch.previous_workflow_status == WorkflowStatusChoices.QUALITY_CHECK_MINOR
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.PRODUCTION_INDEXING


class TestRunStatusFetchers:
    """The S3 boundary itself: poll_index_runs tests mock fetch_run_status, so the real
    index_runs/{config_folder}/{run_id}/ key layout and missing-key handling (None while
    the run is in flight, raise on real errors) must be proven here."""

    @pytest.fixture(autouse=True)
    def index_bucket(self):
        # override_settings can't decorate a plain (non-SimpleTestCase) class
        with override_settings(SDE_INDEX_BUCKET="sde-cosmos-indexing-test"):
            yield

    def _patch_s3(self, get_object):
        s3 = MagicMock()
        if isinstance(get_object, BaseException):
            s3.get_object.side_effect = get_object
        else:
            s3.get_object.return_value = get_object
        session = MagicMock()
        session.client.return_value = s3
        return patch("sde_collections.indexing.run_status.get_boto3_session", return_value=session), s3

    def test_fetch_run_status_reads_status_json_under_run_prefix(self):
        payload = {"state": "succeeded"}
        patcher, s3 = self._patch_s3({"Body": io.BytesIO(json.dumps(payload).encode("utf-8"))})

        with patcher:
            assert fetch_run_status("astro_data", RUN_ID) == payload

        s3.get_object.assert_called_once_with(
            Bucket="sde-cosmos-indexing-test", Key=f"index_runs/astro_data/{RUN_ID}/status.json"
        )

    def test_fetch_validation_report_reads_validation_json(self):
        payload = {"count_matches": True}
        patcher, s3 = self._patch_s3({"Body": io.BytesIO(json.dumps(payload).encode("utf-8"))})

        with patcher:
            assert fetch_validation_report("astro_data", RUN_ID) == payload

        s3.get_object.assert_called_once_with(
            Bucket="sde-cosmos-indexing-test", Key=f"index_runs/astro_data/{RUN_ID}/validation.json"
        )

    @pytest.mark.parametrize("code", ["NoSuchKey", "404"])
    def test_missing_status_means_run_in_flight(self, code):
        patcher, _ = self._patch_s3(ClientError({"Error": {"Code": code}}, "GetObject"))

        with patcher:
            assert fetch_run_status("astro_data", RUN_ID) is None

    def test_real_s3_errors_propagate(self):
        """AccessDenied etc. must surface, not read as 'still indexing' until stall timeout."""
        patcher, _ = self._patch_s3(ClientError({"Error": {"Code": "AccessDenied"}}, "GetObject"))

        with patcher:
            with pytest.raises(ClientError):
                fetch_run_status("astro_data", RUN_ID)


def _dispatched(collection, target, previous, run_id="run-1"):
    return IndexDispatch.objects.create(
        collection=collection,
        run_id=run_id,
        target=target,
        task_arn="arn:aws:ecs:task/x",
        previous_workflow_status=previous,
    )


@pytest.mark.django_db
class TestPollIndexRuns:
    @patch("sde_collections.tasks.send_indexing_validation_report")
    @patch("sde_collections.tasks.fetch_validation_report", return_value={"count_matches": True})
    @patch("sde_collections.tasks.fetch_run_status", return_value={"state": "succeeded"})
    def test_test_success_stays_and_posts_validation_once(self, mock_status, mock_validation, mock_slack):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.TEST_INDEXING)
        dispatch = _dispatched(collection, "test", WorkflowStatusChoices.CURATED)

        poll_index_runs()
        poll_index_runs()  # resolved dispatches are never polled again

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.TEST_INDEXING
        mock_slack.assert_called_once_with(collection.name, dispatch.run_id, {"count_matches": True})
        dispatch.refresh_from_db()
        assert dispatch.completed_at is not None

    @pytest.mark.parametrize(
        "entered_with,expected",
        [
            (WorkflowStatusChoices.QUALITY_CHECK_PERFECT, WorkflowStatusChoices.PROD_PERFECT),
            (WorkflowStatusChoices.QUALITY_CHECK_MINOR, WorkflowStatusChoices.PROD_MINOR),
        ],
    )
    @patch("sde_collections.tasks.fetch_run_status", return_value={"state": "succeeded"})
    def test_prod_success_mirrors_entering_qc_status(self, mock_status, entered_with, expected):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.PRODUCTION_INDEXING)
        _dispatched(collection, "prod", entered_with)

        poll_index_runs()

        collection.refresh_from_db()
        assert collection.workflow_status == expected

    @pytest.mark.parametrize("state", ["failed", "needs_confirmation", "something_new"])
    @patch("sde_collections.tasks.fetch_run_status")
    def test_failed_and_unknown_states_land_on_failed_status(self, mock_status, state):
        mock_status.return_value = {"state": state, "error": "deletion_threshold_exceeded"}
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.TEST_INDEXING)
        _dispatched(collection, "test", WorkflowStatusChoices.CURATED)

        poll_index_runs()

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.INDEXING_FAILED_ON_TEST

    @patch("sde_collections.tasks.fetch_run_status", return_value=None)
    def test_in_flight_run_stays_open_until_stall_timeout(self, mock_status):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.PRODUCTION_INDEXING)
        dispatch = _dispatched(collection, "prod", WorkflowStatusChoices.QUALITY_CHECK_PERFECT)

        poll_index_runs()
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.PRODUCTION_INDEXING

        IndexDispatch.objects.filter(id=dispatch.id).update(
            dispatched_at=timezone.now() - timedelta(hours=7)  # default timeout is 6h
        )
        poll_index_runs()
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.INDEXING_FAILED_ON_PROD

    @patch("sde_collections.tasks.fetch_run_status", return_value=None)
    def test_poller_reads_only_the_open_dispatchs_run_id(self, mock_status):
        """run_id namespacing: an old (resolved) run's status.json can never satisfy a
        newer dispatch — the poller only ever queries the open dispatch's run_id."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.TEST_INDEXING)
        old = _dispatched(collection, "test", WorkflowStatusChoices.CURATED, run_id="run-old")
        IndexDispatch.objects.filter(id=old.id).update(completed_at=timezone.now())
        _dispatched(collection, "test", WorkflowStatusChoices.CURATED, run_id="run-new")

        poll_index_runs()

        assert mock_status.call_args.args == (collection.config_folder, "run-new")
