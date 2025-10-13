"""
FastAPI server factory for Vanna Agents.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ...core import Agent
from ..base import ChatHandler
from .routes import register_chat_routes


class VannaFastAPIServer:
    """FastAPI server factory for Vanna Agents."""

    def __init__(
        self,
        agent: Agent,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize FastAPI server.

        Args:
            agent: The agent to serve (must have user_resolver configured)
            config: Optional server configuration
        """
        self.agent = agent
        self.config = config or {}
        self.chat_handler = ChatHandler(agent)

    def create_app(self) -> FastAPI:
        """Create configured FastAPI app.

        Returns:
            Configured FastAPI application
        """
        # Create FastAPI app
        app_config = self.config.get("fastapi", {})
        app = FastAPI(
            title="Vanna Agents API",
            description="API server for Vanna Agents framework",
            version="0.1.0",
            **app_config
        )

        # Configure CORS if enabled
        cors_config = self.config.get("cors", {})
        if cors_config.get("enabled", True):
            cors_params = {k: v for k, v in cors_config.items() if k != "enabled"}

            # Set sensible defaults
            cors_params.setdefault("allow_origins", ["*"])
            cors_params.setdefault("allow_credentials", True)
            cors_params.setdefault("allow_methods", ["*"])
            cors_params.setdefault("allow_headers", ["*"])

            app.add_middleware(CORSMiddleware, **cors_params)

        # Add static file serving in dev mode
        dev_mode = self.config.get("dev_mode", False)
        if dev_mode:
            static_folder = self.config.get("static_folder", "static")
            try:
                import os
                if os.path.exists(static_folder):
                    app.mount("/static", StaticFiles(directory=static_folder), name="static")
            except Exception:
                pass  # Static files not available

        # Register routes
        register_chat_routes(app, self.chat_handler, self.config)

        # Add health check
        @app.get("/health")
        async def health_check() -> Dict[str, str]:
            return {"status": "healthy", "service": "vanna"}

        return app

    def run(self, **kwargs: Any) -> None:
        """Run the FastAPI server.

        Args:
            **kwargs: Arguments passed to uvicorn.run()
        """
        import uvicorn

        app = self.create_app()

        # Set defaults
        run_kwargs = {
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "info",
            **kwargs
        }

        uvicorn.run(app, **run_kwargs)