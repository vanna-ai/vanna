#!/usr/bin/env python3
"""
Single-Table Console Chat App for Vanna v2 with SQLite

This version is optimized for databases with many tables where you only
need to query one or a few specific tables. It dramatically reduces token
usage by only extracting schema for the specified table(s).

Usage:
    python console_chat_app_single_table.py <database.db> <table_name>

    Or for multiple tables:
    python console_chat_app_single_table.py <database.db> <table1> <table2> <table3>

Examples:
    # Single table
    python console_chat_app_single_table.py myapp.db staffing_table

    # Multiple tables
    python console_chat_app_single_table.py myapp.db staffing_table employees departments

Benefits:
    - Minimal token usage (only 1 table instead of 50)
    - Faster LLM responses
    - Lower API costs
    - Focused context for more accurate queries
"""

import asyncio
import importlib.util
import os
import sys
import time
import sqlite3
from typing import List
from datetime import datetime


def ensure_env() -> None:
    """Load environment variables and check for API key."""
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv
        load_dotenv(override=False)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        print("Or create a .env file with: ANTHROPIC_API_KEY=your-key-here\n")
        sys.exit(1)


def extract_specific_tables_schema(database_path: str, table_names: List[str]) -> str:
    """
    Extract schema for specific tables only.

    Args:
        database_path: Path to SQLite database
        table_names: List of table names to extract

    Returns:
        Formatted string with schema information for specified tables only
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    schema_parts = []
    schema_parts.append("=" * 70)
    schema_parts.append("DATABASE SCHEMA (FILTERED)")
    schema_parts.append("=" * 70)

    # Verify tables exist and get them
    placeholders = ','.join('?' * len(table_names))
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders}) ORDER BY name",
        table_names
    )
    found_tables = cursor.fetchall()

    if not found_tables:
        schema_parts.append(f"\n⚠️  WARNING: None of the specified tables were found!")
        schema_parts.append(f"Requested: {', '.join(table_names)}")
        schema_parts.append("\nAvailable tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        all_tables = cursor.fetchall()
        for (table,) in all_tables:
            schema_parts.append(f"  - {table}")
        conn.close()
        return "\n".join(schema_parts)

    schema_parts.append(f"\nIncluded Tables: {len(found_tables)} of {len(table_names)} requested")

    missing_tables = set(table_names) - {t[0] for t in found_tables}
    if missing_tables:
        schema_parts.append(f"⚠️  Missing tables: {', '.join(missing_tables)}\n")
    else:
        schema_parts.append("")

    for (table_name,) in found_tables:
        # Get table DDL
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        ddl_result = cursor.fetchone()

        if ddl_result:
            schema_parts.append(f"\n-- Table: {table_name}")
            schema_parts.append(ddl_result[0])

        # Get column info with details
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

            # Get column names for sample data
            cursor.execute(f"PRAGMA table_info({table_name})")
            col_info = cursor.fetchall()
            col_names = [col[1] for col in col_info]

            schema_parts.append(f"-- Sample data (first 3 rows):")
            for i, row in enumerate(sample_rows, 1):
                schema_parts.append(f"--   Row {i}: {dict(zip(col_names, row))}")

    schema_parts.append("\n" + "=" * 70)

    conn.close()
    return "\n".join(schema_parts)


def create_schema_aware_tool_description(schema: str, table_names: List[str]) -> str:
    """Create a detailed tool description including the database schema."""
    tables_str = "', '".join(table_names)
    return f"""Execute SQL queries against the configured SQLite database.

IMPORTANT: Use this schema information to generate accurate SQL queries.
Only the following table(s) are available: '{tables_str}'

{schema}

Guidelines:
- Use exact table and column names as shown above
- Pay attention to data types and constraints
- Consider table relationships via foreign keys
- The database is SQLite, so use SQLite-compatible SQL syntax
- Available SQL commands: SELECT, JOIN, GROUP BY, ORDER BY, etc.
- Do NOT use DROP, DELETE, UPDATE, or INSERT unless explicitly requested
- ONLY query the table(s) shown above - other tables in the database are not accessible
"""


def print_header(table_names: List[str]):
    """Print application header."""
    print("\n" + "=" * 70)
    print("🤖 VANNA v2 CONSOLE CHAT - Single-Table SQL Assistant")
    print("=" * 70)
    print(f"Focused on table(s): {', '.join(table_names)}")
    print("Type your questions in natural language.")
    print("Commands: 'quit' or 'exit' to end, 'clear' to clear conversation")
    print("=" * 70 + "\n")


def print_separator(char="-", length=70):
    """Print a separator line."""
    print(char * length)


def print_timestamp(label: str):
    """Print a timestamp with label."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"⏱️  [{timestamp}] {label}")


async def main():
    """Main console chat application."""
    ensure_env()

    # Check for required arguments
    if len(sys.argv) < 3:
        print("\n❌ ERROR: Missing required arguments!")
        print("\nUsage: python console_chat_app_single_table.py <database.db> <table_name> [table2] [table3] ...")
        print("\nExamples:")
        print("  # Single table")
        print("  python console_chat_app_single_table.py myapp.db staffing_table")
        print("\n  # Multiple tables")
        print("  python console_chat_app_single_table.py myapp.db staffing_table employees\n")
        sys.exit(1)

    database_path = sys.argv[1]
    table_names = sys.argv[2:]  # All remaining arguments are table names

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

    print_header(table_names)
    print(f"📊 Database: {os.path.abspath(database_path)}")
    print(f"🎯 Target table(s): {', '.join(table_names)}")
    print(f"🤖 Model: {model}")
    print()

    # Extract schema for specific tables only
    print(f"🔍 Extracting schema for {len(table_names)} table(s)...")
    try:
        schema = extract_specific_tables_schema(database_path, table_names)
        print("✅ Schema extracted successfully!")
        print()
        print(schema)
        print()
    except Exception as e:
        print(f"❌ Error extracting schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print_separator()
    print("✅ LLM has complete knowledge of your table(s)!")
    print("💰 Token usage optimized - only relevant tables included!")
    print_separator()

    # Initialize Vanna agent with single-table schema
    llm = AnthropicLlmService(model=model)
    file_system = LocalFileSystem(working_directory="./console_data")

    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)

    # Create schema-aware SQL tool with custom description
    schema_aware_description = create_schema_aware_tool_description(schema, table_names)
    sql_tool = RunSqlTool(
        sql_runner=sqlite_runner,
        file_system=file_system,
        custom_tool_description=schema_aware_description
    )
    tool_registry.register(sql_tool)

    user_resolver = CookieEmailUserResolver()

    agent = Agent(
        llm_service=llm,
        config=AgentConfig(
            stream_responses=True,
            max_tool_iterations=10,
            include_thinking_indicators=True
        ),
        tool_registry=tool_registry,
        user_resolver=user_resolver,
    )

    # Create request context
    request_context = RequestContext(
        cookies={user_resolver.cookie_name: "console-user@vanna.ai"},
        metadata={"source": "console", "tables": table_names},
        remote_addr="127.0.0.1",
    )

    conversation_id = f"console-session-{int(time.time())}"

    # Main chat loop
    while True:
        try:
            # Get user input
            print()
            user_input = input("💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye!\n")
                break

            if user_input.lower() == 'clear':
                conversation_id = f"console-session-{int(time.time())}"
                print("\n🔄 Conversation cleared. Starting fresh.\n")
                print_separator()
                continue

            # Track execution
            print()
            print_separator("=")
            start_time = time.time()
            print_timestamp("Query received")

            # Send message and process streaming responses
            thinking = False
            tool_calls_made = []
            last_sql = None
            results_data = None

            async for component in agent.send_message(
                request_context=request_context,
                message=user_input,
                conversation_id=conversation_id,
            ):
                # Handle thinking indicators
                if hasattr(component, 'type'):
                    if component.type == 'thinking_indicator_start':
                        if not thinking:
                            print_timestamp("🧠 AI is thinking...")
                            thinking = True
                    elif component.type == 'thinking_indicator_stop':
                        thinking = False

                # Handle tool calls (SQL execution)
                if hasattr(component, 'tool_call') and component.tool_call:
                    tool_call = component.tool_call
                    print()
                    print_timestamp(f"🔧 Tool called: {tool_call.tool_name}")

                    if tool_call.tool_name == 'run_sql':
                        # Extract and display SQL query
                        if hasattr(tool_call, 'args') and tool_call.args:
                            sql = tool_call.args.get('sql', '')
                            if sql:
                                last_sql = sql
                                print()
                                print("📝 Generated SQL Query:")
                                print_separator()
                                print(sql)
                                print_separator()
                                print_timestamp("⚡ Executing SQL...")
                    else:
                        # Show args for other tools
                        if hasattr(tool_call, 'args') and tool_call.args:
                            print(f"   Arguments: {tool_call.args}")

                    tool_calls_made.append(tool_call.tool_name)

                # Handle tool results
                if hasattr(component, 'tool_result') and component.tool_result:
                    tool_result = component.tool_result
                    print_timestamp(f"✅ Tool execution completed")

                    # Try to extract DataFrame from result
                    if hasattr(tool_result, 'content'):
                        import pandas as pd
                        content = tool_result.content

                        # Check if content is a DataFrame
                        if isinstance(content, pd.DataFrame):
                            results_data = content
                            rows, cols = content.shape
                            print(f"📊 Query returned: {rows} rows × {cols} columns")

                            # Display the results table
                            if rows > 0:
                                print()
                                print("📋 Query Results:")
                                print_separator()
                                # Display table with limited rows for readability
                                if rows <= 20:
                                    print(content.to_string(index=False))
                                else:
                                    print(f"Showing first 10 and last 10 rows of {rows} total:")
                                    print(pd.concat([content.head(10), content.tail(10)]).to_string(index=False))
                                print_separator()
                        else:
                            # Non-DataFrame result
                            result_str = str(content)
                            if len(result_str) > 500:
                                print(f"📊 Result: {len(result_str)} characters")
                            else:
                                print(f"📊 Result: {result_str[:200]}")

                # Handle text responses
                if hasattr(component, 'simple_component') and component.simple_component:
                    if hasattr(component.simple_component, 'text'):
                        text = component.simple_component.text
                        if text and text.strip():
                            print()
                            print("🤖 Assistant:", text)

                # Handle rich text (markdown)
                if hasattr(component, 'rich_component') and component.rich_component:
                    if hasattr(component.rich_component, 'content') and component.rich_component.content:
                        content = component.rich_component.content
                        if content and content.strip():
                            print()
                            print("🤖 Assistant:")
                            print(content)

                # Handle data frames (table results)
                if hasattr(component, 'data_frame_component') and component.data_frame_component:
                    df_comp = component.data_frame_component
                    if hasattr(df_comp, 'data_frame_id'):
                        print()
                        print(f"📊 Data table component (ID: {df_comp.data_frame_id})")

            # Execution summary
            elapsed = time.time() - start_time
            print()
            print_separator("=")
            print(f"⏱️  Total time: {elapsed:.2f}s")
            if tool_calls_made:
                print(f"🔧 Tools used: {', '.join(tool_calls_made)}")
            print_separator("=")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    asyncio.run(main())
