"""
Quickstart script to run Tecknoworks AI Agent locally
This script sets up a local server with OpenAI and the Urban Eats restaurant database
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.integrations.openai import OpenAILlmService
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.local.agent_memory import DemoAgentMemory


class SimpleUserResolver(UserResolver):
    """Simple user resolver for demo purposes"""
    async def resolve_user(self, request_context: RequestContext) -> User:
        # For demo purposes, check for a cookie or default to admin
        user_email = request_context.get_cookie('vanna_email')

        if not user_email:
            # Default to admin user if no cookie is set
            user_email = "admin@example.com"

        print(f"User authenticated: {user_email}")

        if user_email == "admin@example.com":
            return User(id="admin1", email=user_email, group_memberships=['admin'])

        return User(id="user1", email=user_email, group_memberships=['user'])


def main():
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    print("Setting up Tecknoworks AI Agent with Urban Eats restaurant database...")

    # Set up tools with access control
    tools = ToolRegistry()
    tools.register_local_tool(
        RunSqlTool(sql_runner=SqliteRunner(database_path="./demo-data/urban_eats.sqlite")),
        access_groups=['admin', 'user']
    )
    tools.register_local_tool(
        VisualizeDataTool(),
        access_groups=['admin', 'user']
    )

    # Set up agent memory
    agent_memory = DemoAgentMemory(max_items=1000)
    tools.register_local_tool(
        SaveQuestionToolArgsTool(),
        access_groups=['admin']
    )
    tools.register_local_tool(
        SearchSavedCorrectToolUsesTool(),
        access_groups=['admin', 'user']
    )

    # Set up LLM with OpenAI
    llm = OpenAILlmService(
        model="gpt-4o",
        api_key=api_key
    )

    # Create agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        config=AgentConfig(),
        agent_memory=agent_memory
    )

    # Create and run server
    print("\n" + "="*70)
    print("Starting Tecknoworks AI Agent Server...")
    print("="*70)
    print("\nServer will be available at:")
    print("  - Web UI: http://localhost:8000")
    print("  - API endpoint: http://localhost:8000/api/vanna/v2/chat_sse")
    print("\nDatabase: Urban Eats Restaurant Chain")
    print("  - 25 restaurant locations")
    print("  - 293K+ orders (6 months of data)")
    print("  - $16.4M+ in revenue data")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    server = VannaFastAPIServer(agent)
    server.run()


if __name__ == "__main__":
    main()
