"""
Compatibility shims for different Python versions.

This module provides compatibility utilities for features that vary across
Python versions.
"""

try:
    from enum import StrEnum  # Py 3.11+
except ImportError:  # Py < 3.11
    from enum import Enum

    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """Minimal backport of StrEnum for Python < 3.11."""

        pass


__all__ = ["StrEnum"]
