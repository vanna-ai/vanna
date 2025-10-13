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

        Args:
            **kwargs: Arguments passed to Flask.run()
        """
        app = self.create_app()

        # Set defaults
        run_kwargs = {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            **kwargs
        }

        app.run(**run_kwargs)