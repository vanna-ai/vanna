"""
Flask route implementations for Vanna Agents.
"""

import asyncio
import json
import traceback
from typing import Any, AsyncGenerator, Dict, Generator, Optional, Union

from flask import Flask, Response, jsonify, request

from ..base import ChatHandler, ChatRequest
from ..base.templates import get_index_html
from ...core.user.request_context import RequestContext


def register_chat_routes(app: Flask, chat_handler: ChatHandler, config: Optional[Dict[str, Any]] = None) -> None:
    """Register chat routes on Flask app.

    Args:
        app: Flask application
        chat_handler: Chat handler instance
        config: Server configuration
    """
    config = config or {}

    @app.route("/")
    def index() -> str:
        """Serve the main chat interface."""
        dev_mode = config.get("dev_mode", False)
        cdn_url = config.get("cdn_url", "https://img.vanna.ai/vanna-components.js")
        api_base_url = config.get("api_base_url", "")

        return get_index_html(
            dev_mode=dev_mode,
            cdn_url=cdn_url,
            api_base_url=api_base_url
        )

    @app.route("/api/vanna/v2/chat_sse", methods=["POST"])
    def chat_sse() -> Union[Response, tuple[Response, int]]:
        """Server-Sent Events endpoint for streaming chat."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            # Extract request context for user resolution
            data['request_context'] = RequestContext(
                cookies=dict(request.cookies),
                headers=dict(request.headers),
                remote_addr=request.remote_addr,
                query_params=dict(request.args),
            )

            chat_request = ChatRequest(**data)
        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            return jsonify({"error": f"Invalid request: {str(e)}"}), 400

        def generate() -> Generator[str, None, None]:
            """Generate SSE stream."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def async_generate() -> AsyncGenerator[str, None]:
                    async for chunk in chat_handler.handle_stream(chat_request):
                        chunk_json = chunk.model_dump_json()
                        yield f"data: {chunk_json}\n\n"

                gen = async_generate()
                try:
                    while True:
                        chunk = loop.run_until_complete(gen.__anext__())
                        yield chunk
                except StopAsyncIteration:
                    yield "data: [DONE]\n\n"
            finally:
                loop.close()

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    @app.route("/api/vanna/v2/chat_websocket")
    def chat_websocket() -> tuple[Response, int]:
        """WebSocket endpoint placeholder."""
        return jsonify({
            "error": "WebSocket endpoint not implemented in basic Flask example",
            "suggestion": "Use Flask-SocketIO for WebSocket support"
        }), 501

    @app.route("/api/vanna/v2/chat_poll", methods=["POST"])
    def chat_poll() -> Union[Response, tuple[Response, int]]:
        """Polling endpoint for chat."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON body required"}), 400

            # Extract request context for user resolution
            data['request_context'] = RequestContext(
                cookies=dict(request.cookies),
                headers=dict(request.headers),
                remote_addr=request.remote_addr,
                query_params=dict(request.args),
            )

            chat_request = ChatRequest(**data)
        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            return jsonify({"error": f"Invalid request: {str(e)}"}), 400

        # Run async handler in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(chat_handler.handle_poll(chat_request))
            return jsonify(result.model_dump())
        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            return jsonify({"error": f"Chat failed: {str(e)}"}), 500
        finally:
            loop.close()