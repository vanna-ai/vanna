"""
Anthropic example using AnthropicLlmService.

Loads environment from .env (via python-dotenv), uses model 'claude-sonnet-4-20250514'
by default, and sends a simple message through a Agent.

Run:
  PYTHONPATH=. python vanna/examples/anthropic_quickstart.py
"""

import asyncio
import importlib.util
import os
import sys


def ensure_env() -> None:
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv

        # Load from local .env without overriding existing env
        load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
    else:
        print(
            "[warn] python-dotenv not installed; skipping .env load. Install with: pip install python-dotenv"
        )

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "[error] ANTHROPIC_API_KEY is not set. Add it to your environment or .env file."
        )
        sys.exit(1)


async def main() -> None:
    ensure_env()

    try:
        from vanna.integrations.anthropic import AnthropicLlmService
    except ImportError:
        print(
            "[error] anthropic extra not installed. Install with: pip install -e .[anthropic]"
        )
        raise

    from vanna import AgentConfig, Agent, User
    from vanna.core.registry import ToolRegistry
    from vanna.tools import ListFilesTool

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    print(f"Using Anthropic model: {model}")

    llm = AnthropicLlmService(model=model)

    # Create tool registry and register the list_files tool
    tool_registry = ToolRegistry()
    list_files_tool = ListFilesTool()
    tool_registry.register(list_files_tool)

    agent = Agent(llm_service=llm, config=AgentConfig(stream_responses=False), tool_registry=tool_registry)

    user = User(id="demo-user", username="demo")
    conversation_id = "anthropic-demo"

    print("Sending: 'List the files in the current directory'\n")
    async for component in agent.send_message(
        user=user,
        message="List the files in the current directory",
        conversation_id=conversation_id,
    ):
        if hasattr(component, "content") and getattr(component, "content"):
            print("Assistant:", component.content)


if __name__ == "__main__":
    asyncio.run(main())
