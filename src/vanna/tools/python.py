"""Python-specific tooling built on top of the file system service."""

from __future__ import annotations

import shlex
import sys
from typing import Any, List, Optional, Sequence, Type

from pydantic import BaseModel, Field

from vanna.components import (
    UiComponent,
    CardComponent,
    ComponentType,
    NotificationComponent,
    SimpleTextComponent,
)
from vanna.core.tool import Tool, ToolContext, ToolResult

from .file_system import CommandResult, FileSystem, LocalFileSystem

MAX_OUTPUT_LENGTH = 4000


class RunPythonFileArgs(BaseModel):
    """Arguments required to execute a Python file."""

    filename: str = Field(description="Python file to execute (relative to the workspace root)")
    arguments: Sequence[str] = Field(
        default_factory=list,
        description="Optional arguments to pass to the Python script",
    )
    timeout_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional timeout for the command in seconds",
    )


class RunPythonFileTool(Tool[RunPythonFileArgs]):
    """Execute a Python file using the provided file system service."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "run_python_file"

    @property
    def description(self) -> str:
        return "Execute a Python file using the workspace interpreter"

    def get_args_schema(self) -> Type[RunPythonFileArgs]:
        return RunPythonFileArgs

    async def execute(self, context: ToolContext, args: RunPythonFileArgs) -> ToolResult:
        exists = await self.file_system.exists(args.filename, context)
        if not exists:
            message = f"Cannot execute '{args.filename}' because it does not exist."
            return _error_result(message)

        command_parts = [sys.executable, args.filename]
        command_parts.extend(args.arguments)
        command = _quote_command(command_parts)

        try:
            result = await self.file_system.run_bash(
                command,
                context,
                timeout=args.timeout_seconds,
            )
        except TimeoutError as exc:
            message = str(exc)
            return _error_result(message)

        summary = (
            f"Executed python {args.filename} (exit code {result.returncode})."
        )
        success = result.returncode == 0
        return _result_from_command(summary, command, result, success=success)


class PipInstallArgs(BaseModel):
    """Arguments required to run pip install."""

    packages: List[str] = Field(
        description="Packages (with optional specifiers) to install",
        min_length=1
    )
    upgrade: bool = Field(
        default=False,
        description="Whether to include --upgrade in the pip invocation",
    )
    extra_args: Sequence[str] = Field(
        default_factory=list,
        description="Additional arguments to pass to pip install",
    )
    timeout_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional timeout for the command in seconds",
    )


class PipInstallTool(Tool[PipInstallArgs]):
    """Install Python packages using pip inside the workspace environment."""

    def __init__(self, file_system: Optional[FileSystem] = None):
        self.file_system = file_system or LocalFileSystem()

    @property
    def name(self) -> str:
        return "pip_install"

    @property
    def description(self) -> str:
        return "Install Python packages using pip"

    def get_args_schema(self) -> Type[PipInstallArgs]:
        return PipInstallArgs

    async def execute(self, context: ToolContext, args: PipInstallArgs) -> ToolResult:
        command_parts = [sys.executable, "-m", "pip", "install"]
        if args.upgrade:
            command_parts.append("--upgrade")
        command_parts.extend(args.packages)
        command_parts.extend(args.extra_args)
        command = _quote_command(command_parts)

        try:
            result = await self.file_system.run_bash(
                command,
                context,
                timeout=args.timeout_seconds,
            )
        except TimeoutError as exc:
            return _error_result(str(exc))

        success = result.returncode == 0
        summary = (
            "pip install completed successfully"
            if success
            else f"pip install failed (exit code {result.returncode})."
        )

        return _result_from_command(summary, command, result, success=success)


def create_python_tools(file_system: Optional[FileSystem] = None) -> List[Tool[Any]]:
    """Create Python-specific tools backed by a shared file system service."""

    fs = file_system or LocalFileSystem()
    return [
        RunPythonFileTool(fs),
        PipInstallTool(fs),
    ]


def _quote_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _truncate(text: str, limit: int = MAX_OUTPUT_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}…"


def _result_from_command(
    summary: str,
    command: str,
    result: CommandResult,
    *,
    success: bool = True,
) -> ToolResult:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    blocks: List[str] = [f"$ {command}"]
    if stdout:
        blocks.append("STDOUT:\n" + _truncate(stdout))
    if stderr:
        blocks.append("STDERR:\n" + _truncate(stderr))
    if not stdout and not stderr:
        blocks.append("(no output)")

    content = "\n\n".join(blocks)
    card_status = "success" if success else "error"
    component = CardComponent(
        type=ComponentType.CARD,
        title="Command Result",
        content=content,
        status=card_status,
    )

    return ToolResult(
        success=success,
        result_for_llm=f"{summary}\n\n{content}",
        ui_component=UiComponent(
            rich_component=component,
            simple_component=SimpleTextComponent(text=summary),
        ),
        error=None if success else content,
    )


def _error_result(message: str) -> ToolResult:
    return ToolResult(
        success=False,
        result_for_llm=message,
        ui_component=UiComponent(
            rich_component=NotificationComponent(
                type=ComponentType.NOTIFICATION,
                level="error",
                message=message,
            ),
            simple_component=SimpleTextComponent(text=message),
        ),
        error=message,
    )
