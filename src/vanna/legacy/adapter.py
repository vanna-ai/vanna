"""
Legacy VannaBase adapter for the Vanna Agents framework.

This module provides a LegacyVannaAdapter that bridges legacy VannaBase objects
with the new ToolRegistry system by auto-registering legacy methods as tools
with appropriate group-based access control.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..capabilities.agent_memory import AgentMemory, ToolMemory, MemorySearchResult
from ..capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from ..core.registry import ToolRegistry
from ..core.tool import Tool, ToolContext, ToolResult
from ..core.user import User
from ..tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from ..tools.run_sql import RunSqlTool
from .base.base import VannaBase


class LegacySqlRunner(SqlRunner):
    """SqlRunner implementation that wraps a legacy VannaBase instance.

    This class bridges the new SqlRunner interface with legacy VannaBase
    run_sql methods, allowing legacy database connections to work with
    the new tool-based architecture.
    """

    def __init__(self, vn: VannaBase):
        """Initialize with a legacy VannaBase instance.

        Args:
            vn: The legacy VannaBase instance with an initialized run_sql method
        """
        self.vn = vn

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query using the legacy VannaBase run_sql method.

        Args:
            args: SQL query arguments containing the SQL string
            context: Tool execution context (not used by legacy implementation)

        Returns:
            DataFrame with query results

        Raises:
            Exception: If query execution fails
        """
        # Call the legacy VannaBase run_sql method
        # The legacy method is synchronous, so we call it directly
        return self.vn.run_sql(args.sql)


class LegacyAgentMemory(AgentMemory):
    """AgentMemory implementation that wraps a legacy VannaBase instance.

    This class bridges the new AgentMemory interface with legacy VannaBase
    question-sql methods, allowing legacy training data storage to work with
    the new agent memory system.

    Note: This is a basic retrofit that maps agent memory operations to the
    legacy add_question_sql and get_similar_question_sql methods. Some features
    may not be fully supported.
    """

    def __init__(self, vn: VannaBase):
        """Initialize with a legacy VannaBase instance.

        Args:
            vn: The legacy VannaBase instance with training data methods
        """
        self.vn = vn

    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a tool usage pattern by storing it as a question-sql pair.

        Args:
            question: The user question
            tool_name: Name of the tool that was used
            args: Arguments passed to the tool
            context: Tool execution context (not used by legacy implementation)
            success: Whether the tool execution was successful
            metadata: Additional metadata (not used by legacy implementation)
        """
        # For legacy compatibility, we primarily care about SQL queries
        # Extract SQL from args if this was a run_sql tool
        if tool_name == "run_sql" and "sql" in args:
            sql = args["sql"]
            # Call the legacy add_question_sql method
            # The legacy method is synchronous, so we call it directly
            self.vn.add_question_sql(question=question, sql=sql)

    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None
    ) -> List[MemorySearchResult]:
        """Search for similar tool usage patterns using legacy question-sql lookup.

        Args:
            question: The question to search for
            context: Tool execution context (not used by legacy implementation)
            limit: Maximum number of results (not directly supported by legacy)
            similarity_threshold: Minimum similarity score (not directly supported by legacy)
            tool_name_filter: Filter by tool name (not directly supported by legacy)

        Returns:
            List of memory search results with similar question-sql pairs
        """
        # Call the legacy get_similar_question_sql method
        similar_results = self.vn.get_similar_question_sql(question=question)

        # Convert legacy results to MemorySearchResult format
        memory_results = []
        for idx, result in enumerate(similar_results):
            # Legacy results are typically dicts with 'question' and 'sql' keys
            if isinstance(result, dict) and "question" in result and "sql" in result:
                tool_memory = ToolMemory(
                    memory_id=None,  # Legacy doesn't provide IDs
                    question=result["question"],
                    tool_name="run_sql",
                    args={"sql": result["sql"]},
                    success=True
                )

                # Assign a simple rank-based similarity score
                # Legacy system doesn't provide actual similarity scores
                similarity_score = 1.0 - (idx * 0.1)  # Decreasing score by rank
                similarity_score = max(similarity_score, 0.0)

                memory_results.append(
                    MemorySearchResult(
                        memory=tool_memory,
                        similarity_score=similarity_score,
                        rank=idx + 1
                    )
                )

        return memory_results[:limit]

    async def get_recent_memories(
        self,
        context: ToolContext,
        limit: int = 10
    ) -> List[ToolMemory]:
        """Get recently added memories.

        Note: Legacy VannaBase does not provide a way to get recent memories,
        so this returns an empty list.

        Args:
            context: Tool execution context
            limit: Maximum number of memories to return

        Returns:
            Empty list (not supported by legacy)
        """
        return []

    async def delete_by_id(
        self,
        context: ToolContext,
        memory_id: str
    ) -> bool:
        """Delete a memory by its ID.

        Note: Legacy VannaBase does not provide a way to delete by ID,
        so this operation is not supported.

        Args:
            context: Tool execution context
            memory_id: ID of the memory to delete

        Returns:
            False (operation not supported by legacy)
        """
        return False

    async def clear_memories(
        self,
        context: ToolContext,
        tool_name: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> int:
        """Clear stored memories.

        Note: Legacy VannaBase does not provide a direct clear method,
        so this operation is not supported.

        Args:
            context: Tool execution context
            tool_name: Optional tool name filter
            before_date: Optional date filter

        Returns:
            0 (operation not supported by legacy)
        """
        return 0


class LegacyVannaAdapter(ToolRegistry):
    """Adapter that wraps a legacy VannaBase object and exposes its methods as tools.

    This adapter automatically registers specific VannaBase methods as tools in the
    registry with configurable group-based access control. This allows legacy Vanna
    instances to work seamlessly with the new Agents framework.

    Features:
    - Auto-registers legacy methods as tools
    - Configurable group-based permissions ('user', 'admin', etc.)
    - Seamless integration with ToolRegistry
    - Preserves legacy VannaBase functionality

    Example:
        ```python
        from vanna.legacy.base import VannaBase
        from vanna.legacy.adapter import LegacyVannaAdapter

        # Initialize your legacy Vanna instance
        vn = VannaBase(config={"model": "gpt-4"})
        vn.connect_to_postgres(...)

        # Create adapter and auto-register tools
        adapter = LegacyVannaAdapter(vn)

        # Tools are now available through the registry
        schemas = await adapter.get_schemas(user)
        ```
    """

    def __init__(
        self,
        vn: VannaBase,
        audit_logger: Optional[Any] = None,
        audit_config: Optional[Any] = None,
    ) -> None:
        """Initialize the adapter with a legacy VannaBase instance.

        Args:
            vanna: The legacy VannaBase instance to wrap
            audit_logger: Optional audit logger for tool execution tracking
            audit_config: Optional audit configuration
        """
        super().__init__(audit_logger=audit_logger, audit_config=audit_config)
        self.vn = vn
        self._register_tools()

    def _register_tools(self) -> None:
        """Register legacy VannaBase methods as tools with appropriate permissions.

        Registers the following tools:
        - RunSqlTool: Wraps the legacy run_sql method via LegacySqlRunner
        - SaveQuestionToolArgsTool: Wraps add_question_sql via LegacyAgentMemory
        - SearchSavedCorrectToolUsesTool: Wraps get_similar_question_sql via LegacyAgentMemory
        """
        # Create a LegacySqlRunner to wrap the VannaBase run_sql method
        sql_runner = LegacySqlRunner(self.vn)

        # Register the RunSqlTool with user and admin access
        run_sql_tool = RunSqlTool(sql_runner)
        self.register_local_tool(
            run_sql_tool,
            access_groups=['user', 'admin']
        )

        # Create a LegacyAgentMemory to wrap the VannaBase question-sql methods
        agent_memory = LegacyAgentMemory(self.vn)

        # Register memory tools
        # SaveQuestionToolArgsTool - for saving question-tool-args patterns (admin only)
        save_memory_tool = SaveQuestionToolArgsTool(agent_memory)
        self.register_local_tool(
            save_memory_tool,
            access_groups=['admin']
        )

        # SearchSavedCorrectToolUsesTool - for searching similar patterns (user and admin)
        search_memory_tool = SearchSavedCorrectToolUsesTool(agent_memory)
        self.register_local_tool(
            search_memory_tool,
            access_groups=['user', 'admin']
        )

    # Example stub for a tool wrapper (to be expanded)
    # You can copy and customize this pattern for each tool you want to expose
    """
    class ExampleTool(Tool[ExampleToolArgs]):
        def __init__(self, vanna: VannaBase):
            self.vanna = vanna

        @property
        def name(self) -> str:
            return "example_tool"

        @property
        def description(self) -> str:
            return "Example tool description"

        @property
        def access_groups(self) -> List[str]:
            # This is optional - will be overridden by register_local_tool
            return []

        def get_args_schema(self) -> type[ExampleToolArgs]:
            return ExampleToolArgs

        async def execute(
            self,
            context: ToolContext,
            args: ExampleToolArgs
        ) -> ToolResult:
            # Call the legacy VannaBase method
            result = self.vanna.example_method(args.param1, args.param2)

            return ToolResult(
                success=True,
                result_for_llm=result,
                ui_component=None,
            )
    """
