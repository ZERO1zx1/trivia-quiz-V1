"""DEPRECATED compatibility stub.

This root-level module was orphaned (no internal importers) and its
contents have been relocated to ``app.jobs.email_tasks``. This stub
re-exports the helpers so that any external importer continues to work,
and emits a ``DeprecationWarning`` on import. Prefer importing from
``app.jobs.email_tasks`` — this module will be removed in a future
release.
"""
import warnings

warnings.warn(
    "app.tasks is deprecated and will be removed; "
    "import from app.jobs.email_tasks instead.",
    DeprecationWarning,
    stacklevel=2,
)

from app.jobs.email_tasks import (  # noqa: F401,E402
    get_redis_queue,
    queue_email,
    send_email_async,
)
