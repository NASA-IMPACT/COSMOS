"""
Management command to restore PostgreSQL database from backup.

Usage:
    docker-compose -f local.yml run --rm django python manage.py database_restore backups/backup.sql[.gz]
    docker-compose -f production.yml run --rm django python manage.py database_restore backups/backup.sql[.gz]

The backup file should be located in the /backups directory, which is mounted as a volume in both
local and production environments.
"""

import enum
import gzip
import os
import shutil
import socket
import subprocess
from contextlib import contextmanager

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


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
    help = "Restores PostgreSQL database from backup file (compressed or uncompressed)"

    def add_arguments(self, parser):
        parser.add_argument("backup_path", type=str, help="Path to the backup file (.sql or .sql.gz)")

    def get_db_settings(self):
        """Get database connection settings."""
        db = settings.DATABASES["default"]
        return {
            "host": db["HOST"],
            "name": db["NAME"],
            "user": db["USER"],
            "password": db["PASSWORD"],
        }

    def run_psql_command(self, command: str, db_name: str = "postgres", env: dict = None) -> None:
        """Execute a psql command."""
        db = self.get_db_settings()
        cmd = ["psql", "-h", db["host"], "-U", db["user"], "-d", db_name, "-c", command]
        subprocess.run(cmd, env=env, check=True)

    def terminate_database_connections(self, env: dict) -> None:
        """Terminate all connections to the database."""
        db = self.get_db_settings()
        # Close Django's connection first
        connections.close_all()

        # Terminate any remaining PostgreSQL connections
        terminate_conn_sql = f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{db["name"]}'
        AND pid <> pg_backend_pid();
        """
        try:
            self.run_psql_command(terminate_conn_sql, env=env)
        except subprocess.CalledProcessError:
            # If this fails, it's usually because there are no connections to terminate
            pass

    def reset_database(self, env: dict) -> None:
        """Drop and recreate the database."""
        db = self.get_db_settings()

        self.stdout.write(f"Terminating connections to {db['name']}...")
        self.terminate_database_connections(env)

        self.stdout.write(f"Dropping database {db['name']}...")
        self.run_psql_command(f"DROP DATABASE IF EXISTS {db['name']}", env=env)

        self.stdout.write(f"Creating database {db['name']}...")
        self.run_psql_command(f"CREATE DATABASE {db['name']}", env=env)

    def restore_backup(self, backup_file: str, env: dict) -> None:
        """Restore database from backup file."""
        db = self.get_db_settings()
        cmd = ["psql", "-h", db["host"], "-U", db["user"], "-d", db["name"], "-f", backup_file]
        self.stdout.write("Restoring from backup...")
        subprocess.run(cmd, env=env, check=True)

    def decompress_file(self, input_file: str, output_file: str) -> None:
        """Decompress gzipped file to output file."""
        with gzip.open(input_file, "rb") as f_in:
            with open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    def handle(self, *args, **options):
        server = detect_server()
        backup_path = options["backup_path"]
        is_compressed = backup_path.endswith(".gz")

        if not os.path.exists(backup_path):
            raise CommandError(f"Backup file not found: {backup_path}")

        env = os.environ.copy()
        env["PGPASSWORD"] = self.get_db_settings()["password"]

        try:
            # Reset the database first
            self.reset_database(env)

            # Handle backup restoration
            if is_compressed:
                with temp_file_handler(backup_path[:-3]) as temp_file:
                    self.decompress_file(backup_path, temp_file)
                    self.restore_backup(temp_file, env)
            else:
                self.restore_backup(backup_path, env)

            self.stdout.write(self.style.SUCCESS(f"Successfully restored {server.value} database from {backup_path}"))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Restore failed on {server.value}: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during restore process: {str(e)}"))
