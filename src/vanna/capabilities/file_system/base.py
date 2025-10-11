"""
File system capability interface.

This module contains the abstract base class for file system operations.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from .models import CommandResult, FileSearchMatch

if TYPE_CHECKING:
    from vanna.core.tool import ToolContext


class FileSystem(ABC):
    """Abstract base class for file system operations."""

    @abstractmethod
    async def list_files(self, directory: str, context: "ToolContext") -> List[str]:
        """List files in a directory."""
        pass

    @abstractmethod
    async def read_file(self, filename: str, context: "ToolContext") -> str:
        """Read the contents of a file."""
        pass

    @abstractmethod
    async def write_file(
        self, filename: str, content: str, context: "ToolContext", overwrite: bool = False
    ) -> None:
        """Write content to a file."""
        pass

    @abstractmethod
    async def exists(self, path: str, context: "ToolContext") -> bool:
        """Check if a file or directory exists."""
        pass

    @abstractmethod
    async def is_directory(self, path: str, context: "ToolContext") -> bool:
        """Check if a path is a directory."""
        pass

    @abstractmethod
    async def search_files(
        self,
        query: str,
        context: "ToolContext",
        *,
        max_results: int = 20,
        include_content: bool = False,
    ) -> List[FileSearchMatch]:
        """Search for files matching a query within the accessible namespace."""
        pass

    @abstractmethod
    async def run_bash(
        self,
        command: str,
        context: "ToolContext",
        *,
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Execute a bash command within the accessible namespace."""
        pass
