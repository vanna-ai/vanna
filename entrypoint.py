"""
Tecknoworks AI Agent - Azure Deployment Entrypoint

This script initializes the FastAPI server with Azure AI Foundry for production deployment.
It uses environment variables for configuration, which are typically injected from Azure Key Vault.

Supported LLM providers (in priority order):
- Azure AI Foundry (recommended): AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_API_KEY
- Azure OpenAI (legacy): AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
- OpenAI (fallback): OPENAI_API_KEY
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the src directory is in the Python path
sys.path.insert(0, str(Path(__file__).parent))

from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.local.agent_memory import DemoAgentMemory


class SimpleUserResolver(UserResolver):
    """Simple user resolver for demo purposes"""

    async def resolve_user(self, request_context: RequestContext) -> User:
        # For demo purposes, check for a cookie or default to admin
        user_email = request_context.get_cookie('tecknoworks_email')

        if not user_email:
            user_email = "admin@example.com"

        print(f"User authenticated: {user_email}")

        if user_email == "admin@example.com":
            return User(id="admin1", email=user_email, group_memberships=['admin'])

        return User(id="user1", email=user_email, group_memberships=['user'])


def get_llm_service():
    """
    Get the appropriate LLM service based on environment configuration.

    Supports (in priority order):
    - Azure AI Foundry (recommended for Azure deployment)
    - Azure OpenAI (legacy)
    - OpenAI (fallback)
    """

    # Check for Azure AI Foundry configuration first (highest priority)
    foundry_endpoint = os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
    foundry_api_key = os.getenv("AZURE_AI_FOUNDRY_API_KEY")
    foundry_model = os.getenv("AZURE_AI_FOUNDRY_MODEL")
    foundry_use_entra_id = os.getenv("AZURE_AI_FOUNDRY_USE_ENTRA_ID", "").lower() in ("true", "1", "yes")

    if foundry_endpoint and (foundry_api_key or foundry_use_entra_id):
        print(f"Using Azure AI Foundry: {foundry_endpoint}")
        if foundry_model:
            print(f"Model: {foundry_model}")

        from vanna.integrations.foundry import AzureAIFoundryLlmService
        return AzureAIFoundryLlmService(
            endpoint=foundry_endpoint,
            api_key=foundry_api_key,
            model=foundry_model,
            use_entra_id=foundry_use_entra_id
        )

    # Check for Azure OpenAI configuration (legacy)
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    if azure_endpoint and azure_api_key:
        print(f"Using Azure OpenAI: {azure_endpoint}")
        print(f"Model: {azure_model}")

        from vanna.integrations.azureopenai import AzureOpenAILlmService
        return AzureOpenAILlmService(
            model=azure_model,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=azure_api_version
        )

    # Fallback to OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        print("Using OpenAI (fallback)")
        from vanna.integrations.openai import OpenAILlmService
        return OpenAILlmService(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=openai_api_key
        )

    raise ValueError(
        "No LLM configuration found. Please set either:\n"
        "  - AZURE_AI_FOUNDRY_ENDPOINT + AZURE_AI_FOUNDRY_API_KEY or AZURE_AI_FOUNDRY_USE_ENTRA_ID=true\n"
        "  - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY (for Azure OpenAI)\n"
        "  - OPENAI_API_KEY (for OpenAI)"
    )


def main():
    """Main entry point for the Tecknoworks AI Agent server."""

    print("=" * 70)
    print("Tecknoworks AI Agent - Urban Eats Restaurant Analytics")
    print("=" * 70)

    # Get database path
    db_path = os.getenv("DATABASE_PATH", "./demo-data/urban_eats.sqlite")
    print(f"Database: {db_path}")

    # Verify database exists
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Initialize LLM service
    llm = get_llm_service()

    # Set up tools with access control
    tools = ToolRegistry()
    tools.register_local_tool(
        RunSqlTool(sql_runner=SqliteRunner(database_path=db_path)),
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

    # Configure UI features for better user experience
    # Enable more features for regular users to see what's happening
    from vanna.core.agent.config import UiFeatures, UiFeature

    ui_features = UiFeatures(
        feature_group_access={
            # Both admin and user can see tool names in task tracker
            UiFeature.UI_FEATURE_SHOW_TOOL_NAMES: ["admin", "user"],
            # Both can see tool arguments (shows what the agent is doing)
            UiFeature.UI_FEATURE_SHOW_TOOL_ARGUMENTS: ["admin", "user"],
            # Only admin sees error details
            UiFeature.UI_FEATURE_SHOW_TOOL_ERROR: ["admin"],
            # Both can see LLM's reasoning before tool execution
            UiFeature.UI_FEATURE_SHOW_TOOL_INVOCATION_MESSAGE_IN_CHAT: ["admin", "user"],
            # Both can see detailed memory search results
            UiFeature.UI_FEATURE_SHOW_MEMORY_DETAILED_RESULTS: ["admin", "user"],
        }
    )

    # Create agent with enhanced UI features
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        config=AgentConfig(
            ui_features=ui_features,
            max_tool_iterations=25,  # Increased from default 10 for complex analytical workflows
        ),
        agent_memory=agent_memory
    )

    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print()
    print(f"Server starting on {host}:{port}")
    print("=" * 70)
    print()
    print("Database: Urban Eats Restaurant Chain")
    print("  - 25 restaurant locations")
    print("  - 293K+ orders (6 months of data)")
    print("  - $16.4M+ in revenue data")
    print()
    print("Endpoints:")
    print(f"  - Health: http://{host}:{port}/health")
    print(f"  - Chat SSE: http://{host}:{port}/api/vanna/v2/chat_sse")
    print(f"  - Chat Poll: http://{host}:{port}/api/vanna/v2/chat_poll")
    print()
    print("=" * 70)

    # Create and run server
    server = VannaFastAPIServer(agent)
    server.run(host=host, port=port)


if __name__ == "__main__":
    main()
