"""
Example demonstrating how to use ToolRegistry.transform_args for user-specific
argument transformation, such as applying row-level security (RLS) to SQL queries.

This example shows:
1. Creating a custom ToolRegistry subclass that overrides transform_args
2. Applying RLS transformation to SQL queries based on user context
3. Rejecting tool execution when validation fails
"""

from typing import Union
from pydantic import BaseModel

from vanna.core import ToolRegistry
from vanna.core.tool import Tool, ToolContext, ToolRejection, ToolResult
from vanna.core.user import User


# Example: SQL execution tool arguments
class SQLExecutionArgs(BaseModel):
    query: str
    database: str = "default"


class SQLExecutionTool(Tool[SQLExecutionArgs]):
    @property
    def name(self) -> str:
        return "execute_sql"

    @property
    def description(self) -> str:
        return "Execute a SQL query against the database"

    def get_args_schema(self):
        return SQLExecutionArgs

    async def execute(self, context: ToolContext, args: SQLExecutionArgs) -> ToolResult:
        # Execute the SQL query (implementation not shown)
        return ToolResult(
            success=True,
            result_for_llm=f"Executed query: {args.query[:50]}...",
        )


class RLSToolRegistry(ToolRegistry):
    """Custom ToolRegistry that applies row-level security to SQL queries."""

    async def transform_args(
        self,
        tool: Tool,
        args,
        user: User,
        context: ToolContext,
    ) -> Union[SQLExecutionArgs, ToolRejection]:
        """Apply row-level security transformation to SQL queries."""

        # Only transform SQL execution tools
        if tool.name == "execute_sql" and isinstance(args, SQLExecutionArgs):
            original_query = args.query.strip()

            # Example 1: Reject queries that try to access restricted tables
            if "restricted_table" in original_query.lower():
                return ToolRejection(
                    reason="Access to 'restricted_table' is not permitted for your user group"
                )

            # Example 2: Apply RLS by modifying the WHERE clause
            # This is a simplified example - real RLS would be more sophisticated
            if "SELECT" in original_query.upper() and "users" in original_query.lower():
                # Add a WHERE clause to filter by user's organization
                user_org_id = user.metadata.get("organization_id")

                if user_org_id:
                    # Simple RLS: append WHERE clause for organization filtering
                    if "WHERE" in original_query.upper():
                        transformed_query = original_query.replace(
                            "WHERE",
                            f"WHERE organization_id = {user_org_id} AND",
                            1
                        )
                    else:
                        # Add WHERE clause before ORDER BY, LIMIT, etc.
                        transformed_query = original_query.rstrip(";")
                        transformed_query += f" WHERE organization_id = {user_org_id}"

                    # Return transformed arguments
                    return args.model_copy(update={"query": transformed_query})

            # Example 3: Validate required parameters
            if not args.database:
                return ToolRejection(
                    reason="Database parameter is required for SQL execution"
                )

        # For all other tools or if no transformation needed, pass through
        return args


# Usage example
async def example_usage():
    """Demonstrate using the RLS-enabled ToolRegistry."""
    from vanna.capabilities.agent_memory import AgentMemory

    # Create registry and register tool
    registry = RLSToolRegistry()
    sql_tool = SQLExecutionTool()
    registry.register_local_tool(sql_tool, access_groups=[])

    # Create a user with organization context
    user = User(
        user_id="user123",
        metadata={"organization_id": 42}
    )

    # Create tool context
    context = ToolContext(
        user=user,
        conversation_id="conv123",
        request_id="req123",
        agent_memory=AgentMemory(),
    )

    # Example 1: Query that will be transformed with RLS
    from vanna.core.tool import ToolCall

    tool_call = ToolCall(
        id="call1",
        name="execute_sql",
        arguments={
            "query": "SELECT * FROM users",
            "database": "production"
        }
    )

    result = await registry.execute(tool_call, context)
    print(f"Result: {result.result_for_llm}")
    # The query will be transformed to: SELECT * FROM users WHERE organization_id = 42

    # Example 2: Query that will be rejected
    tool_call_rejected = ToolCall(
        id="call2",
        name="execute_sql",
        arguments={
            "query": "SELECT * FROM restricted_table",
            "database": "production"
        }
    )

    result = await registry.execute(tool_call_rejected, context)
    print(f"Rejected: {result.error}")
    # Will return: "Access to 'restricted_table' is not permitted for your user group"


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
