"""DEPRECATED compatibility shim.

All scheduled background jobs have been relocated to the ``app.jobs``
package (see ``app.jobs.premium_jobs`` and ``app.jobs.streak_jobs``).
This module is kept only so that third-party imports and the legacy
``register_jobs`` wiring continue to work. Prefer importing directly
from ``app.jobs.*`` — this module will be removed in a future release.
"""
import warnings

warnings.warn(
    "app.utils.scheduler is deprecated and will be removed; "
    "import check_expired_premium from app.jobs.premium_jobs and "
    "check_streak_protection from app.jobs.streak_jobs instead.",
    DeprecationWarning,
    stacklevel=2,
)

from app.jobs.premium_jobs import check_expired_premium  # noqa: F401,E402
from app.jobs.streak_jobs import check_streak_protection  # noqa: F401,E402
