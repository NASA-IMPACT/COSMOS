"""
Management command to backup PostgreSQL database.

Usage:
    docker-compose -f local.yml run --rm django python manage.py database_backup
    docker-compose -f local.yml run --rm django python manage.py database_backup --no-compress
    docker-compose -f production.yml run --rm django python manage.py database_backup
"""

import enum
import gzip
import os
import shutil
import socket
import subprocess
from contextlib import contextmanager
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand


class Server(enum.Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    UNKNOWN = "UNKNOWN"


def detect_server() -> Server:
    hostname = socket.gethostname().upper()
    if "PRODUCTION" in hostname:
        return Server.PRODUCTION
    elif "STAGING" in hostname:
        return Server.STAGING
    return Server.UNKNOWN


@contextmanager
def temp_file_handler(filename: str):
    """Context manager to handle temporary files, ensuring cleanup."""
    try:
        yield filename
    finally:
        if os.path.exists(filename):
            os.remove(filename)


class Command(BaseCommand):
    help = "Creates a PostgreSQL backup using pg_dump"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-compress",
            action="store_true",
            help="Disable backup file compression (enabled by default)",
        )

    def get_backup_filename(self, server: Server, compress: bool) -> tuple[str, str]:
        """Generate backup filename and actual dump path.

        Returns:
            tuple[str, str]: A tuple containing (final_filename, temp_filename)
                - final_filename: The name of the final backup file (with .gz if compressed)
                - temp_filename: The name of the temporary dump file (always without .gz)
        """
        date_str = datetime.now().strftime("%Y%m%d")
        temp_filename = f"{server.value.lower()}_backup_{date_str}.sql"
        final_filename = f"{temp_filename}.gz" if compress else temp_filename
        return final_filename, temp_filename

    def run_pg_dump(self, output_file: str, env: dict) -> None:
        """Execute pg_dump with given parameters."""
        db_settings = settings.DATABASES["default"]
        cmd = [
            "pg_dump",
            "-h",
            db_settings["HOST"],
            "-U",
            db_settings["USER"],
            "-d",
            db_settings["NAME"],
            "--no-owner",
            "--no-privileges",
            "-f",
            output_file,
        ]
        subprocess.run(cmd, env=env, check=True)

    def compress_file(self, input_file: str, output_file: str) -> None:
        """Compress input file to output file using gzip."""
        with open(input_file, "rb") as f_in:
            with gzip.open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    def handle(self, *args, **options):
        server = detect_server()
        compress = not options["no_compress"]
        backup_file, dump_file = self.get_backup_filename(server, compress)

        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DATABASES["default"]["PASSWORD"]

        try:
            if compress:
                with temp_file_handler(dump_file):
                    self.run_pg_dump(dump_file, env)
                    self.compress_file(dump_file, backup_file)
            else:
                self.run_pg_dump(backup_file, env)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {'compressed ' if compress else ''}backup for {server.value}: {backup_file}"
                )
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Backup failed on {server.value}: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during backup process: {str(e)}"))
