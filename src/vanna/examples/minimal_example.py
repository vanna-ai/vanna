"""Minimal Claude + SQLite example ready for FastAPI."""

from __future__ import annotations

import os
from pathlib import Path

from vanna import AgentConfig, Agent
from vanna.core.registry import ToolRegistry
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local import LocalFileSystem
from vanna.tools import (
    RunSqlTool,
    # Visualization
    VisualizeDataTool,
    # Python execution
    RunPythonFileTool,
    PipInstallTool,
    # File system (for coding agents)
    SearchFilesTool,
    ListFilesTool,
    ReadFileTool,
    WriteFileTool,
)

_DB = Path(__file__).resolve().parents[2] / "Chinook.sqlite"


def create_demo_agent() -> Agent:
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    llm = AnthropicLlmService(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"))

    # Shared file system for all tools
    file_system = LocalFileSystem("./claude_data")

    tools = ToolRegistry()

    # 1. Basic SQL agent - query databases
    tools.register(
        RunSqlTool(
            sql_runner=SqliteRunner(database_path=str(_DB)),
            file_system=file_system,
        )
    )

    # 2. Add visualization - create charts from data
    tools.register(VisualizeDataTool(file_system=file_system))

    # 3. Add Python execution - build dashboards with artifacts
    # tools.register(RunPythonFileTool(file_system=file_system))
    # tools.register(PipInstallTool(file_system=file_system))

    # 4. Full coding agent - read, write, search files
    # tools.register(SearchFilesTool(file_system=file_system))
    # tools.register(ListFilesTool(file_system=file_system))
    # tools.register(ReadFileTool(file_system=file_system))
    # tools.register(WriteFileTool(file_system=file_system))

    return Agent(
        llm_service=llm,
        tool_registry=tools,
    )
