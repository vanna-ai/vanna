#!/usr/bin/env python3
"""
Vanna Agent Manager - Persistent Agent with Shared Memory

Manages a singleton Vanna agent instance that persists across requests,
enabling learning from successful queries and improving over time.

Key features:
- Shared agent memory across all users
- Learns from successful query patterns
- Pre-populated with training data
- Thread-safe for concurrent requests
"""

import os
import asyncio
import sqlite3
import logging
from typing import Optional, Dict, Any
import pandas as pd
from threading import Lock

# Configure logger
logger = logging.getLogger("vanna_manager")
logger.setLevel(logging.INFO)


class VannaAgentManager:
    """
    Singleton manager for Vanna agent with persistent memory.

    This ensures:
    1. Single agent instance shared across all requests
    2. Memory persists and learns from all user queries
    3. Thread-safe concurrent access
    4. Training data pre-loaded
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the Vanna agent manager (only once)."""
        if self._initialized:
            return

        self._initialized = True
        self._agent = None
        self._agent_memory = None
        self._query_count = 0

        logger.info("🔧 Initializing Vanna Agent Manager...")

    def initialize_agent(
        self,
        database_path: str,
        table_name: str = "staffing_table",
        load_training_data: bool = True
    ) -> None:
        """
        Initialize the Vanna agent with persistent memory.

        Args:
            database_path: Path to SQLite database
            table_name: Name of staffing table
            load_training_data: Whether to pre-populate with training examples
        """
        with self._lock:
            if self._agent is not None:
                logger.info("✅ Agent already initialized")
                return

            try:
                from vanna.integrations.anthropic import AnthropicLlmService
                from vanna import Agent, AgentConfig
                from vanna.core.registry import ToolRegistry
                from vanna.core.user import CookieEmailUserResolver, RequestContext
                from vanna.integrations.sqlite import SqliteRunner
                from vanna.tools import RunSqlTool, LocalFileSystem
                from vanna.capabilities.agent_memory import InMemoryAgentMemory

                logger.info(f"📊 Database: {database_path}")
                logger.info(f"🎯 Table: {table_name}")

                # Extract schema
                schema = self._extract_table_schema(database_path, table_name)

                # Create tool description
                tool_description = f"""Execute SQL queries against the staffing database.

IMPORTANT: Use this schema information to generate accurate SQL queries.

{schema}

Guidelines:
- Use exact table and column names as shown above
- The database is SQLite, so use SQLite-compatible SQL syntax
- For date queries, use strftime() function
- Only use SELECT queries (no modifications)
"""

                # Initialize components
                model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
                llm = AnthropicLlmService(model=model)
                file_system = LocalFileSystem(working_directory="./adk_staffing_data")

                # Create shared agent memory (persists across queries!)
                self._agent_memory = InMemoryAgentMemory()

                tool_registry = ToolRegistry()

                # Configure SQLite runner with read-only URI
                db_uri = f"file:{database_path}?mode=ro"
                sqlite_runner = SqliteRunner(database_path=db_uri)

                sql_tool = RunSqlTool(
                    sql_runner=sqlite_runner,
                    file_system=file_system,
                    custom_tool_description=tool_description
                )
                tool_registry.register(sql_tool)

                user_resolver = CookieEmailUserResolver()

                # Create agent with persistent memory
                self._agent = Agent(
                    llm_service=llm,
                    config=AgentConfig(
                        stream_responses=False,
                        max_tool_iterations=3,
                        include_thinking_indicators=False
                    ),
                    tool_registry=tool_registry,
                    user_resolver=user_resolver,
                    agent_memory=self._agent_memory  # SHARED MEMORY!
                )

                # Pre-populate with training data
                if load_training_data:
                    self._load_training_data(database_path, table_name)

                logger.info("✅ Vanna Agent initialized with persistent memory!")
                logger.info(f"   Model: {model}")
                logger.info(f"   Memory: Shared across all requests")
                logger.info(f"   Learning: Enabled")

            except Exception as e:
                logger.error(f"❌ Failed to initialize agent: {e}")
                raise

    def _extract_table_schema(self, db_path: str, table_name: str) -> str:
        """Extract schema for a specific table."""
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        schema_parts = []

        # Get table DDL
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        ddl_result = cursor.fetchone()

        if not ddl_result:
            conn.close()
            raise ValueError(f"Table '{table_name}' not found in database.")

        schema_parts.append(f"-- Table: {table_name}")
        schema_parts.append(ddl_result[0])

        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if columns:
            schema_parts.append(f"-- Columns ({len(columns)}):")
            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                pk_marker = " [PRIMARY KEY]" if pk else ""
                not_null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""
                schema_parts.append(
                    f"--   {name}: {col_type}{pk_marker}{not_null_marker}{default_marker}"
                )

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        schema_parts.append(f"-- Rows: {row_count:,}")

        # Show sample data (first 3 rows)
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()

            cursor.execute(f"PRAGMA table_info({table_name})")
            col_info = cursor.fetchall()
            col_names = [col[1] for col in col_info]

            schema_parts.append(f"-- Sample data (first 3 rows):")
            for i, row in enumerate(sample_rows, 1):
                schema_parts.append(f"--   Row {i}: {dict(zip(col_names, row))}")

        conn.close()
        return "\n".join(schema_parts)

    def _load_training_data(self, database_path: str, table_name: str) -> None:
        """
        Pre-populate agent memory with common query patterns.

        This gives the agent a head start with proven examples.
        """
        logger.info("📚 Loading training data...")

        try:
            from vanna.core.tool import ToolContext
            from vanna.core.user import User
            import uuid

            # Create training context
            training_context = ToolContext(
                user=User(
                    id="system_training",
                    username="System",
                    group_memberships=["admin"]
                ),
                conversation_id="training-session",
                request_id=str(uuid.uuid4()),
                agent_memory=self._agent_memory
            )

            # Run async training data population
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def populate_training():
                # Business rules
                await self._agent_memory.save_text_memory(
                    content=f"""
                    Business Rule: Active Employees in {table_name}
                    - Filter active employees with status checks
                    - Exclude test or demo accounts
                    - Use proper date formatting for hire dates
                    """,
                    context=training_context
                )

                await self._agent_memory.save_text_memory(
                    content=f"""
                    Business Rule: Department Analysis
                    - Group by department for organizational views
                    - Count distinct employees
                    - Sort by employee count descending
                    """,
                    context=training_context
                )

                await self._agent_memory.save_text_memory(
                    content=f"""
                    Business Rule: Salary Calculations
                    - Exclude NULL salary values
                    - Exclude zero values
                    - Round to 2 decimal places
                    - Use ROUND() and AVG() functions
                    """,
                    context=training_context
                )

                # Example queries (these will be retrieved for similar questions)
                example_queries = [
                    {
                        "question": "How many employees are there?",
                        "sql": f"SELECT COUNT(*) as total_employees FROM {table_name}"
                    },
                    {
                        "question": "Show me headcount by department",
                        "sql": f"""
                            SELECT department, COUNT(*) as employee_count
                            FROM {table_name}
                            GROUP BY department
                            ORDER BY employee_count DESC
                        """
                    },
                    {
                        "question": "What is the average salary?",
                        "sql": f"""
                            SELECT ROUND(AVG(salary), 2) as avg_salary
                            FROM {table_name}
                            WHERE salary IS NOT NULL AND salary > 0
                        """
                    },
                    {
                        "question": "Average salary by department",
                        "sql": f"""
                            SELECT
                                department,
                                ROUND(AVG(salary), 2) as avg_salary,
                                COUNT(*) as employee_count
                            FROM {table_name}
                            WHERE salary IS NOT NULL AND salary > 0
                            GROUP BY department
                            ORDER BY avg_salary DESC
                        """
                    },
                    {
                        "question": "How many employees were hired in 2024?",
                        "sql": f"""
                            SELECT COUNT(*) as hires_2024
                            FROM {table_name}
                            WHERE strftime('%Y', hire_date) = '2024'
                        """
                    }
                ]

                for ex in example_queries:
                    await self._agent_memory.save_tool_usage(
                        question=ex["question"],
                        tool_name="run_sql",
                        args={"sql": ex["sql"]},
                        context=training_context,
                        success=True,
                        metadata={"source": "training_data"}
                    )

                logger.info(f"   ✅ Loaded {len(example_queries)} example queries")
                logger.info(f"   ✅ Loaded 3 business rules")

            loop.run_until_complete(populate_training())

        except Exception as e:
            logger.warning(f"⚠️ Failed to load training data: {e}")
            logger.warning("   Agent will still work but won't have training examples")

    async def query(
        self,
        question: str,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using the shared Vanna agent.

        This method:
        1. Uses the persistent agent (learning from all queries)
        2. Stores successful patterns for future use
        3. Is thread-safe for concurrent requests

        Args:
            question: Natural language question
            user_id: User identifier (for context, not isolation)
            metadata: Optional metadata to track query source

        Returns:
            Dict with query results
        """
        if self._agent is None:
            raise RuntimeError("Agent not initialized. Call initialize_agent() first.")

        self._query_count += 1
        query_num = self._query_count

        logger.info(f"🔍 Query #{query_num} from {user_id}: {question[:50]}...")

        try:
            from vanna.core.user import RequestContext

            # Create request context (unique per request but shares memory!)
            request_context = RequestContext(
                cookies={"email": f"{user_id}@un.org"},
                metadata=metadata or {"source": "production", "user": user_id},
                remote_addr="127.0.0.1",
            )

            sql_query = None
            result_df = None
            response_text = ""

            # Execute query (agent will learn from this!)
            async for component in self._agent.send_message(
                request_context=request_context,
                message=question,
                conversation_id=f"staffing-{query_num}",
            ):
                # Capture SQL query
                if hasattr(component, 'tool_call') and component.tool_call:
                    if component.tool_call.tool_name == 'run_sql':
                        if hasattr(component.tool_call, 'args') and component.tool_call.args:
                            sql_query = component.tool_call.args.get('sql', '')

                # Capture query results
                if hasattr(component, 'tool_result') and component.tool_result:
                    if hasattr(component.tool_result, 'content'):
                        content = component.tool_result.content
                        if isinstance(content, pd.DataFrame):
                            result_df = content

                # Capture response text
                if hasattr(component, 'simple_component') and component.simple_component:
                    if hasattr(component.simple_component, 'text'):
                        text = component.simple_component.text
                        if text and text.strip():
                            response_text += text + " "

                if hasattr(component, 'rich_component') and component.rich_component:
                    if hasattr(component.rich_component, 'content'):
                        content = component.rich_component.content
                        if content and content.strip():
                            response_text += content + " "

            # Format results
            if result_df is not None and not result_df.empty:
                data = result_df.to_dict('records')
                rows, cols = result_df.shape

                logger.info(f"   ✅ Query #{query_num} succeeded: {rows} rows")

                return {
                    "status": "success",
                    "result": {
                        "question": question,
                        "sql": sql_query or "SQL query generated",
                        "data": data,
                        "row_count": rows,
                        "column_count": cols,
                        "summary": response_text.strip() or f"Query returned {rows} row(s)",
                        "query_number": query_num,
                        "data_source": "Staffing Database via Vanna (Learning Enabled)"
                    }
                }
            elif sql_query:
                logger.info(f"   ✅ Query #{query_num} succeeded: no results")
                return {
                    "status": "success",
                    "result": {
                        "question": question,
                        "sql": sql_query,
                        "data": [],
                        "summary": response_text.strip() or "Query executed successfully with no results.",
                        "query_number": query_num,
                        "data_source": "Staffing Database via Vanna (Learning Enabled)"
                    }
                }
            else:
                logger.warning(f"   ⚠️ Query #{query_num} failed to generate SQL")
                return {
                    "status": "error",
                    "result": {
                        "question": question,
                        "error": "Unable to generate SQL query for this question.",
                        "suggestion": response_text.strip() or "Try rephrasing your question.",
                        "query_number": query_num,
                        "data_source": "Staffing Query Tool"
                    }
                }

        except Exception as e:
            logger.error(f"   ❌ Query #{query_num} error: {e}")
            return {
                "status": "error",
                "result": {
                    "question": question,
                    "error": f"Query execution failed: {str(e)}",
                    "query_number": query_num,
                    "data_source": "Staffing Query Tool"
                }
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent's learning."""
        return {
            "initialized": self._agent is not None,
            "total_queries": self._query_count,
            "memory_enabled": self._agent_memory is not None,
        }


# Singleton instance
_manager = VannaAgentManager()


def get_vanna_manager() -> VannaAgentManager:
    """Get the singleton Vanna agent manager."""
    return _manager
