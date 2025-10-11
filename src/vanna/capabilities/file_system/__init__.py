"""
File system capability.

This module provides abstractions for file system operations used by tools.
"""

from .base import FileSystem
from .models import CommandResult, FileSearchMatch

__all__ = [
    "FileSystem",
    "FileSearchMatch",
    "CommandResult",
]
