from contextlib import contextmanager

from django.db import connection


class AdvisoryLock:
    """
    Utility class for managing Postgres advisory locks.
    Uses a 64-bit integer for the lock key, which can be derived from a string.
    """

    def __init__(self, name: str):
        """Initialize with a lock name that will be converted to a consistent integer."""
        # Convert lock name to a positive 64-bit integer using hash
        # We use hash() and abs() to ensure we get a positive integer within Postgres' supported range
        self.lock_id = abs(hash(name)) % (2**63 - 1)

    def acquire(self) -> bool:
        """
        Attempt to acquire the advisory lock.
        Returns True if lock was acquired, False otherwise.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s);", [self.lock_id])
            return cursor.fetchone()[0]

    def release(self) -> bool:
        """
        Release the advisory lock.
        Returns True if lock was released, False if it wasn't held.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s);", [self.lock_id])
            return cursor.fetchone()[0]

    @contextmanager
    def hold(self):
        """
        Context manager for handling lock acquisition and release.

        Usage:
            with AdvisoryLock("my_lock").hold():
                # do work here
        """
        acquired = False
        try:
            acquired = self.acquire()
            yield acquired
        finally:
            if acquired:
                self.release()
