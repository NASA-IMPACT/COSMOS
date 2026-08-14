# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_database_backup.py
import gzip
import os
import subprocess
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from sde_collections.management.commands import database_backup
from sde_collections.management.commands.database_backup import temp_file_handler


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run


@pytest.fixture
def mock_date():
    with patch("sde_collections.management.commands.database_backup.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 1, 15)
        yield mock_dt


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
    return database_backup.Command()


class TestBackupCommand:
    def test_get_backup_filename_compressed(self, command, mock_date, monkeypatch):
        """Test backup filename generation with compression."""
        monkeypatch.setenv("BACKUP_ENVIRONMENT", "staging")
        backup_file, dump_file = command.get_backup_filename(compress=True)
        assert backup_file.endswith("staging_backup_20240115.sql.gz")
        assert dump_file.endswith("staging_backup_20240115.sql")

    def test_get_backup_filename_uncompressed(self, command, mock_date, monkeypatch):
        """Test backup filename generation without compression."""
        monkeypatch.setenv("BACKUP_ENVIRONMENT", "production")
        backup_file, dump_file = command.get_backup_filename(compress=False)
        assert backup_file.endswith("production_backup_20240115.sql")
        assert dump_file == backup_file

    def test_get_backup_filename_no_environment(self, command, mock_date, monkeypatch):
        """Test backup filename generation with no environment set."""
        monkeypatch.delenv("BACKUP_ENVIRONMENT", raising=False)
        backup_file, dump_file = command.get_backup_filename(compress=True)
        assert backup_file.endswith("unknown_backup_20240115.sql.gz")
        assert dump_file.endswith("unknown_backup_20240115.sql")

    def test_run_pg_dump(self, command, mock_subprocess, mock_settings):
        """Test pg_dump command execution."""
        env = {"PGPASSWORD": "test_password"}
        command.run_pg_dump("test_output.sql", env)

        mock_subprocess.assert_called_once()
        cmd_args = mock_subprocess.call_args[0][0]
        assert cmd_args == [
            "pg_dump",
            "-h",
            "test-db-host",
            "-U",
            "test_user",
            "-d",
            "test_db",
            "--no-owner",
            "--no-privileges",
            "-f",
            "test_output.sql",
        ]

    def test_compress_file(self, command, tmp_path):
        """Test file compression."""
        input_file = tmp_path / "test.sql"
        output_file = tmp_path / "test.sql.gz"
        test_content = b"Test database content"

        # Create test input file
        input_file.write_bytes(test_content)

        # Compress the file
        command.compress_file(str(input_file), str(output_file))

        # Verify compression
        assert output_file.exists()
        with gzip.open(output_file, "rb") as f:
            assert f.read() == test_content

    def test_temp_file_handler_cleanup(self, tmp_path):
        """Test temporary file cleanup."""
        test_file = tmp_path / "temp.sql"
        test_file.touch()

        with temp_file_handler(str(test_file)):
            assert test_file.exists()
        assert not test_file.exists()

    def test_temp_file_handler_cleanup_on_error(self, tmp_path):
        """Test temporary file cleanup when an error occurs."""
        test_file = tmp_path / "temp.sql"
        test_file.touch()

        with pytest.raises(ValueError):
            with temp_file_handler(str(test_file)):
                assert test_file.exists()
                raise ValueError("Test error")
        assert not test_file.exists()

    @pytest.mark.parametrize(
        "compress,env_name",
        [
            (True, "production"),
            (False, "staging"),
            (True, "carson_local"),
        ],
    )
    def test_handle_integration(self, compress, env_name, mock_subprocess, mock_date, mock_settings, monkeypatch):
        """Test full backup process integration."""
        monkeypatch.setenv("BACKUP_ENVIRONMENT", env_name)
        call_command("database_backup", no_compress=not compress)

        # Verify correct command execution
        mock_subprocess.assert_called_once()

        # Verify the dump lands on the exact backups-volume path
        cmd_args = mock_subprocess.call_args[0][0]
        assert cmd_args[-1] == f"/app/backups/{env_name}_backup_20240115.sql"

    def test_compressed_backup_writes_gz_and_removes_temp_dump(self, mock_subprocess, tmp_path):
        """Real file lifecycle: the mocked pg_dump writes a dump file, the real
        compress_file gzips it, and temp_file_handler removes the intermediate .sql."""
        dump_content = b"-- PostgreSQL dump"

        def fake_pg_dump(cmd, env, check):
            with open(cmd[-1], "wb") as f:
                f.write(dump_content)

        mock_subprocess.side_effect = fake_pg_dump
        output = tmp_path / "backup.sql"

        call_command("database_backup", output=str(output))

        assert not output.exists()  # temp dump cleaned up
        with gzip.open(str(output) + ".gz", "rb") as f:
            assert f.read() == dump_content

    def test_handle_pg_dump_error(self, mock_subprocess, tmp_path):
        """pg_dump failure must be reported, swallowed, and leave no backup artifacts."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "pg_dump")
        output = tmp_path / "backup.sql"
        out = StringIO()

        call_command("database_backup", output=str(output), stdout=out)  # must not raise

        assert "Backup failed" in out.getvalue()
        assert not output.exists()
        assert not os.path.exists(str(output) + ".gz")

    def test_handle_compression_error(self, mock_subprocess, tmp_path):
        """Compression failure must be reported, swallowed, and still clean up the temp
        dump that pg_dump produced. (Patch compress_file on the class: call_command
        instantiates its own Command, so patching a fixture instance guards nothing.)"""

        def fake_pg_dump(cmd, env, check):
            with open(cmd[-1], "wb") as f:
                f.write(b"-- dump")

        mock_subprocess.side_effect = fake_pg_dump
        output = tmp_path / "backup.sql"
        out = StringIO()

        with patch.object(
            database_backup.Command, "compress_file", side_effect=Exception("Compression failed")
        ):
            call_command("database_backup", output=str(output), stdout=out)  # must not raise

        assert "Error during backup process" in out.getvalue()
        assert not output.exists()  # temp dump cleaned up despite the failure
        assert not os.path.exists(str(output) + ".gz")
