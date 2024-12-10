# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_database_backup.py
import gzip
import os
import subprocess
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

from sde_collections.management.commands import database_backup
from sde_collections.management.commands.database_backup import (
    Server,
    temp_file_handler,
)


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
    def test_get_backup_filename_compressed(self, command, mock_date):
        """Test backup filename generation with compression."""
        backup_file, dump_file = command.get_backup_filename(Server.STAGING, compress=True)
        assert backup_file == "staging_backup_20240115.sql.gz"
        assert dump_file == "staging_backup_20240115.sql"

    def test_get_backup_filename_uncompressed(self, command, mock_date):
        """Test backup filename generation without compression."""
        backup_file, dump_file = command.get_backup_filename(Server.PRODUCTION, compress=False)
        assert backup_file == "production_backup_20240115.sql"
        assert dump_file == backup_file

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

    @patch("socket.gethostname")
    def test_server_detection(self, mock_hostname):
        """Test server environment detection."""
        test_cases = [
            ("PRODUCTION-SERVER", Server.PRODUCTION),
            ("STAGING-DB", Server.STAGING),
            ("DEV-HOST", Server.UNKNOWN),
        ]

        for hostname, expected_server in test_cases:
            mock_hostname.return_value = hostname
            with patch("sde_collections.management.commands.database_backup.detect_server") as mock_detect:
                mock_detect.return_value = expected_server
                server = database_backup.detect_server()
                assert server == expected_server

    @pytest.mark.parametrize(
        "compress,hostname",
        [
            (True, "PRODUCTION-SERVER"),
            (False, "STAGING-SERVER"),
            (True, "UNKNOWN-SERVER"),
        ],
    )
    def test_handle_integration(self, compress, hostname, mock_subprocess, mock_date, mock_settings):
        """Test full backup process integration."""
        with patch("socket.gethostname", return_value=hostname):
            call_command("database_backup", no_compress=not compress)

        # Verify correct command execution
        mock_subprocess.assert_called_once()

        # Verify correct filename used
        cmd_args = mock_subprocess.call_args[0][0]
        date_str = "20240115"
        server_type = hostname.split("-")[0].lower()
        expected_base = f"{server_type}_backup_{date_str}.sql"

        if compress:
            assert cmd_args[-1] == expected_base  # Temporary file
            # Verify cleanup attempted
            assert not os.path.exists(expected_base)
        else:
            assert cmd_args[-1] == expected_base

    def test_handle_pg_dump_error(self, mock_subprocess, mock_date):
        """Test error handling when pg_dump fails."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "pg_dump")

        with patch("socket.gethostname", return_value="STAGING-SERVER"):
            call_command("database_backup")

        # Verify error handling and cleanup
        date_str = "20240115"
        temp_file = f"staging_backup_{date_str}.sql"
        assert not os.path.exists(temp_file)

    def test_handle_compression_error(self, mock_subprocess, mock_date, command):
        """Test error handling during compression."""
        # Mock compression to fail
        command.compress_file = Mock(side_effect=Exception("Compression failed"))

        with patch("socket.gethostname", return_value="STAGING-SERVER"):
            call_command("database_backup")

        # Verify cleanup
        date_str = "20240115"
        temp_file = f"staging_backup_{date_str}.sql"
        assert not os.path.exists(temp_file)
