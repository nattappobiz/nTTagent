"""Aggregate router imports for FastAPI.

This package initialises the sub‑routers so they can be imported by
``app.main`` without causing circular imports. Each router module defines
its own ``router`` instance which is included in the main application.
"""

from . import uploads  # noqa: F401
from . import citizens  # noqa: F401
from . import files  # noqa: F401
from . import export  # noqa: F401