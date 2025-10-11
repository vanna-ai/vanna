"""
Claude example using the SQL query tool with the Chinook database.

This example demonstrates using the RunSqlTool with SqliteRunner and Claude's AI
to intelligently query and analyze the Chinook database, with automatic visualization support.

Requirements:
- ANTHROPIC_API_KEY environment variable or .env file
- anthropic package: pip install -e .[anthropic]
- plotly package: pip install -e .[visualization]

Usage:
  PYTHONPATH=. python vanna/examples/claude_sqlite_example.py
"""

import asyncio
import importlib.util
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vanna import Agent


def ensure_env() -> None:
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv

        # Load from local .env without overriding existing env
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
    else:
        print(
            "[warn] python-dotenv not installed; skipping .env load. Install with: pip install python-dotenv"
        )

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "[error] ANTHROPIC_API_KEY is not set. Add it to your environment or .env file."
        )
        sys.exit(1)


async def main() -> None:
    ensure_env()

    try:
        from vanna.integrations.anthropic import AnthropicLlmService
    except ImportError:
        print(
            "[error] anthropic extra not installed. Install with: pip install -e .[anthropic]"
        )
        raise

    from vanna import AgentConfig, Agent
    from vanna.core.registry import ToolRegistry
    from vanna.core.user import CookieEmailUserResolver, RequestContext
    from vanna.integrations.sqlite import SqliteRunner
    from vanna.tools import (
        RunSqlTool,
        VisualizeDataTool,
        LocalFileSystem,
    )

    # Get the path to the Chinook database
    database_path = os.path.join(os.path.dirname(__file__), "..", "..", "Chinook.sqlite")
    database_path = os.path.abspath(database_path)

    if not os.path.exists(database_path):
        print(f"[error] Chinook database not found at {database_path}")
        print("Please download it with: curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite")
        sys.exit(1)

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    print(f"Using Anthropic model: {model}")
    print(f"Using database: {database_path}")

    llm = AnthropicLlmService(model=model)

    # Create shared FileSystem for both tools
    file_system = LocalFileSystem(working_directory="./claude_data")

    # Create tool registry and register the SQL tool with SQLite runner
    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner, file_system=file_system)
    tool_registry.register(sql_tool)

    # Register visualization tool
    try:
        viz_tool = VisualizeDataTool(file_system=file_system)
        tool_registry.register(viz_tool)
        print("Visualization tool enabled")
    except ImportError:
        print("[warn] Plotly not installed. Visualization tool disabled. Install with: pip install -e .[visualization]")

    user_resolver = CookieEmailUserResolver()

    agent = Agent(
        llm_service=llm,
        config=AgentConfig(stream_responses=False),
        tool_registry=tool_registry,
        user_resolver=user_resolver,
    )

    # Simulate a logged-in demo user via cookie-based resolver
    request_context = RequestContext(
        cookies={user_resolver.cookie_name: "demo-user@example.com"},
        metadata={"demo": True},
        remote_addr="127.0.0.1",
    )
    conversation_id = "claude-sqlite-demo"

    # Sample queries to demonstrate different capabilities
    sample_questions = [
        "What tables are in this database?",
        "Show me the first 5 customers with their names",
        "What's the total number of tracks in the database?",
        "Find the top 5 artists by number of albums",
        "What's the average invoice total?",
        "Get data on the top 10 longest tracks and then visualize it",
    ]

    print("\n" + "="*60)
    print("Claude SQLite Database Assistant Demo")
    print("="*60)
    print("This demo shows Claude querying the Chinook music database.")
    print("Claude will intelligently construct SQL queries to answer questions")
    print("and can create visualizations of the results.")
    print()

    for i, question in enumerate(sample_questions, 1):
        print(f"\n--- Question {i}: {question} ---")

        async for component in agent.send_message(
            request_context=request_context,
            message=question,
            conversation_id=conversation_id,
        ):
            # Handle different component types
            if hasattr(component, "simple_component") and component.simple_component:
                if hasattr(component.simple_component, "text"):
                    print("Assistant:", component.simple_component.text)
            elif hasattr(component, "rich_component") and component.rich_component:
                if hasattr(component.rich_component, "content") and component.rich_component.content:
                    print("Assistant:", component.rich_component.content)
            elif hasattr(component, "content") and component.content:
                print("Assistant:", component.content)

        print()  # Add spacing between questions

    print("\n" + "="*60)
    print("Demo complete! Claude successfully queried the database.")
    print("="*60)


def create_demo_agent() -> "Agent":
    """Create a demo agent with Claude and SQLite query tool.

    This function is called by the vanna server framework.

    Returns:
        Configured Agent with Claude LLM and SQLite tool
    """
    ensure_env()

    try:
        from vanna.integrations.anthropic import AnthropicLlmService
    except ImportError:
        print(
            "[error] anthropic extra not installed. Install with: pip install -e .[anthropic]"
        )
        raise

    from vanna import AgentConfig, Agent
    from vanna.core.registry import ToolRegistry
    from vanna.core.user import CookieEmailUserResolver
    from vanna.integrations.sqlite import SqliteRunner
    from vanna.tools import (
        RunSqlTool,
        VisualizeDataTool,
        LocalFileSystem,
    )

    # Get the path to the Chinook database
    database_path = os.path.join(os.path.dirname(__file__), "..", "..", "Chinook.sqlite")
    database_path = os.path.abspath(database_path)

    if not os.path.exists(database_path):
        raise FileNotFoundError(f"Chinook database not found at {database_path}. Please download it from https://vanna.ai/Chinook.sqlite")

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    llm = AnthropicLlmService(model=model)

    # Create shared FileSystem for both tools
    file_system = LocalFileSystem(working_directory="./claude_data")

    # Create tool registry and register the SQL tool with SQLite runner
    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner, file_system=file_system)
    tool_registry.register(sql_tool)

    # Register visualization tool if available
    try:
        viz_tool = VisualizeDataTool(file_system=file_system)
        tool_registry.register(viz_tool)
    except ImportError:
        pass  # Visualization tool not available

    user_resolver = CookieEmailUserResolver()

    return Agent(
        llm_service=llm,
        config=AgentConfig(stream_responses=True),  # Enable streaming for web interface
        tool_registry=tool_registry,
        user_resolver=user_resolver,
    )


if __name__ == "__main__":
    asyncio.run(main())
