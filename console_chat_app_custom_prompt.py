#!/usr/bin/env python3
"""
Console Chat App with Custom System Prompt Example

Demonstrates how to customize the system prompt to control SQL generation behavior.
Based on official Vanna example: vanna/examples/custom_system_prompt_example.py

Usage:
    python console_chat_app_custom_prompt.py <database.db> <table_name>

Example:
    python console_chat_app_custom_prompt.py myapp.db staffing_table
"""

import asyncio
import importlib.util
import os
import sys
import time
import sqlite3
from typing import List, Optional
from datetime import datetime

# Import official Vanna interfaces
from vanna.core.interfaces import SystemPromptBuilder
from vanna.core.models import ToolSchema, User


# ============================================================================
# CUSTOM SYSTEM PROMPT BUILDER
# ============================================================================

class SQLExpertSystemPromptBuilder(SystemPromptBuilder):
    """
    Custom system prompt builder for SQL query generation.

    This controls how the LLM generates SQL queries by providing:
    - Domain-specific context
    - Query best practices
    - Business rules
    - Response formatting guidelines
    """

    def __init__(self, domain_context: str = ""):
        """
        Initialize with optional domain context.

        Args:
            domain_context: Description of the database domain (e.g., "staffing management")
        """
        self.domain_context = domain_context

    async def build_system_prompt(
        self, user: User, tools: List[ToolSchema]
    ) -> Optional[str]:
        """
        Build customized system prompt for SQL generation.

        This method is called once per conversation turn, before the LLM processes
        the user's message. The prompt you return here will guide all SQL generation.
        """

        # Base prompt with SQL expertise
        prompt = f"""You are an expert SQL database assistant{f' for {self.domain_context}' if self.domain_context else ''}.

Your primary responsibilities:
1. Translate natural language questions into efficient, correct SQL queries
2. Analyze query results and provide business insights
3. Explain complex queries in simple terms
4. Suggest optimizations and follow-up questions

SQL Query Guidelines:
- Always validate table and column names against the schema
- Use appropriate JOINs (avoid Cartesian products)
- Limit result sets to reasonable sizes (default: 1000 rows)
- Use explicit column names instead of SELECT *
- Add comments for complex queries
- Format dates as YYYY-MM-DD
- Round decimals appropriately (2 places for currency, 1 for percentages)

Best Practices:
- For aggregations, use GROUP BY with meaningful groupings
- For performance, avoid SELECT DISTINCT when not necessary
- Use indexes effectively (filter on indexed columns first)
- Handle NULL values explicitly
- Use CASE statements for conditional logic

Response Format:
1. Briefly explain your approach
2. Execute the SQL query using available tools
3. Summarize results with key insights
4. Suggest relevant follow-up questions when appropriate
"""

        # Add tool-specific instructions
        tool_names = [tool.name for tool in tools]
        if "visualize_data" in tool_names:
            prompt += "\n- Create visualizations for numerical trends and distributions"
        if "save_question_tool_args" in tool_names:
            prompt += "\n- Save successful query patterns for future reference"

        prompt += f"\n\nAvailable tools: {', '.join(tool_names)}"

        return prompt


class StaffingSystemPromptBuilder(SystemPromptBuilder):
    """
    Domain-specific system prompt for staffing/HR analytics.

    Includes business rules and conventions specific to staffing data.
    """

    async def build_system_prompt(
        self, user: User, tools: List[ToolSchema]
    ) -> Optional[str]:
        """Build staffing-focused system prompt."""

        prompt = """You are an expert HR analytics assistant specializing in staffing data analysis.

DOMAIN: Employee Staffing and Human Resources

Your expertise includes:
- Headcount analysis (by department, location, status, hire date)
- Compensation analysis (salary ranges, averages, distributions)
- Tenure analysis (retention, turnover, hiring trends)
- Organizational structure queries

SQL Query Standards for Staffing Data:
- For salary analysis, exclude NULL or 0 values
- For headcount, filter by status='active' unless specified otherwise
- For hire date analysis, default to last 12 months unless specified
- Group by department/location for meaningful aggregations
- Use DATE functions for hire date calculations

Formatting Rules:
- Salaries: Format as currency with $ and commas (e.g., $75,000)
- Headcount: Always show as whole numbers (no decimals)
- Percentages: Show with 1 decimal place (e.g., 15.3%)
- Dates: Format as YYYY-MM-DD or human-readable format
- Names: Title case for proper nouns

Data Privacy:
- Do not expose individual employee PII without aggregation
- Use employee_id instead of names when possible
- Respect data access policies

Response Style:
- Lead with the key metric or answer
- Provide context (e.g., "compared to last quarter")
- Highlight trends and outliers
- Suggest actionable next steps

Common Queries You Should Handle Well:
- "How many employees in each department?"
- "What's the average salary by department?"
- "Show me hiring trends over time"
- "Who are the longest-tenured employees?"
- "What's our turnover rate?"
"""

        # Add tool information
        tool_names = [tool.name for tool in tools]
        prompt += f"\n\nAvailable tools: {', '.join(tool_names)}"

        return prompt


# ============================================================================
# REST OF THE CONSOLE APP (same as console_chat_app_single_table.py)
# ============================================================================

def ensure_env() -> None:
    """Load environment variables and check for API key."""
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv
        load_dotenv(override=False)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)


def extract_specific_tables_schema(database_path: str, table_names: List[str]) -> str:
    """Extract schema for specific tables only."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    schema_parts = []
    schema_parts.append("=" * 70)
    schema_parts.append("DATABASE SCHEMA")
    schema_parts.append("=" * 70)

    placeholders = ','.join('?' * len(table_names))
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders}) ORDER BY name",
        table_names
    )
    found_tables = cursor.fetchall()

    if not found_tables:
        schema_parts.append(f"\n⚠️  WARNING: None of the specified tables were found!")
        conn.close()
        return "\n".join(schema_parts)

    schema_parts.append(f"\nIncluded Tables: {len(found_tables)}\n")

    for (table_name,) in found_tables:
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        ddl_result = cursor.fetchone()

        if ddl_result:
            schema_parts.append(f"\n-- Table: {table_name}")
            schema_parts.append(ddl_result[0])

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if columns:
            schema_parts.append(f"-- Columns ({len(columns)}):")
            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                pk_marker = " [PRIMARY KEY]" if pk else ""
                not_null_marker = " NOT NULL" if not_null else ""
                schema_parts.append(f"--   {name}: {col_type}{pk_marker}{not_null_marker}")

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        schema_parts.append(f"-- Rows: {row_count:,}\n")

    conn.close()
    return "\n".join(schema_parts)


def create_schema_aware_tool_description(schema: str, table_names: List[str]) -> str:
    """Create tool description including database schema."""
    return f"""Execute SQL queries against the configured SQLite database.

IMPORTANT: Use this schema information to generate accurate SQL queries:

{schema}

Guidelines:
- Use exact table and column names as shown above
- Only query the tables listed: {', '.join(table_names)}
- The database is SQLite - use SQLite-compatible syntax
"""


async def main():
    """Main console chat application with custom system prompt."""
    ensure_env()

    if len(sys.argv) < 3:
        print("\n❌ ERROR: Missing required arguments!")
        print("\nUsage: python console_chat_app_custom_prompt.py <database.db> <table_name> [table2] ...")
        print("\nExamples:")
        print("  python console_chat_app_custom_prompt.py myapp.db staffing_table")
        sys.exit(1)

    database_path = sys.argv[1]
    table_names = sys.argv[2:]

    if not os.path.exists(database_path):
        print(f"\n❌ ERROR: Database file not found: {database_path}\n")
        sys.exit(1)

    # Import Vanna components
    try:
        from vanna.integrations.anthropic import AnthropicLlmService
    except ImportError:
        print("\n❌ ERROR: anthropic integration not installed.")
        print("Install with: pip install anthropic\n")
        sys.exit(1)

    from vanna import Agent, AgentConfig
    from vanna.core.registry import ToolRegistry
    from vanna.core.user import CookieEmailUserResolver, RequestContext
    from vanna.integrations.sqlite import SqliteRunner
    from vanna.tools import RunSqlTool, LocalFileSystem

    # Setup
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    print("\n" + "=" * 70)
    print("🤖 VANNA CONSOLE CHAT - Custom System Prompt Demo")
    print("=" * 70)
    print(f"📊 Database: {os.path.abspath(database_path)}")
    print(f"🎯 Table(s): {', '.join(table_names)}")
    print(f"🤖 Model: {model}")
    print(f"✨ Using custom system prompt for better SQL generation!")
    print("=" * 70 + "\n")

    # Extract schema
    schema = extract_specific_tables_schema(database_path, table_names)
    print(schema)
    print("\n" + "=" * 70)

    # Initialize Vanna agent with CUSTOM SYSTEM PROMPT
    llm = AnthropicLlmService(model=model)
    file_system = LocalFileSystem(working_directory="./console_data")

    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)

    schema_aware_description = create_schema_aware_tool_description(schema, table_names)
    sql_tool = RunSqlTool(
        sql_runner=sqlite_runner,
        file_system=file_system,
        custom_tool_description=schema_aware_description
    )
    tool_registry.register(sql_tool)

    user_resolver = CookieEmailUserResolver()

    # Choose which custom system prompt to use
    # Option 1: General SQL expert prompt
    # custom_prompt_builder = SQLExpertSystemPromptBuilder(domain_context="staffing management")

    # Option 2: Staffing-specific prompt (recommended for HR/staffing data)
    custom_prompt_builder = StaffingSystemPromptBuilder()

    agent = Agent(
        llm_service=llm,
        config=AgentConfig(
            stream_responses=True,
            max_tool_iterations=10,
            include_thinking_indicators=True
        ),
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        system_prompt_builder=custom_prompt_builder,  # ⭐ CUSTOM SYSTEM PROMPT!
    )

    print("✅ Custom system prompt loaded!")
    print("💡 The LLM will follow your custom SQL generation guidelines")
    print("=" * 70)

    # Create request context
    request_context = RequestContext(
        cookies={user_resolver.cookie_name: "console-user@vanna.ai"},
        metadata={"source": "console"},
        remote_addr="127.0.0.1",
    )

    conversation_id = f"console-session-{int(time.time())}"

    # Main chat loop
    print("\n💬 Type your questions (or 'quit' to exit):\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye!\n")
                break

            print()
            start_time = time.time()

            # Send message
            async for component in agent.send_message(
                request_context=request_context,
                message=user_input,
                conversation_id=conversation_id,
            ):
                # Handle SQL execution display
                if hasattr(component, 'tool_call') and component.tool_call:
                    tool_call = component.tool_call
                    if tool_call.tool_name == 'run_sql':
                        if hasattr(tool_call, 'args') and tool_call.args:
                            sql = tool_call.args.get('sql', '')
                            if sql:
                                print("📝 Generated SQL:")
                                print("-" * 70)
                                print(sql)
                                print("-" * 70)

                # Handle results
                if hasattr(component, 'tool_result') and component.tool_result:
                    if hasattr(component.tool_result, 'content'):
                        import pandas as pd
                        content = component.tool_result.content
                        if isinstance(content, pd.DataFrame) and len(content) > 0:
                            print(f"\n📊 Results ({len(content)} rows):")
                            print("-" * 70)
                            if len(content) <= 20:
                                print(content.to_string(index=False))
                            else:
                                print(content.head(10).to_string(index=False))
                                print(f"... ({len(content)-10} more rows)")
                            print("-" * 70)

                # Handle text responses
                if hasattr(component, 'simple_component') and component.simple_component:
                    if hasattr(component.simple_component, 'text'):
                        text = component.simple_component.text
                        if text and text.strip():
                            print(f"\n🤖 Assistant: {text}")

            elapsed = time.time() - start_time
            print(f"\n⏱️  Time: {elapsed:.2f}s\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
