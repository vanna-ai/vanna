"""
Flask server factory for Vanna Agents.
"""

import asyncio
from typing import Any, Dict, Optional

from flask import Flask
from flask_cors import CORS

from ...core import Agent
from ..base import ChatHandler
from .routes import register_chat_routes


class VannaFlaskServer:
    """Flask server factory for Vanna Agents."""

    def __init__(
        self,
        agent: Agent,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Flask server.

        Args:
            agent: The agent to serve (must have user_resolver configured)
            config: Optional server configuration
        """
        self.agent = agent
        self.config = config or {}
        self.chat_handler = ChatHandler(agent)

    def create_app(self) -> Flask:
        """Create configured Flask app.

        Returns:
            Configured Flask application
        """
        # Check if dev mode is enabled
        dev_mode = self.config.get("dev_mode", False)
        static_folder = self.config.get("static_folder", "static") if dev_mode else None

        app = Flask(__name__, static_folder=static_folder, static_url_path="/static")

        # Apply configuration
        app.config.update(self.config.get("flask", {}))

        # Enable CORS if configured
        cors_config = self.config.get("cors", {})
        if cors_config.get("enabled", True):
            CORS(app, **{k: v for k, v in cors_config.items() if k != "enabled"})

        # Register routes
        register_chat_routes(app, self.chat_handler, self.config)

        # Add health check
        @app.route("/health")
        def health_check() -> Dict[str, str]:
            return {"status": "healthy", "service": "vanna"}

        return app

    def run(self, **kwargs: Any) -> None:
        """Run the Flask server.

        This method automatically detects if running in an async environment
        (Jupyter, Colab, IPython, etc.) and:
        - Installs and applies nest_asyncio to handle existing event loops
        - Sets up port forwarding if in Google Colab
        - Displays the correct URL for accessing the app

        Args:
            **kwargs: Arguments passed to Flask.run()
        """
        import sys

        app = self.create_app()

        # Set defaults
        run_kwargs = {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            **kwargs
        }

        # Get the port from run_kwargs
        port = run_kwargs.get("port", 5000)

        # Check if we're in an environment with a running event loop
        # (Jupyter, Colab, IPython, VS Code notebooks, etc.)
        in_async_env = False
        try:
            import asyncio
            try:
                asyncio.get_running_loop()
                in_async_env = True
            except RuntimeError:
                in_async_env = False
        except Exception:
            pass

        if in_async_env:
            # Apply nest_asyncio to allow nested event loops
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                print("Warning: nest_asyncio not installed. Installing...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "nest_asyncio"])
                import nest_asyncio
                nest_asyncio.apply()

        # Check if we're specifically in Google Colab for port forwarding
        in_colab = "google.colab" in sys.modules

        if in_colab:
            try:
                from google.colab import output
                output.serve_kernel_port_as_window(port)
                from google.colab.output import eval_js
                print("Your app is running at:")
                print(eval_js(f"google.colab.kernel.proxyPort({port})"))
            except Exception as e:
                print(f"Warning: Could not set up Colab port forwarding: {e}")
                print(f"Your app is running at: http://localhost:{port}")
        else:
            print("Your app is running at:")
            print(f"http://localhost:{port}")

        app.run(**run_kwargs)