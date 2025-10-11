"""
File system tools with dependency injection support.

This module provides file system operations through an abstract FileSystem interface,
allowing for different implementations (local, remote, sandboxed, etc.).
The tools accept a FileSystem instance via dependency injection.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Type
import difflib
import hashlib

from pydantic import BaseModel, Field, model_validator

from vanna.core.tool import Tool, ToolContext, ToolResult
from vanna.components import (
    UiComponent,
    CardComponent,
    NotificationComponent,
    ComponentType,
    SimpleTextComponent,
)

MAX_SEARCH_FILE_BYTES = 1_000_000
FILENAME_MATCH_SNIPPET = "[filename match]"


@dataclass
class FileSearchMatch:
    """Represents a single search result within a file system."""

    path: str
    snippet: Optional[str] = None


@dataclass
class CommandResult:
    """Represents the result of executing a shell command."""

    stdout: str
    stderr: str
    returncode: int


def _make_snippet(text: str, query: str, context_window: int = 60) -> Optional[str]:
    """Return a short snippet around the first occurrence of query in text."""

    lowered = text.lower()
    index = lowered.find(query.lower())
    if index == -1:
        return None

    start = max(0, index - context_window)
    end = min(len(text), index + len(query) + context_window)
    snippet = text[start:end].replace("\n", " ").strip()

    if start > 0:
        snippet = f"…{snippet}"
    if end < len(text):
        snippet = f"{snippet}…"

    return snippet


class FileSystem(ABC):
    """Abstract base class for file system operations."""

    @abstractmethod
    async def list_files(self, directory: str, context: ToolContext) -> List[str]:
        """List files in a directory."""
        pass

    @abstractmethod
    async def read_file(self, filename: str, context: ToolContext) -> str:
        """Read the contents of a file."""
        pass

    @abstractmethod
    async def write_file(self, filename: str, content: str, context: ToolContext, overwrite: bool = False) -> None:
        """Write content to a file."""
        pass

    @abstractmethod
    async def exists(self, path: str, context: ToolContext) -> bool:
        """Check if a file or directory exists."""
        pass

    @abstractmethod
    async def is_directory(self, path: str, context: ToolContext) -> bool:
        """Check if a path is a directory."""
        pass

    @abstractmethod
    async def search_files(
        self,
        query: str,
        context: ToolContext,
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
        context: ToolContext,
        *,
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Execute a bash command within the accessible namespace."""
        pass


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
                snippet = FILENAME_MATCH_SNIPPET

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
                    snippet = _make_snippet(content, trimmed_query) or snippet
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


class SearchFilesArgs(BaseModel):
    """Arguments for searching files."""

    query: str = Field(description="Text to search for in file names or contents")
    include_content: bool = Field(
        default=True,
        description="Whether to search within file contents in addition to file names",
    )
    max_results: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of matches to return",
    )


class SearchFilesTool(Tool[SearchFilesArgs]):
    """Tool to search for files using the injected file system implementation."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "Search for files by name or content"

    def get_args_schema(self) -> Type[SearchFilesArgs]:
        return SearchFilesArgs

    async def execute(self, context: ToolContext, args: SearchFilesArgs) -> ToolResult:
        try:
            matches = await self.file_system.search_files(
                args.query,
                context,
                max_results=args.max_results,
                include_content=args.include_content,
            )
        except Exception as exc:
            error_msg = f"Error searching files: {exc}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(exc),
            )

        if not matches:
            message = f"No matches found for '{args.query}'."
            return ToolResult(
                success=True,
                result_for_llm=message,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="info",
                        message=message,
                    ),
                    simple_component=SimpleTextComponent(text=message),
                ),
            )

        lines: List[str] = []
        for match in matches:
            snippet = match.snippet
            if snippet == FILENAME_MATCH_SNIPPET:
                snippet_text = "(matched filename)"
            elif snippet:
                snippet_text = snippet
            else:
                snippet_text = ""

            if snippet_text and len(snippet_text) > 200:
                snippet_text = f"{snippet_text[:197]}…"

            if snippet_text:
                lines.append(f"- {match.path}: {snippet_text}")
            else:
                lines.append(f"- {match.path}")

        summary = (
            f"Found {len(matches)} match(es) for '{args.query}' (max {args.max_results})."
        )
        content = "\n".join(lines)

        return ToolResult(
            success=True,
            result_for_llm=f"{summary}\n{content}",
            ui_component=UiComponent(
                rich_component=CardComponent(
                    type=ComponentType.CARD,
                    title=f"Search results for '{args.query}'",
                    content=content,
                ),
                simple_component=SimpleTextComponent(text=summary),
            ),
        )


class ListFilesArgs(BaseModel):
    """Arguments for listing files."""
    directory: str = Field(default=".", description="Directory to list (defaults to current)")


class ListFilesTool(Tool[ListFilesArgs]):
    """Tool to list files in a directory using dependency injection for file system access."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        """Initialize with optional file system dependency."""
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files in a directory"

    def get_args_schema(self) -> Type[ListFilesArgs]:
        return ListFilesArgs

    async def execute(self, context: ToolContext, args: ListFilesArgs) -> ToolResult:
        try:
            files = await self.file_system.list_files(args.directory, context)

            if not files:
                result = f"No files found in directory '{args.directory}'"
                files_list = "No files found"
            else:
                files_list = "\n".join(f"- {f}" for f in files)
                result = f"Files in '{args.directory}':\n{files_list}"

            return ToolResult(
                success=True,
                result_for_llm=result,
                ui_component=UiComponent(
                    rich_component=CardComponent(
                        type=ComponentType.CARD,
                        title=f"Files in {args.directory}",
                        content=files_list,
                    ),
                    simple_component=SimpleTextComponent(text=result),
                )
            )
        except Exception as e:
            error_msg = f"Error listing files: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(e)
            )


class ReadFileArgs(BaseModel):
    """Arguments for reading a file."""
    filename: str = Field(description="Name of the file to read")


class ReadFileTool(Tool[ReadFileArgs]):
    """Tool to read file contents using dependency injection for file system access."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        """Initialize with optional file system dependency."""
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file"

    def get_args_schema(self) -> Type[ReadFileArgs]:
        return ReadFileArgs

    async def execute(self, context: ToolContext, args: ReadFileArgs) -> ToolResult:
        try:
            content = await self.file_system.read_file(args.filename, context)
            result = f"Content of '{args.filename}':\n\n{content}"

            return ToolResult(
                success=True,
                result_for_llm=result,
                ui_component=UiComponent(
                    rich_component=CardComponent(
                        type=ComponentType.CARD,
                        title=f"Contents of {args.filename}",
                        content=content,
                    ),
                    simple_component=SimpleTextComponent(text=f"File content:\n{content}"),
                )
            )
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(e)
            )


class WriteFileArgs(BaseModel):
    """Arguments for writing a file."""
    filename: str = Field(description="Name of the file to write")
    content: str = Field(description="Content to write to the file")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing files")


class WriteFileTool(Tool[WriteFileArgs]):
    """Tool to write content to a file using dependency injection for file system access."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        """Initialize with optional file system dependency."""
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file"

    def get_args_schema(self) -> Type[WriteFileArgs]:
        return WriteFileArgs

    async def execute(self, context: ToolContext, args: WriteFileArgs) -> ToolResult:
        try:
            await self.file_system.write_file(args.filename, args.content, context, args.overwrite)

            success_msg = f"Successfully wrote {len(args.content)} characters to '{args.filename}'"

            return ToolResult(
                success=True,
                result_for_llm=success_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="success",
                        message=f"File '{args.filename}' written successfully",
                    ),
                    simple_component=SimpleTextComponent(text=f"Wrote to {args.filename}"),
                )
            )
        except Exception as e:
            error_msg = f"Error writing file: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(e)
            )


class LineEdit(BaseModel):
    """Definition of a single line-based edit operation."""

    start_line: int = Field(ge=1, description="First line (1-based) affected by this edit")
    end_line: Optional[int] = Field(
        default=None,
        description=(
            "Last line (1-based, inclusive) to replace. Set to start_line - 1 to insert before start_line. "
            "Defaults to start_line, replacing a single line."
        ),
    )
    new_content: str = Field(default="", description="Replacement text (preserves provided newlines)")

    @model_validator(mode="after")
    def validate_line_range(self) -> "LineEdit":
        effective_end = self.start_line if self.end_line is None else self.end_line

        if effective_end < self.start_line - 1:
            raise ValueError("end_line must be >= start_line - 1")

        return self


class EditFileArgs(BaseModel):
    """Arguments for editing one or more sections within a file."""

    filename: str = Field(description="Path to the file to edit")
    edits: List[LineEdit] = Field(
        description="List of edits to apply. Later entries should reference higher line numbers.",
        min_length=1
    )


class EditFileTool(Tool[EditFileArgs]):
    """Tool to apply line-based edits to an existing file."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Modify specific lines within a file"

    def get_args_schema(self) -> Type[EditFileArgs]:
        return EditFileArgs

    async def execute(self, context: ToolContext, args: EditFileArgs) -> ToolResult:
        try:
            original_content = await self.file_system.read_file(args.filename, context)
        except Exception as exc:
            error_msg = f"Error loading file '{args.filename}': {exc}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(exc),
            )

        lines = original_content.splitlines(keepends=True)
        applied_edits: List[str] = []

        # Apply edits starting from the bottom so line numbers remain valid for each operation
        for edit in sorted(args.edits, key=lambda e: e.start_line, reverse=True):
            start_line = edit.start_line
            end_line = edit.end_line if edit.end_line is not None else edit.start_line

            if start_line < 1:
                return self._range_error(args.filename, start_line, end_line, "start_line must be >= 1")

            if end_line < start_line - 1:
                return self._range_error(
                    args.filename,
                    start_line,
                    end_line,
                    "end_line must be >= start_line - 1",
                )

            is_insertion = end_line == start_line - 1

            if not is_insertion and start_line > len(lines):
                return self._range_error(
                    args.filename,
                    start_line,
                    end_line,
                    f"start_line {start_line} is beyond the end of the file (len={len(lines)})",
                )

            if is_insertion:
                if start_line > len(lines) + 1:
                    return self._range_error(
                        args.filename,
                        start_line,
                        end_line,
                        "Cannot insert beyond one line past the end of the file",
                    )
                start_index = min(start_line - 1, len(lines))
                end_index = start_index
            else:
                if end_line > len(lines):
                    return self._range_error(
                        args.filename,
                        start_line,
                        end_line,
                        f"end_line {end_line} is beyond the end of the file (len={len(lines)})",
                    )
                start_index = start_line - 1
                end_index = end_line

            replacement_lines = edit.new_content.splitlines(keepends=True)
            lines[start_index:end_index] = replacement_lines

            if is_insertion:
                inserted_count = len(replacement_lines)
                applied_edits.append(
                    f"Inserted {inserted_count} line(s) at line {start_line}"
                )
            else:
                removed_count = end_line - start_line + 1
                applied_edits.append(
                    f"Replaced lines {start_line}-{end_line} (removed {removed_count} line(s))"
                )

        new_content = "".join(lines)

        if new_content == original_content:
            message = f"No changes applied to '{args.filename}' (content already up to date)."
            return ToolResult(
                success=True,
                result_for_llm=message,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="info",
                        message=message,
                    ),
                    simple_component=SimpleTextComponent(text=message),
                ),
            )

        try:
            await self.file_system.write_file(args.filename, new_content, context, overwrite=True)
        except Exception as exc:
            error_msg = f"Error writing updated contents to '{args.filename}': {exc}"
            return ToolResult(
                success=False,
                result_for_llm=error_msg,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_msg,
                    ),
                    simple_component=SimpleTextComponent(text=error_msg),
                ),
                error=str(exc),
            )

        diff_lines = list(
            difflib.unified_diff(
                original_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"a/{args.filename}",
                tofile=f"b/{args.filename}",
                lineterm="",
            )
        )

        diff_text = "\n".join(diff_lines) if diff_lines else "(No textual diff available)"
        summary = (
            f"Updated '{args.filename}' with {len(args.edits)} edit(s).\n" + "\n".join(reversed(applied_edits))
        )

        return ToolResult(
            success=True,
            result_for_llm=f"{summary}\n\n{diff_text}",
            ui_component=UiComponent(
                rich_component=CardComponent(
                    type=ComponentType.CARD,
                    title=f"Edited {args.filename}",
                    content=diff_text,
                ),
                simple_component=SimpleTextComponent(text=summary),
            ),
        )

    def _range_error(self, filename: str, start_line: int, end_line: int, message: str) -> ToolResult:
        error_msg = (
            f"Invalid edit range for '{filename}': start_line={start_line}, end_line={end_line}. {message}"
        )
        return ToolResult(
            success=False,
            result_for_llm=error_msg,
            ui_component=UiComponent(
                rich_component=NotificationComponent(
                    type=ComponentType.NOTIFICATION,
                    level="error",
                    message=error_msg,
                ),
                simple_component=SimpleTextComponent(text=error_msg),
            ),
            error=message,
        )


# Convenience function for creating tools with default local file system
def create_file_system_tools(file_system: Optional[FileSystem] = None) -> List[Tool[Any]]:
    """Create a set of file system tools with optional dependency injection."""
    fs = file_system or LocalFileSystem()
    return [
        ListFilesTool(fs),
        SearchFilesTool(fs),
        ReadFileTool(fs),
        WriteFileTool(fs),
        EditFileTool(fs),
    ]
