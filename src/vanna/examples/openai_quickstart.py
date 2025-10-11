"""
OpenAI example using OpenAILlmService.

Loads environment from .env (via python-dotenv), uses model 'gpt-5' by default,
and sends a simple message through a Agent.

Run:
  PYTHONPATH=. python vanna/examples/openai_quickstart.py
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

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "[error] OPENAI_API_KEY is not set. Add it to your environment or .env file."
        )
        sys.exit(1)


async def main() -> None:
    ensure_env()

    # Lazy import after env load to allow custom base_url/org via env
    try:
        from vanna.integrations.anthropic import OpenAILlmService
    except ImportError as e:
        print(
            "[error] openai extra not installed. Install with: pip install -e .[openai]"
        )
        raise

    from vanna import AgentConfig, Agent, User
    from vanna.core.registry import ToolRegistry
    from vanna.tools import ListFilesTool

    # Default to 'gpt-5' for this demo; override via $OPENAI_MODEL if desired
    model = os.getenv("OPENAI_MODEL", "gpt-5")
    print(f"Using OpenAI model: {model}")

    llm = OpenAILlmService(model=model)

    # Create tool registry and register the list_files tool
    tool_registry = ToolRegistry()
    list_files_tool = ListFilesTool()
    tool_registry.register(list_files_tool)

    # Some models (e.g., reasoning/gpt-5) only support the default temperature=1.0
    agent = Agent(
        llm_service=llm,
        config=AgentConfig(stream_responses=False, temperature=1.0),
        tool_registry=tool_registry,
    )

    user = User(id="demo-user", username="demo")
    conversation_id = "openai-demo"

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
