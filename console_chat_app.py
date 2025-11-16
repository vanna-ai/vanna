#!/usr/bin/env python3
"""
Simple Console Chat App for Vanna v2 with SQLite

This console app provides full visibility into:
- SQL query generation
- Query execution
- Results
- Tool calls and reasoning

Usage:
    python console_chat_app.py <path_to_database.db>

Example:
    # First download the Chinook demo database:
    curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite

    # Then run the app:
    python console_chat_app.py Chinook.sqlite

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - pip install anthropic
"""

import asyncio
import importlib.util
import os
import sys
import time
from typing import Optional
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


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("🤖 VANNA v2 CONSOLE CHAT - Interactive SQL Query Assistant")
    print("=" * 70)
    print("Type your questions in natural language.")
    print("The AI will generate and execute SQL queries to answer them.")
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

    # Check for database path argument
    if len(sys.argv) < 2:
        print("\n❌ ERROR: No database path provided!")
        print("\nUsage: python console_chat_app.py <path_to_database.db>")
        print("\nExample:")
        print("  # Download demo database:")
        print("  curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite")
        print("\n  # Run the app:")
        print("  python console_chat_app.py Chinook.sqlite\n")
        sys.exit(1)

    database_path = sys.argv[1]
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
    from vanna.core.user import UserResolver, User, RequestContext
    from vanna.integrations.sqlite import SqliteRunner
    from vanna.tools import RunSqlTool, LocalFileSystem

    # Create a simple user resolver
    class SimpleUserResolver(UserResolver):
        async def resolve_user(self, request_context: RequestContext) -> User:
            user_email = request_context.get_cookie('vanna_email') or 'guest@example.com'
            group = 'admin' if user_email == 'admin@example.com' else 'user'
            return User(id=user_email, email=user_email, group_memberships=[group])

    # Setup
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    print_header()
    print(f"📊 Database: {os.path.abspath(database_path)}")
    print(f"🤖 Model: {model}")
    print(f"✅ Ready!\n")
    print_separator()

    # Initialize Vanna agent
    llm = AnthropicLlmService(model=model)
    file_system = LocalFileSystem(working_directory="./console_data")

    tool_registry = ToolRegistry()
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner, file_system=file_system)
    tool_registry.register_local_tool(sql_tool, access_groups=[])

    user_resolver = SimpleUserResolver()

    agent = Agent(
        llm_service=llm,
        config=AgentConfig(
            stream_responses=True,  # Enable streaming for real-time feedback
            max_tool_iterations=10,
            include_thinking_indicators=True
        ),
        tool_registry=tool_registry,
        user_resolver=user_resolver,
    )

    # Create request context
    request_context = RequestContext(
        cookies={"vanna_email": "console-user@vanna.ai"},
        metadata={"source": "console"},
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
