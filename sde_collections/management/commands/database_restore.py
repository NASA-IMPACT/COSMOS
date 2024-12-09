"""
Management command to restore PostgreSQL database.

Usage:
    docker-compose -f local.yml run --rm django python manage.py database_restore path/to/backup.sql
    docker-compose -f production.yml run --rm django python manage.py database_restore path/to/backup.sql
"""

import enum
import os
import socket
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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


class Command(BaseCommand):
    help = "Restores PostgreSQL database from backup file"

    def add_arguments(self, parser):
        parser.add_argument("backup_path", type=str, help="Path to the backup file")

    def handle(self, *args, **options):
        server = detect_server()
        backup_path = options["backup_path"]

        if not os.path.exists(backup_path):
            raise CommandError(f"Backup file not found: {backup_path}")

        db_settings = settings.DATABASES["default"]
        host = db_settings["HOST"]
        name = db_settings["NAME"]
        user = db_settings["USER"]
        password = db_settings["PASSWORD"]

        # Drop and recreate database
        drop_cmd = ["psql", "-h", host, "-U", user, "-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {name}"]
        create_cmd = ["psql", "-h", host, "-U", user, "-d", "postgres", "-c", f"CREATE DATABASE {name}"]

        # Restore command
        restore_cmd = ["psql", "-h", host, "-U", user, "-d", name, "-f", backup_path]

        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = password

            self.stdout.write(f"Dropping database {name}...")
            subprocess.run(drop_cmd, env=env, check=True)

            self.stdout.write(f"Creating database {name}...")
            subprocess.run(create_cmd, env=env, check=True)

            self.stdout.write("Restoring from backup...")
            subprocess.run(restore_cmd, env=env, check=True)

            self.stdout.write(self.style.SUCCESS(f"Successfully restored {server.value} database from {backup_path}"))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Restore failed on {server.value}: {str(e)}"))
