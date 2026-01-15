"""
OpenAI + SQLite Example with Web UI
This is a proper setup using OpenAI with the Chinook database
"""
import os
from dotenv import load_dotenv

load_dotenv()

from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.integrations.openai import OpenAILlmService
from vanna.tools import RunSqlTool, VisualizeDataTool, LocalFileSystem
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.core.system_prompt import DefaultSystemPromptBuilder
import sqlite3


class SimpleUserResolver(UserResolver):
    """Simple user resolver that extracts email from cookie"""

    def __init__(self, cookie_name: str = "vanna_email"):
        self.cookie_name = cookie_name

    async def resolve_user(self, request_context: RequestContext) -> User:
        email = request_context.get_cookie(self.cookie_name)
        if not email:
            # Default to demo user if no cookie
            email = "demo@example.com"

        return User(
            id=email.split("@")[0],
            email=email,
            group_memberships=["admin", "user"],
        )


def get_database_schema(database_path: str) -> str:
    """Extract database schema information for the system prompt"""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema_info = ["DATABASE SCHEMA (Chinook - Digital Music Store):", "="*60, ""]

    for table in tables:
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        schema_info.append(f"Table: {table}")
        schema_info.append("Columns:")
        for col in columns:
            col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
            pk_marker = " (PRIMARY KEY)" if pk else ""
            null_marker = " NOT NULL" if not_null else ""
            schema_info.append(f"  - {col_name}: {col_type}{pk_marker}{null_marker}")
        schema_info.append("")

    conn.close()
    return "\n".join(schema_info)


def create_demo_agent() -> Agent:
    """Create a demo agent with OpenAI and SQLite"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    # Check for database (resolve path relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(script_dir, "Chinook.sqlite")
    if not os.path.exists(database_path):
        raise FileNotFoundError(
            f"Chinook database not found at {database_path}. "
            "Download it from https://vanna.ai/Chinook.sqlite"
        )

    print(f"Using OpenAI (gpt-4o)")
    print(f"Using database: {database_path}")

    # Get database schema for system prompt
    schema_info = get_database_schema(database_path)

    # Set up LLM
    llm = OpenAILlmService(model="gpt-4o", api_key=api_key)

    # Create shared FileSystem for tools
    file_system = LocalFileSystem(working_directory="./openai_data")

    # Create tool registry
    tool_registry = ToolRegistry()

    # Register SQL tool
    sqlite_runner = SqliteRunner(database_path=database_path)
    sql_tool = RunSqlTool(sql_runner=sqlite_runner, file_system=file_system)
    tool_registry.register_local_tool(sql_tool, access_groups=["admin", "user"])

    # Register visualization tool
    viz_tool = VisualizeDataTool(file_system=file_system)
    tool_registry.register_local_tool(viz_tool, access_groups=["admin", "user"])

    # User resolver
    user_resolver = SimpleUserResolver()

    # Agent memory
    agent_memory = DemoAgentMemory(max_items=1000)

    # Create system prompt with database schema
    base_prompt = f"""You are Vanna, an AI data analyst assistant. You help users query and analyze data from a SQLite database.

{schema_info}

IMPORTANT SQL GUIDELINES:
- Use the EXACT table and column names shown above (case-sensitive)
- All table names are singular and capitalized (e.g., "Track" not "tracks", "Album" not "albums")
- When joining tables, use the foreign key relationships shown in the schema
- Always use proper SQL syntax for SQLite

When a user asks a question:
1. Analyze which tables and columns are needed
2. Write a SQL query using the exact schema above
3. Execute the query using the run_sql tool
4. Interpret and summarize the results for the user
5. Offer to visualize the data if appropriate"""

    system_prompt_builder = DefaultSystemPromptBuilder(base_prompt=base_prompt)

    return Agent(
        llm_service=llm,
        config=AgentConfig(stream_responses=True),
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
        system_prompt_builder=system_prompt_builder,
    )


def main():
    agent = create_demo_agent()

    print("\n" + "="*70)
    print("Vanna 2.0 - OpenAI + SQLite + Web UI")
    print("="*70)
    print("\nServer starting at:")
    print("  - Web UI: http://localhost:8000")
    print("  - API: http://localhost:8000/api/vanna/v2/chat_sse")
    print("\nTry asking questions like:")
    print("  - 'What tables are in the database?'")
    print("  - 'Show me the top 10 customers by total purchases'")
    print("  - 'Visualize the top 5 genres by number of tracks'")
    print("\nPress Ctrl+C to stop")
    print("="*70 + "\n")

    server = VannaFastAPIServer(agent)
    server.run()


if __name__ == "__main__":
    main()
