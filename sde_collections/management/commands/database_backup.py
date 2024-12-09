"""
Management command to backup PostgreSQL database.

Usage:
    docker-compose -f local.yml run --rm django python manage.py database_backup
    docker-compose -f production.yml run --rm django python manage.py database_backup
"""

import enum
import os
import socket
import subprocess
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


class Command(BaseCommand):
    help = "Creates a PostgreSQL backup using pg_dump"

    def handle(self, *args, **options):
        server = detect_server()
        date_str = datetime.now().strftime("%Y%m%d")
        backup_file = f"{server.value.lower()}_backup_{date_str}.sql"

        db_settings = settings.DATABASES["default"]
        host = db_settings["HOST"]
        name = db_settings["NAME"]
        user = db_settings["USER"]
        password = db_settings["PASSWORD"]

        cmd = ["pg_dump", "-h", host, "-U", user, "-d", name, "--no-owner", "--no-privileges", "-f", backup_file]

        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            subprocess.run(cmd, env=env, check=True)
            self.stdout.write(self.style.SUCCESS(f"Successfully created backup for {server.value}: {backup_file}"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Backup failed on {server.value}: {str(e)}"))
