"""
Local file system implementation.

This module provides a local file system implementation with per-user isolation.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import List, Optional

from vanna.capabilities.file_system import CommandResult, FileSearchMatch, FileSystem
from vanna.core.tool import ToolContext

MAX_SEARCH_FILE_BYTES = 1_000_000


class LocalFileSystem(FileSystem):
    """Local file system implementation with per-user isolation."""

    def __init__(self, working_directory: str = "."):
        """Initialize with a working directory.

        Args:
            working_directory: Base directory where user-specific folders will be created
        """
        self.working_directory = Path(working_directory)

    def _get_user_directory(self, context: ToolContext) -> Path:
        """Get the user-specific directory by hashing the user ID.

        Args:
            context: Tool context containing user information

        Returns:
            Path to the user-specific directory
        """
        # Hash the user ID to create a directory name
        user_hash = hashlib.sha256(context.user.id.encode()).hexdigest()[:16]
        user_dir = self.working_directory / user_hash

        # Create the directory if it doesn't exist
        user_dir.mkdir(parents=True, exist_ok=True)

        return user_dir

    def _resolve_path(self, path: str, context: ToolContext) -> Path:
        """Resolve a path relative to the user's directory.

        Args:
            path: Path relative to user directory
            context: Tool context containing user information

        Returns:
            Absolute path within user's directory
        """
        user_dir = self._get_user_directory(context)
        resolved = user_dir / path

        # Ensure the path is within the user's directory (prevent directory traversal)
        try:
            resolved.resolve().relative_to(user_dir.resolve())
        except ValueError:
            raise PermissionError(f"Access denied: path '{path}' is outside user directory")

        return resolved

    async def list_files(self, directory: str, context: ToolContext) -> List[str]:
        """List files in a directory within the user's isolated space."""
        directory_path = self._resolve_path(directory, context)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directory '{directory}' does not exist")

        if not directory_path.is_dir():
            raise NotADirectoryError(f"'{directory}' is not a directory")

        files = []
        for item in directory_path.iterdir():
            if item.is_file():
                files.append(item.name)

        return sorted(files)

    async def read_file(self, filename: str, context: ToolContext) -> str:
        """Read the contents of a file within the user's isolated space."""
        file_path = self._resolve_path(filename, context)

        if not file_path.exists():
            raise FileNotFoundError(f"File '{filename}' does not exist")

        if not file_path.is_file():
            raise IsADirectoryError(f"'{filename}' is a directory, not a file")

        return file_path.read_text(encoding='utf-8')

    async def write_file(self, filename: str, content: str, context: ToolContext, overwrite: bool = False) -> None:
        """Write content to a file within the user's isolated space."""
        file_path = self._resolve_path(filename, context)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File '{filename}' already exists. Use overwrite=True to replace it.")

        file_path.write_text(content, encoding='utf-8')

    async def exists(self, path: str, context: ToolContext) -> bool:
        """Check if a file or directory exists within the user's isolated space."""
        try:
            resolved_path = self._resolve_path(path, context)
            return resolved_path.exists()
        except PermissionError:
            return False

    async def is_directory(self, path: str, context: ToolContext) -> bool:
        """Check if a path is a directory within the user's isolated space."""
        try:
            resolved_path = self._resolve_path(path, context)
            return resolved_path.exists() and resolved_path.is_dir()
        except PermissionError:
            return False

    async def search_files(
        self,
        query: str,
        context: ToolContext,
        *,
        max_results: int = 20,
        include_content: bool = False,
    ) -> List[FileSearchMatch]:
        """Search for files within the user's isolated space."""

        trimmed_query = query.strip()
        if not trimmed_query:
            raise ValueError("Search query must not be empty")

        user_dir = self._get_user_directory(context)
        matches: List[FileSearchMatch] = []
        query_lower = trimmed_query.lower()

        for path in user_dir.rglob("*"):
            if len(matches) >= max_results:
                break

            if not path.is_file():
                continue

            relative_path = path.relative_to(user_dir).as_posix()
            include_entry = False
            snippet: Optional[str] = None

            if query_lower in path.name.lower():
                include_entry = True
                snippet = "[filename match]"

            content: Optional[str] = None
            if include_content:
                try:
                    size = path.stat().st_size
                except OSError:
                    if include_entry:
                        matches.append(FileSearchMatch(path=relative_path, snippet=snippet))
                    continue

                if size <= MAX_SEARCH_FILE_BYTES:
                    try:
                        content = path.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        content = None
                elif not include_entry:
                    # Skip oversized files if they do not match by name
                    continue

            if include_content and content is not None:
                if query_lower in content.lower():
                    # Create snippet
                    lowered = content.lower()
                    index = lowered.find(query_lower)
                    if index != -1:
                        context_window = 60
                        start = max(0, index - context_window)
                        end = min(len(content), index + len(query) + context_window)
                        snippet = content[start:end].replace("\n", " ").strip()
                        if start > 0:
                            snippet = f"…{snippet}"
                        if end < len(content):
                            snippet = f"{snippet}…"
                    include_entry = True
                elif not include_entry:
                    continue

            if include_entry:
                matches.append(FileSearchMatch(path=relative_path, snippet=snippet))

        return matches

    async def run_bash(
        self,
        command: str,
        context: ToolContext,
        *,
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Execute a bash command within the user's isolated space."""

        if not command.strip():
            raise ValueError("Command must not be empty")

        user_dir = self._get_user_directory(context)

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(user_dir),
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds") from exc

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return CommandResult(stdout=stdout, stderr=stderr, returncode=process.returncode or 0)
