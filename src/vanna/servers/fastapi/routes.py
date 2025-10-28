"""
FastAPI route implementations for Vanna Agents.
"""

import json
import traceback
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse

from ..base import ChatHandler, ChatRequest, ChatResponse
from ..base.templates import get_index_html
from ...core.user.request_context import RequestContext


def register_chat_routes(app: FastAPI, chat_handler: ChatHandler, config: Optional[Dict[str, Any]] = None) -> None:
    """Register chat routes on FastAPI app.

    Args:
        app: FastAPI application
        chat_handler: Chat handler instance
        config: Server configuration
    """
    config = config or {}

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Serve the main chat interface."""
        dev_mode = config.get("dev_mode", False)
        cdn_url = config.get("cdn_url", "https://img.vanna.ai/vanna-components.js")
        api_base_url = config.get("api_base_url", "")

        return get_index_html(
            dev_mode=dev_mode,
            cdn_url=cdn_url,
            api_base_url=api_base_url
        )

    @app.post("/api/vanna/v2/chat_sse")
    async def chat_sse(chat_request: ChatRequest, http_request: Request) -> StreamingResponse:
        """Server-Sent Events endpoint for streaming chat."""
        # Extract request context for user resolution
        chat_request.request_context = RequestContext(
            cookies=dict(http_request.cookies),
            headers=dict(http_request.headers),
            remote_addr=http_request.client.host if http_request.client else None,
            query_params=dict(http_request.query_params),
            metadata=chat_request.metadata,
        )

        async def generate() -> AsyncGenerator[str, None]:
            """Generate SSE stream."""
            try:
                async for chunk in chat_handler.handle_stream(chat_request):
                    chunk_json = chunk.model_dump_json()
                    yield f"data: {chunk_json}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                traceback.print_stack()
                traceback.print_exc()
                error_data = {
                    "type": "error",
                    "data": {"message": str(e)},
                    "conversation_id": chat_request.conversation_id or "",
                    "request_id": chat_request.request_id or "",
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    @app.websocket("/api/vanna/v2/chat_websocket")
    async def chat_websocket(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time chat."""
        await websocket.accept()

        try:
            while True:
                # Receive message
                try:
                    data = await websocket.receive_json()

                    # Extract request context for user resolution
                    metadata = data.get('metadata', {})
                    data['request_context'] = RequestContext(
                        cookies=dict(websocket.cookies),
                        headers=dict(websocket.headers),
                        remote_addr=websocket.client.host if websocket.client else None,
                        query_params=dict(websocket.query_params),
                        metadata=metadata,
                    )

                    chat_request = ChatRequest(**data)
                except Exception as e:
                    traceback.print_stack()
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Invalid request: {str(e)}"},
                    })
                    continue

                # Stream response
                try:
                    async for chunk in chat_handler.handle_stream(chat_request):
                        await websocket.send_json(chunk.model_dump())

                    # Send completion signal
                    await websocket.send_json({
                        "type": "completion",
                        "data": {"status": "done"},
                        "conversation_id": chunk.conversation_id if 'chunk' in locals() else "",
                        "request_id": chunk.request_id if 'chunk' in locals() else "",
                    })

                except Exception as e:
                    traceback.print_stack()
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                        "conversation_id": chat_request.conversation_id or "",
                        "request_id": chat_request.request_id or "",
                    })

        except WebSocketDisconnect:
            pass
        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"WebSocket error: {str(e)}"},
                })
            except:
                pass
            finally:
                await websocket.close()

    @app.post("/api/vanna/v2/chat_poll")
    async def chat_poll(chat_request: ChatRequest, http_request: Request) -> ChatResponse:
        """Polling endpoint for chat."""
        # Extract request context for user resolution
        chat_request.request_context = RequestContext(
            cookies=dict(http_request.cookies),
            headers=dict(http_request.headers),
            remote_addr=http_request.client.host if http_request.client else None,
            query_params=dict(http_request.query_params),
            metadata=chat_request.metadata,
        )

        try:
            result = await chat_handler.handle_poll(chat_request)
            return result
        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")