"""
Mock example showing how to use the SQL query tool with the Chinook database.

This example demonstrates using the RunSqlTool with SqliteRunner and a mock LLM service
that automatically executes sample SQL queries against the Chinook database.

Usage:
  Template: Copy this file and modify for your custom database
  Interactive: python -m vanna.examples.mock_sqlite_example
  REPL: from vanna.examples.mock_sqlite_example import create_demo_agent
  Server: python -m vanna.servers --example mock_sqlite_example
"""

import asyncio
import os
import random
import uuid
from typing import AsyncGenerator, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from vanna import (
    AgentConfig,
    Agent,
    Tool,
    ToolContext,
    ToolRegistry,
    ToolResult,
    User,
    UiComponent,
)
from vanna.core.interfaces import LlmService
from vanna.core.models import (
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
    ToolCall,
    ToolSchema,
)
from vanna.core.rich_components import (
    CardComponent,
    NotificationComponent,
    ComponentType,
)
from vanna.core.simple_components import (
    SimpleTextComponent,
)
from vanna.tools import RunSqlTool
from vanna.integrations.sqlite import SqliteRunner


class MockSqliteLlmService(LlmService):
    """LLM service that exercises the SQLite query tool with sample queries."""

    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random(seed)
        self._sample_queries = [
            "SELECT name FROM sqlite_master WHERE type='table'",
            "SELECT COUNT(*) as total_customers FROM Customer",
            "SELECT FirstName, LastName FROM Customer LIMIT 5",
            "SELECT Name, Composer FROM Track WHERE Composer IS NOT NULL LIMIT 5",
            "SELECT COUNT(*) as album_count FROM Album",
            "SELECT Name FROM Artist LIMIT 10",
            "SELECT AVG(Total) as avg_invoice_total FROM Invoice",
            "SELECT GenreId, COUNT(*) as track_count FROM Track GROUP BY GenreId LIMIT 5",
        ]

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Handle non-streaming SQLite interactions."""
        await asyncio.sleep(0.1)
        return self._build_response(request)

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Provide streaming compatibility by yielding a single chunk."""
        await asyncio.sleep(0.1)
        response = self._build_response(request)

        if response.tool_calls:
            yield LlmStreamChunk(tool_calls=response.tool_calls)
        if response.content is not None:
            yield LlmStreamChunk(content=response.content, finish_reason=response.finish_reason)
        else:
            yield LlmStreamChunk(finish_reason=response.finish_reason)

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Mock validation - no errors."""
        return []

    def _build_response(self, request: LlmRequest) -> LlmResponse:
        """Create a response that either calls the tool or explains its result."""
        last_message = request.messages[-1] if request.messages else None

        if last_message and last_message.role == "tool":
            # Respond to tool result
            result = last_message.content or "No result provided"
            return LlmResponse(
                content=f"Here's what I found in the database:\n\n{result}",
                finish_reason="stop",
                usage={"prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60},
            )

        # Generate a random SQL query
        sql_query = self._random.choice(self._sample_queries)
        tool_call = ToolCall(
            id=f"call_{uuid.uuid4().hex[:8]}",
            name="run_sql",
            arguments={"sql": sql_query},
        )

        return LlmResponse(
            content="Let me query the Chinook database for you...",
            tool_calls=[tool_call],
            finish_reason="tool_calls",
            usage={"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
        )


def create_demo_agent() -> Agent:
    """Create a demo agent with SQLite query tool.

    Returns:
        Configured Agent with SQLite tool and mock LLM
    """
    # Get the path to the Chinook database
    database_path = os.path.join(os.path.dirname(__file__), "..", "..", "Chinook.sqlite")
    database_path = os.path.abspath(database_path)

    if not os.path.exists(database_path):
        raise FileNotFoundError(f"Chinook database not found at {database_path}. Please download it from https://vanna.ai/Chinook.sqlite")

    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner)
    tool_registry.register(sql_tool)

    llm_service = MockSqliteLlmService()

    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        config=AgentConfig(
            stream_responses=False,
            include_thinking_indicators=False,
        ),
    )


async def main() -> None:
    """Run the mock SQLite example."""

    # Create agent using factory function
    agent = create_demo_agent()
    tool_registry = agent.tool_registry

    # Create a test user
    user = User(id="user123", username="testuser", permissions=[])

    # Test the tool directly
    print("Testing SQL tool directly:")
    tool_call = ToolCall(
        id="test123",
        name="run_sql",
        arguments={"sql": "SELECT name FROM sqlite_master WHERE type='table'"}
    )

    context = ToolContext(user=user, conversation_id="test", request_id="test")

    result = await tool_registry.execute(tool_call, context)
    print(f"Tables in database:\n{result.result_for_llm if result.success else result.error}")

    # Show available tools
    schemas = await tool_registry.get_schemas(user)
    print(
        f"\nAvailable tools for user: {[schema.name for schema in schemas]}"
    )

    # Demonstrate the mock LLM triggering SQL queries
    print("\n" + "="*50)
    print("Agent conversation demo:")
    print("="*50)

    conversation_id = "sqlite-demo"

    # Run multiple queries to show different results
    for i in range(3):
        print(f"\n--- Query {i+1} ---")
        async for component in agent.send_message(
            user=user,
            message=f"Show me some data from the database (query {i+1})",
            conversation_id=conversation_id
        ):
            if hasattr(component.rich_component, "content") and component.rich_component.content:
                print(f"Assistant: {component.rich_component.content}")
            elif component.simple_component and hasattr(component.simple_component, "text"):
                print(f"Assistant: {component.simple_component.text}")


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting mock SQLite example...")
    print("This example uses the Chinook database to demonstrate SQL queries.")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()