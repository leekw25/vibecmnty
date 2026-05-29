from __future__ import annotations

from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def configure_sqlite_connection(sender, connection, **kwargs):
    """
    Optimize SQLite for concurrent reads/writes in web workload.
    """
    if connection.vendor != "sqlite":
        return

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA busy_timeout=20000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA wal_autocheckpoint=1000;")
