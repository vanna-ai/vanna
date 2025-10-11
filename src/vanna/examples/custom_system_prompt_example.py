"""
Example demonstrating custom system prompt builder with dependency injection.

This example shows how to create a custom SystemPromptBuilder that dynamically
generates system prompts based on user context and available tools.

Usage:
  python -m vanna.examples.custom_system_prompt_example
"""

from typing import List, Optional

from vanna.core.interfaces import SystemPromptBuilder
from vanna.core.models import ToolSchema, User


class CustomSystemPromptBuilder(SystemPromptBuilder):
    """Custom system prompt builder that personalizes prompts based on user."""

    async def build_system_prompt(
        self, user: User, tools: List[ToolSchema]
    ) -> Optional[str]:
        """Build a personalized system prompt.

        Args:
            user: The user making the request
            tools: List of tools available to the user

        Returns:
            Personalized system prompt
        """
        # Build personalized greeting
        username = user.username or user.id
        greeting = f"Hello {username}! I'm your AI assistant."

        # Add role-specific instructions based on user permissions
        role_instructions = []
        if "admin" in user.permissions:
            role_instructions.append(
                "As an admin user, you have access to all tools and capabilities."
            )
        elif "analyst" in user.permissions:
            role_instructions.append(
                "You're working as an analyst. I'll help you query and visualize data."
            )
        else:
            role_instructions.append("I'm here to help you with your tasks.")

        # List available tools
        tool_info = []
        if tools:
            tool_info.append("\nAvailable tools:")
            for tool in tools:
                tool_info.append(f"- {tool.name}: {tool.description}")

        # Combine all parts
        parts = [greeting] + role_instructions + tool_info
        return "\n".join(parts)


class SQLAssistantSystemPromptBuilder(SystemPromptBuilder):
    """System prompt builder specifically for SQL database assistants."""

    def __init__(self, database_name: str = "database"):
        """Initialize with database context.

        Args:
            database_name: Name of the database being queried
        """
        self.database_name = database_name

    async def build_system_prompt(
        self, user: User, tools: List[ToolSchema]
    ) -> Optional[str]:
        """Build a SQL-focused system prompt.

        Args:
            user: The user making the request
            tools: List of tools available to the user

        Returns:
            SQL-focused system prompt
        """
        prompt = f"""You are an expert SQL database assistant for the {self.database_name} database.

Your primary responsibilities:
1. Write efficient, correct SQL queries
2. Explain query results clearly
3. Suggest optimizations when relevant
4. Visualize data when appropriate

Guidelines:
- Always validate SQL syntax before execution
- Use appropriate JOINs and avoid Cartesian products
- Limit result sets to reasonable sizes by default
- Format numbers and dates for readability
"""

        # Add tool-specific instructions
        has_viz_tool = any(tool.name == "visualize_data" for tool in tools)
        if has_viz_tool:
            prompt += "\n- Create visualizations for numerical data when it helps understanding"

        return prompt


async def demo() -> None:
    """Demonstrate custom system prompt builders."""
    from vanna import Agent, User
    from vanna.core.registry import ToolRegistry
    from vanna.integrations.anthropic.mock import MockLlmService

    # Example 1: Custom personalized system prompt
    print("=" * 60)
    print("Example 1: Custom Personalized System Prompt")
    print("=" * 60)

    custom_builder = CustomSystemPromptBuilder()
    admin_user = User(
        id="user-1",
        username="Alice",
        permissions=["admin"]
    )

    # Simulate some tools
    mock_tools = [
        ToolSchema(
            name="query_database",
            description="Query the SQL database",
            parameters={}
        ),
        ToolSchema(
            name="visualize_data",
            description="Create data visualizations",
            parameters={}
        ),
    ]

    prompt = await custom_builder.build_system_prompt(admin_user, mock_tools)
    print("\nGenerated system prompt for admin user:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)

    # Example 2: SQL-specific system prompt
    print("\n" + "=" * 60)
    print("Example 2: SQL Assistant System Prompt")
    print("=" * 60)

    sql_builder = SQLAssistantSystemPromptBuilder(database_name="Chinook")
    analyst_user = User(
        id="user-2",
        username="Bob",
        permissions=["analyst"]
    )

    prompt = await sql_builder.build_system_prompt(analyst_user, mock_tools)
    print("\nGenerated system prompt for SQL assistant:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)

    # Example 3: Using custom builder with Agent
    print("\n" + "=" * 60)
    print("Example 3: Using Custom Builder with Agent")
    print("=" * 60)

    mock_llm = MockLlmService()
    tool_registry = ToolRegistry()

    agent = Agent(
        llm_service=mock_llm,
        tool_registry=tool_registry,
        system_prompt_builder=sql_builder  # Inject custom builder here
    )

    print("\nAgent created with custom SQL system prompt builder!")
    print("The agent will now use the SQL-focused system prompt for all interactions.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
