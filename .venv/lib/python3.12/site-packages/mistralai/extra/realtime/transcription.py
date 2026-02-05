from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncIterator, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    from websockets.asyncio.client import (
        ClientConnection,
        connect,
    )  # websockets >= 13.0
except ImportError as exc:
    raise ImportError(
        "The `websockets` package (>=13.0) is required for real-time transcription. "
        "Install with: pip install 'mistralai[realtime]'"
    ) from exc

from mistralai import models, utils
from mistralai.models import (
    AudioFormat,
    RealtimeTranscriptionError,
    RealtimeTranscriptionSession,
    RealtimeTranscriptionSessionCreated,
)
from mistralai.sdkconfiguration import SDKConfiguration
from mistralai.utils import generate_url, get_security, get_security_from_env

from ..exceptions import RealtimeTranscriptionException, RealtimeTranscriptionWSError
from .connection import (
    RealtimeConnection,
    RealtimeEvent,
    UnknownRealtimeEvent,
    parse_realtime_event,
)


class RealtimeTranscription:
    """Client for realtime transcription over WebSocket (websockets >= 13.0)."""

    def __init__(self, sdk_config: SDKConfiguration) -> None:
        self._sdk_config = sdk_config

    def _build_url(
        self,
        model: str,
        *,
        server_url: Optional[str],
        query_params: Mapping[str, str],
    ) -> str:
        if server_url is not None:
            base_url = utils.remove_suffix(server_url, "/")
        else:
            base_url, _ = self._sdk_config.get_server_details()

        url = generate_url(base_url, "/v1/audio/transcriptions/realtime", None)

        parsed = urlparse(url)
        merged = dict(parse_qsl(parsed.query, keep_blank_values=True))
        merged["model"] = model
        merged.update(dict(query_params))

        return urlunparse(parsed._replace(query=urlencode(merged)))

    async def connect(
        self,
        model: str,
        audio_format: Optional[AudioFormat] = None,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> RealtimeConnection:
        if timeout_ms is None:
            timeout_ms = self._sdk_config.timeout_ms

        security = self._sdk_config.security
        if security is not None and callable(security):
            security = security()

        resolved_security = get_security_from_env(security, models.Security)

        headers: dict[str, str] = {}
        query_params: dict[str, str] = {}

        if resolved_security is not None:
            security_headers, security_query = get_security(resolved_security)
            headers |= security_headers
            for key, values in security_query.items():
                if values:
                    query_params[key] = values[-1]

        if http_headers is not None:
            headers |= dict(http_headers)

        url = self._build_url(model, server_url=server_url, query_params=query_params)

        parsed = urlparse(url)
        if parsed.scheme == "https":
            parsed = parsed._replace(scheme="wss")
        elif parsed.scheme == "http":
            parsed = parsed._replace(scheme="ws")
        ws_url = urlunparse(parsed)
        open_timeout = None if timeout_ms is None else timeout_ms / 1000.0
        user_agent = self._sdk_config.user_agent

        websocket: Optional[ClientConnection] = None
        try:
            websocket = await connect(
                ws_url,
                additional_headers=dict(headers),
                open_timeout=open_timeout,
                user_agent_header=user_agent,
            )

            session, initial_events = await _recv_handshake(
                websocket, timeout_ms=timeout_ms
            )
            connection = RealtimeConnection(
                websocket=websocket,
                session=session,
                initial_events=initial_events,
            )

            if audio_format is not None:
                await connection.update_session(audio_format)

            return connection

        except RealtimeTranscriptionException:
            if websocket is not None:
                await websocket.close()
            raise
        except Exception as exc:
            if websocket is not None:
                await websocket.close()
            raise RealtimeTranscriptionException(f"Failed to connect: {exc}") from exc

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        model: str,
        audio_format: Optional[AudioFormat] = None,
        server_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        http_headers: Optional[Mapping[str, str]] = None,
    ) -> AsyncIterator[RealtimeEvent]:
        """
        Flow
          - opens connection
          - streams audio in background
          - yields events from the connection
        """
        async with await self.connect(
            model=model,
            audio_format=audio_format,
            server_url=server_url,
            timeout_ms=timeout_ms,
            http_headers=http_headers,
        ) as connection:

            async def _send() -> None:
                async for chunk in audio_stream:
                    if connection.is_closed:
                        break
                    await connection.send_audio(chunk)
                await connection.end_audio()

            send_task = asyncio.create_task(_send())

            try:
                async for event in connection:
                    yield event

                    # stop early (caller still sees the terminating event)
                    if isinstance(event, RealtimeTranscriptionError):
                        break
                    if getattr(event, "type", None) == "transcription.done":
                        break
            finally:
                send_task.cancel()
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                await connection.close()


def _extract_error_message(payload: dict) -> str:
    err = payload.get("error")
    if isinstance(err, dict):
        msg = err.get("message")
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            detail = msg.get("detail")
            if isinstance(detail, str):
                return detail
    return "Realtime transcription error"


async def _recv_handshake(
    websocket: ClientConnection,
    *,
    timeout_ms: Optional[int],
) -> tuple[RealtimeTranscriptionSession, list[RealtimeEvent]]:
    """
    Read messages until session.created or error.
    Replay all messages read during handshake as initial events (lossless).
    """
    timeout_s = None if timeout_ms is None else timeout_ms / 1000.0
    deadline = None if timeout_s is None else (time.monotonic() + timeout_s)

    initial_events: list[RealtimeEvent] = []

    def remaining() -> Optional[float]:
        if deadline is None:
            return None
        return max(0.0, deadline - time.monotonic())

    try:
        while True:
            raw = await asyncio.wait_for(websocket.recv(), timeout=remaining())
            text = (
                raw.decode("utf-8", errors="replace")
                if isinstance(raw, (bytes, bytearray))
                else raw
            )

            try:
                payload = json.loads(text)
            except Exception as exc:
                initial_events.append(
                    UnknownRealtimeEvent(
                        type=None, content=text, error=f"invalid JSON: {exc}"
                    )
                )
                continue

            msg_type = payload.get("type") if isinstance(payload, dict) else None
            if msg_type == "error" and isinstance(payload, dict):
                parsed = parse_realtime_event(payload)
                initial_events.append(parsed)
                if isinstance(parsed, RealtimeTranscriptionError):
                    raise RealtimeTranscriptionWSError(
                        _extract_error_message(payload),
                        payload=parsed,
                        raw=payload,
                    )
                raise RealtimeTranscriptionWSError(
                    _extract_error_message(payload),
                    payload=None,
                    raw=payload,
                )

            event = parse_realtime_event(payload)
            initial_events.append(event)

            if isinstance(event, RealtimeTranscriptionSessionCreated):
                return event.session, initial_events

    except asyncio.TimeoutError as exc:
        raise RealtimeTranscriptionException(
            "Timeout waiting for session creation."
        ) from exc
    except RealtimeTranscriptionException:
        raise
    except Exception as exc:
        raise RealtimeTranscriptionException(
            f"Unexpected websocket handshake failure: {exc}"
        ) from exc
