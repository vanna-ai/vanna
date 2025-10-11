"""
Example demonstrating SQL query execution with automatic visualization.

This example shows the integration of RunSqlTool and VisualizeDataTool,
demonstrating how SQL results are saved to CSV files and can be visualized
using the visualization tool with dependency injection.

Usage:
  PYTHONPATH=. python vanna/examples/visualization_example.py
"""

import asyncio
import os
import sys
import uuid
from typing import AsyncGenerator, List, Optional

from vanna import (
    AgentConfig,
    Agent,
    ToolRegistry,
    User,
)
from vanna.core import LlmService
from vanna.core import (
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
    ToolCall,
    ToolSchema,
)
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools import (
    RunSqlTool,
    VisualizeDataTool,
    LocalFileSystem,
)


class VisualizationDemoLlmService(LlmService):
    """Mock LLM that demonstrates SQL query and visualization workflow."""

    def __init__(self) -> None:
        self.step = 0
        self.csv_filename: Optional[str] = None

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Handle non-streaming requests."""
        await asyncio.sleep(0.1)
        return self._build_response(request)

    async def stream_request(self, request: LlmRequest) -> AsyncGenerator[LlmStreamChunk, None]:
        """Handle streaming requests."""
        await asyncio.sleep(0.1)
        response = self._build_response(request)

        if response.tool_calls:
            yield LlmStreamChunk(tool_calls=response.tool_calls)
        if response.content:
            yield LlmStreamChunk(content=response.content, finish_reason=response.finish_reason)
        else:
            yield LlmStreamChunk(finish_reason=response.finish_reason)

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tools - no errors."""
        return []

    def _build_response(self, request: LlmRequest) -> LlmResponse:
        """Build response based on conversation state."""
        last_message = request.messages[-1] if request.messages else None

        # If we got a tool result, process it
        if last_message and last_message.role == "tool":
            tool_result = last_message.content or ""

            # Check if this was a SQL query result with a CSV file
            if "Results saved to" in tool_result and ".csv" in tool_result:
                # Extract filename from result
                import re
                match = re.search(r"'([^']*\.csv)'", tool_result)
                if match:
                    self.csv_filename = match.group(1)
                    # Now visualize the data
                    return LlmResponse(
                        content=f"Great! I've saved the query results. Now let me create a visualization of the data.",
                        tool_calls=[ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name="visualize_data",
                            arguments={"filename": self.csv_filename}
                        )],
                        finish_reason="tool_calls"
                    )

            # If this was a visualization result, acknowledge it
            if "Created visualization" in tool_result:
                return LlmResponse(
                    content=f"Perfect! I've created a visualization of the data. {tool_result}",
                    finish_reason="stop"
                )

            # Default acknowledgment
            return LlmResponse(
                content=f"I've completed the operation. {tool_result}",
                finish_reason="stop"
            )

        # Initial request - run SQL query
        if self.step == 0:
            self.step += 1
            return LlmResponse(
                content="I'll query the database for you and then create a visualization.",
                tool_calls=[ToolCall(
                    id=f"call_{uuid.uuid4().hex[:8]}",
                    name="run_sql",
                    arguments={"sql": "SELECT Name, Milliseconds, Bytes FROM Track LIMIT 20"}
                )],
                finish_reason="tool_calls"
            )

        # Default response
        return LlmResponse(
            content="I can help you query databases and visualize the results.",
            finish_reason="stop"
        )


def create_demo_agent() -> Agent:
    """
    Create a demo agent with SQL and visualization tools.

    This function is called by the vanna server framework.

    Returns:
        Configured Agent with SQL and visualization tools
    """
    # Check for Chinook database
    database_path = os.path.join(os.path.dirname(__file__), "..", "..", "Chinook.sqlite")
    database_path = os.path.abspath(database_path)

    if not os.path.exists(database_path):
        raise FileNotFoundError(
            f"Chinook database not found at {database_path}. "
            "Please download it from https://vanna.ai/Chinook.sqlite"
        )

    # Create shared FileSystem for both tools
    file_system = LocalFileSystem(working_directory="./data_storage")

    # Create SQL tool with FileSystem
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner, file_system=file_system)

    # Create visualization tool with same FileSystem
    viz_tool = VisualizeDataTool(file_system=file_system)

    # Create tool registry
    tool_registry = ToolRegistry()
    tool_registry.register(sql_tool)
    tool_registry.register(viz_tool)

    # Create LLM service
    llm_service = VisualizationDemoLlmService()

    # Create agent with streaming enabled for web interface
    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=False,
        ),
    )


async def main() -> None:
    """Demonstrate SQL query execution with automatic visualization."""
    print("🎨 SQL + Visualization Demo")
    print("=" * 60)
    print("This example demonstrates:")
    print("1. Running SQL queries that save results to CSV files")
    print("2. Automatically visualizing the CSV data")
    print("3. User isolation for file storage")
    print("=" * 60)
    print()

    # Create agent using factory function
    agent = create_demo_agent()

    # Create test user
    user = User(id="demo-user", username="demo")

    # Show available tools
    tools = await agent.get_available_tools(user)
    print(f"Available tools: {[tool.name for tool in tools]}")
    print()

    # Run conversation
    conversation_id = "viz-demo"

    print("User: Show me some track data and visualize it")
    print()

    async for component in agent.send_message(
            user=user,
            message="Show me some track data and visualize it",
            conversation_id=conversation_id
        ):
        if component.simple_component and hasattr(component.simple_component, 'text') and component.simple_component.text:
            print(f"Agent: {component.simple_component.text}")
        elif component.simple_component and hasattr(component.simple_component, 'text'):
            print(f"Agent: {component.simple_component.text}")
        elif hasattr(component.rich_component, 'content'):
            if isinstance(component.rich_component.content, dict):
                # This is the chart
                print(f"Agent: [Chart Generated - Plotly figure with {len(str(component.rich_component.content))} chars]")
            else:
                print(f"Agent: {component.rich_component.content}")

    print()
    print("=" * 60)
    print("Demo complete!")
    print()
    print("Key features demonstrated:")
    print("✅ SQL queries save results to user-isolated CSV files")
    print("✅ Visualization tool reads CSV files using FileSystem")
    print("✅ Automatic chart type selection based on data shape")
    print("✅ Dependency injection allows customization")
    print()


if __name__ == "__main__":
    asyncio.run(main())
