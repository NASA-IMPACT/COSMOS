# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_database_restore.py
import gzip
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections

from sde_collections.management.commands import database_restore
from sde_collections.models.collection import Collection
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)

# Register the integration mark
pytest.mark.integration = pytest.mark.django_db(transaction=True)


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run


@pytest.fixture
def mock_settings(settings):
    """Configure test database settings."""
    settings.DATABASES = {
        "default": {
            "HOST": "test-db-host",
            "NAME": "test_db",
            "USER": "test_user",
            "PASSWORD": "test_password",
        }
    }
    return settings


@pytest.fixture
def command():
    return database_restore.Command()


@pytest.fixture
def backup_file(tmp_path):
    """Create a temporary backup file."""
    backup_path = tmp_path / "test_backup.sql"
    backup_path.write_text("-- Test backup content")
    return str(backup_path)


@pytest.fixture
def compressed_backup_file(tmp_path):
    """Create a temporary compressed backup file."""
    backup_path = tmp_path / "test_backup.sql.gz"
    with gzip.open(backup_path, "wt") as f:
        f.write("-- Test backup content")
    return str(backup_path)


class TestRestoreCommand:
    def test_get_db_settings(self, command, mock_settings):
        """Test database settings retrieval."""
        settings = command.get_db_settings()
        assert settings == {
            "host": "test-db-host",
            "name": "test_db",
            "user": "test_user",
            "password": "test_password",
        }

    def test_run_psql_command(self, command, mock_subprocess, mock_settings):
        """Test psql command execution."""
        env = {"PGPASSWORD": "test_password"}
        command.run_psql_command("SELECT 1;", "test_db", env)

        mock_subprocess.assert_called_once()
        cmd_args = mock_subprocess.call_args[0][0]
        assert cmd_args == [
            "psql",
            "-h",
            "test-db-host",
            "-U",
            "test_user",
            "-d",
            "test_db",
            "-c",
            "SELECT 1;",
        ]

    def test_reset_database(self, command, mock_subprocess, mock_settings):
        """Test database reset process."""
        env = {"PGPASSWORD": "test_password"}
        command.reset_database(env)

        # Verify drop, create and terminate connections commands were executed
        assert mock_subprocess.call_count >= 2
        calls = mock_subprocess.call_args_list
        assert any("DROP DATABASE" in call[0][0][-1] for call in calls)
        assert any("CREATE DATABASE" in call[0][0][-1] for call in calls)

    def test_restore_backup(self, command, mock_subprocess, mock_settings, backup_file):
        """Test backup restoration."""
        env = {"PGPASSWORD": "test_password"}
        command.restore_backup(backup_file, env)

        mock_subprocess.assert_called_once()
        cmd_args = mock_subprocess.call_args[0][0]
        assert cmd_args == [
            "psql",
            "-h",
            "test-db-host",
            "-U",
            "test_user",
            "-d",
            "test_db",
            "-f",
            backup_file,
        ]

    def test_decompress_file(self, command, tmp_path, compressed_backup_file):
        """Test backup file decompression."""
        output_file = str(tmp_path / "decompressed.sql")
        command.decompress_file(compressed_backup_file, output_file)

        with open(output_file) as f:
            content = f.read()
            assert content == "-- Test backup content"

    def test_handle_file_not_found(self, command):
        """Test error handling for non-existent backup file."""
        with pytest.raises(CommandError):
            call_command("database_restore", "nonexistent.sql")


@pytest.mark.django_db
class TestDatabaseIntegration:
    """Integration tests for backup and restore functionality."""

    def create_test_data(self):
        """Create a set of test data using factories."""
        collection = CollectionFactory()

        # Create some URLs
        dump_urls = DumpUrlFactory.create_batch(3, collection=collection)
        curated_urls = CuratedUrlFactory.create_batch(3, collection=collection)
        delta_urls = DeltaUrlFactory.create_batch(3, collection=collection)

        return {
            "collection": collection,
            "dump_urls": dump_urls,
            "curated_urls": curated_urls,
            "delta_urls": delta_urls,
        }

    def verify_data_integrity(self, original_data):
        """Verify that all data matches the original after restore."""
        # Close all existing database connections before verification
        connections.close_all()

        # Verify collection
        restored_collection = Collection.objects.get(pk=original_data["collection"].pk)
        assert restored_collection.name == original_data["collection"].name
        assert restored_collection.config_folder == original_data["collection"].config_folder

        # Verify URLs
        for original_url in original_data["dump_urls"]:
            restored_url = DumpUrl.objects.get(pk=original_url.pk)
            assert restored_url.url == original_url.url
            assert restored_url.scraped_title == original_url.scraped_title

        for original_url in original_data["curated_urls"]:
            restored_url = CuratedUrl.objects.get(pk=original_url.pk)
            assert restored_url.url == original_url.url
            assert restored_url.scraped_title == original_url.scraped_title

        for original_url in original_data["delta_urls"]:
            restored_url = DeltaUrl.objects.get(pk=original_url.pk)
            assert restored_url.url == original_url.url
            assert restored_url.scraped_title == original_url.scraped_title

    @pytest.mark.integration
    def test_full_backup_restore_cycle(self, tmp_path):
        """Test complete backup and restore cycle with actual data."""
        # Create test data
        original_data = self.create_test_data()

        # Create backup
        backup_file = str(tmp_path / "integration_test_backup.sql")
        with patch("socket.gethostname", return_value="TEST-SERVER"):
            connections.close_all()  # Close connections before backup
            call_command("database_backup", "--no-compress", output=backup_file)

        # Clear the database
        for Model in [Collection, DumpUrl, CuratedUrl, DeltaUrl]:
            Model.objects.all().delete()

        assert Collection.objects.count() == 0
        assert DumpUrl.objects.count() == 0
        assert CuratedUrl.objects.count() == 0
        assert DeltaUrl.objects.count() == 0

        # Restore from backup
        connections.close_all()  # Close connections before restore
        call_command("database_restore", backup_file)

        # Verify data integrity
        self.verify_data_integrity(original_data)

    @pytest.mark.integration
    def test_compressed_backup_restore_cycle(self, tmp_path):
        """Test backup and restore cycle with compression."""
        # Create test data
        original_data = self.create_test_data()

        # Create compressed backup
        backup_file = str(tmp_path / "integration_test_backup.sql.gz")
        with patch("socket.gethostname", return_value="TEST-SERVER"):
            connections.close_all()  # Close connections before backup
            call_command("database_backup", output=backup_file)  # Compression is enabled by default

        # Clear the database
        connections.close_all()  # Close connections before clearing
        Collection.objects.all().delete()

        # Restore from compressed backup
        connections.close_all()  # Close connections before restore
        call_command("database_restore", backup_file)

        # Verify data integrity
        self.verify_data_integrity(original_data)

    @pytest.mark.integration
    def test_partial_data_integrity(self, tmp_path):
        """Test backup and restore with partial data modifications."""
        # Create initial data
        original_data = self.create_test_data()
        original_name = original_data["collection"].name
        original_url_id = original_data["curated_urls"][0].id  # Store the ID explicitly

        # Create backup
        backup_file = str(tmp_path / "partial_test_backup.sql")
        with patch("socket.gethostname", return_value="TEST-SERVER"):
            connections.close_all()  # Close connections before backup
            call_command("database_backup", "--no-compress", output=backup_file)

        # Modify some data
        collection = original_data["collection"]
        collection.name = "Modified Name"
        collection.save()

        new_curated_url = CuratedUrlFactory(collection=collection)
        original_data["curated_urls"][0].delete()

        # Restore from backup
        connections.close_all()  # Close connections before restore
        call_command("database_restore", backup_file)

        # Verify original state is restored
        restored_collection = Collection.objects.get(pk=collection.pk)
        assert restored_collection.name == original_name
        assert not CuratedUrl.objects.filter(pk=new_curated_url.pk).exists()
        assert CuratedUrl.objects.filter(pk=original_url_id).exists()  # Use the stored ID
