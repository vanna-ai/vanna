"""
CLI for running Vanna Agents servers with example agents.
"""

import importlib
import json
from typing import Dict, Optional, Any, cast, TextIO, Union

import click

from ...core import Agent

class ExampleAgentLoader:
    """Loads example agents for the CLI."""

    @staticmethod
    def list_available_examples() -> Dict[str, str]:
        """Return available examples with descriptions."""
        return {
            "mock_quickstart": "Basic agent with mock LLM service",
            "anthropic_quickstart": "Agent configured for Anthropic's Claude API",
            "openai_quickstart": "Agent configured for OpenAI's GPT models",
            "mock_custom_tool": "Agent with custom tool demonstration (mock LLM)",
            "mock_quota_example": "Agent with usage quota management (mock LLM)",
            "mock_rich_components_demo": "Rich components demonstration with cards, tasks, and progress (mock LLM)",
            "coding_agent_example": "Coding agent with file system tools (list, read, write files)",
            "email_auth_example": "Email-based authentication demonstration (mock LLM)",
            "claude_sqlite_example": "Claude agent with SQLite database querying capabilities",
            "mock_sqlite_example": "Mock agent with SQLite database demonstration",
        }

    @staticmethod
    def load_example_agent(example_name: str) -> Agent:
        """Load an example agent by name.

        Args:
            example_name: Name of the example to load

        Returns:
            Configured agent instance

        Raises:
            ValueError: If example not found or failed to load
        """
        try:
            # Import the example module
            module = importlib.import_module(f"vanna.examples.{example_name}")

            # Look for standard factory functions
            factory_functions = [
                "create_demo_agent",
                "create_agent",
                "create_basic_demo",
            ]

            for func_name in factory_functions:
                if hasattr(module, func_name):
                    factory = getattr(module, func_name)
                    return cast(Agent, factory())

            # Look for module-level agent instances
            if hasattr(module, "main_agent"):
                return cast(Agent, module.main_agent)

            raise AttributeError(f"No agent factory found in {example_name}")

        except ImportError as e:
            raise ValueError(f"Example '{example_name}' not found: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load example '{example_name}': {e}")


@click.command()
@click.option(
    "--framework",
    type=click.Choice(["flask", "fastapi"]),
    default="fastapi",
    help="Web framework to use",
)
@click.option("--port", default=8000, help="Port to run server on")
@click.option("--host", default="0.0.0.0", help="Host to bind server to")
@click.option(
    "--example", help="Example agent to use (use --list-examples to see options)"
)
@click.option(
    "--list-examples", is_flag=True, help="List available example agents"
)
@click.option(
    "--config", type=click.File("r"), help="JSON config file for server settings"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--dev", is_flag=True, help="Enable development mode (load components from local assets)")
@click.option("--static-folder", default=None, help="Static folder path for development mode")
@click.option("--cdn-url", default="https://img.vanna.ai/vanna-components.js", help="CDN URL for web components")
def main(
    framework: str,
    port: int,
    host: str,
    example: Optional[str],
    list_examples: bool,
    config: Optional[click.File],
    debug: bool,
    dev: bool,
    static_folder: Optional[str],
    cdn_url: str,
) -> None:
    """Run Vanna Agents server with optional example agent."""

    if list_examples:
        click.echo("Available example agents:")
        examples = ExampleAgentLoader.list_available_examples()
        for name, description in examples.items():
            click.echo(f"  {name:20} - {description}")
        return

    # Load configuration
    server_config = {}
    if config:
        server_config = json.load(cast(TextIO, config))

    # Set default static folder based on dev mode
    if static_folder is None:
        static_folder = "frontend/webcomponent/static" if dev else "static"

    # Add CLI options to config
    server_config.update({
        "dev_mode": dev,
        "static_folder": static_folder,
        "cdn_url": cdn_url,
        "api_base_url": "",  # Can be overridden in config file
    })

    # Create agent
    if example:
        try:
            agent = ExampleAgentLoader.load_example_agent(example)
            click.echo(f"✓ Loaded example agent: {example}")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            return
    else:
        # Fallback to basic agent
        try:
            from ...agents import create_basic_agent
            from ...integrations.mock import MockLlmService

            llm_service = MockLlmService(
                response_content="Hello! I'm a Vanna Agents demo server. How can I help you?"
            )
            agent = create_basic_agent(llm_service)
            click.echo("✓ Using basic demo agent (use --example to specify different agent)")
        except ImportError as e:
            click.echo(f"Error: Could not create basic agent: {e}", err=True)
            return

    from ..flask.app import VannaFlaskServer
    from ..fastapi.app import VannaFastAPIServer

    # Create and run server
    server: Union[VannaFlaskServer, VannaFastAPIServer]
    if framework == "flask":
        server = VannaFlaskServer(agent, config=server_config)
        click.echo(f"🚀 Starting Flask server on http://{host}:{port}")
        if dev:
            click.echo(f"📦 Development mode: loading web components from ./{static_folder}/")
        else:
            click.echo(f"🌍 Production mode: loading web components from CDN")
        try:
            server.run(host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            click.echo("\n👋 Server stopped")
    else:
        server = VannaFastAPIServer(agent, config=server_config)
        click.echo(f"🚀 Starting FastAPI server on http://{host}:{port}")
        click.echo(f"📖 API docs available at http://{host}:{port}/docs")
        if dev:
            click.echo(f"📦 Development mode: loading web components from ./{static_folder}/")
        else:
            click.echo(f"🌍 Production mode: loading web components from CDN")
        try:
            server.run(host=host, port=port)
        except KeyboardInterrupt:
            click.echo("\n👋 Server stopped")


if __name__ == "__main__":
    main()