from __future__ import annotations

import base64
import json
from asyncio import CancelledError
from collections import deque
from typing import Any, AsyncIterator, Deque, Optional, Union

from pydantic import ValidationError, BaseModel

try:
    from websockets.asyncio.client import ClientConnection  # websockets >= 13.0
except ImportError as exc:
    raise ImportError(
        "The `websockets` package (>=13.0) is required for real-time transcription. "
        "Install with: pip install 'mistralai[realtime]'"
    ) from exc

from mistralai.models import (
    AudioFormat,
    RealtimeTranscriptionError,
    RealtimeTranscriptionSession,
    RealtimeTranscriptionSessionCreated,
    RealtimeTranscriptionSessionUpdated,
    TranscriptionStreamDone,
    TranscriptionStreamLanguage,
    TranscriptionStreamSegmentDelta,
    TranscriptionStreamTextDelta,
)


class UnknownRealtimeEvent(BaseModel):
    """
    Forward-compat fallback event:
    - unknown message type
    - invalid JSON payload
    - schema validation failure
    """
    type: Optional[str]
    content: Any
    error: Optional[str] = None


RealtimeEvent = Union[
    # session lifecycle
    RealtimeTranscriptionSessionCreated,
    RealtimeTranscriptionSessionUpdated,
    # server errors
    RealtimeTranscriptionError,
    # transcription events
    TranscriptionStreamLanguage,
    TranscriptionStreamSegmentDelta,
    TranscriptionStreamTextDelta,
    TranscriptionStreamDone,
    # forward-compat fallback
    UnknownRealtimeEvent,
]


_MESSAGE_MODELS: dict[str, Any] = {
    "session.created": RealtimeTranscriptionSessionCreated,
    "session.updated": RealtimeTranscriptionSessionUpdated,
    "error": RealtimeTranscriptionError,
    "transcription.language": TranscriptionStreamLanguage,
    "transcription.segment": TranscriptionStreamSegmentDelta,
    "transcription.text.delta": TranscriptionStreamTextDelta,
    "transcription.done": TranscriptionStreamDone,
}


def parse_realtime_event(payload: Any) -> RealtimeEvent:
    """
    Tolerant parser:
    - unknown event type -> UnknownRealtimeEvent
    - validation failures -> UnknownRealtimeEvent (includes error string)
    - invalid payload -> UnknownRealtimeEvent
    """
    if not isinstance(payload, dict):
        return UnknownRealtimeEvent(
            type=None, content=payload, error="expected JSON object"
        )

    msg_type = payload.get("type")
    if not isinstance(msg_type, str):
        return UnknownRealtimeEvent(
            type=None, content=payload, error="missing/invalid 'type'"
        )

    model_cls = _MESSAGE_MODELS.get(msg_type)
    if model_cls is None:
        return UnknownRealtimeEvent(
            type=msg_type, content=payload, error="unknown event type"
        )
    try:
        parsed = model_cls.model_validate(payload)
        return parsed
    except ValidationError as exc:
        return UnknownRealtimeEvent(type=msg_type, content=payload, error=str(exc))


class RealtimeConnection:
    def __init__(
        self,
        websocket: ClientConnection,
        session: RealtimeTranscriptionSession,
        *,
        initial_events: Optional[list[RealtimeEvent]] = None,
    ) -> None:
        self._websocket = websocket
        self._session = session
        self._audio_format = session.audio_format
        self._closed = False
        self._initial_events: Deque[RealtimeEvent] = deque(initial_events or [])

    @property
    def request_id(self) -> str:
        return self._session.request_id

    @property
    def session(self) -> RealtimeTranscriptionSession:
        return self._session

    @property
    def audio_format(self) -> AudioFormat:
        return self._audio_format

    @property
    def is_closed(self) -> bool:
        return self._closed

    async def send_audio(
        self, audio_bytes: Union[bytes, bytearray, memoryview]
    ) -> None:
        if self._closed:
            raise RuntimeError("Connection is closed")

        message = {
            "type": "input_audio.append",
            "audio": base64.b64encode(bytes(audio_bytes)).decode("ascii"),
        }
        await self._websocket.send(json.dumps(message))

    async def update_session(self, audio_format: AudioFormat) -> None:
        if self._closed:
            raise RuntimeError("Connection is closed")

        self._audio_format = audio_format
        message = {
            "type": "session.update",
            "session": {"audio_format": audio_format.model_dump(mode="json")},
        }
        await self._websocket.send(json.dumps(message))

    async def end_audio(self) -> None:
        if self._closed:
            return
        await self._websocket.send(json.dumps({"type": "input_audio.end"}))

    async def close(self, *, code: int = 1000, reason: str = "") -> None:
        if self._closed:
            return
        self._closed = True
        await self._websocket.close(code=code, reason=reason)

    async def __aenter__(self) -> "RealtimeConnection":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def __aiter__(self) -> AsyncIterator[RealtimeEvent]:
        return self.events()

    async def events(self) -> AsyncIterator[RealtimeEvent]:
        # replay any handshake/prelude events (including session.created)
        while self._initial_events:
            ev = self._initial_events.popleft()
            self._apply_session_updates(ev)
            yield ev

        try:
            async for msg in self._websocket:
                text = (
                    msg.decode("utf-8", errors="replace")
                    if isinstance(msg, (bytes, bytearray))
                    else msg
                )
                try:
                    data = json.loads(text)
                except Exception as exc:
                    yield UnknownRealtimeEvent(
                        type=None, content=text, error=f"invalid JSON: {exc}"
                    )
                    continue

                ev = parse_realtime_event(data)
                self._apply_session_updates(ev)
                yield ev
        except CancelledError:
            pass
        finally:
            await self.close()

    def _apply_session_updates(self, ev: RealtimeEvent) -> None:
        if isinstance(ev, RealtimeTranscriptionSessionCreated) or isinstance(ev, RealtimeTranscriptionSessionUpdated):
            self._session = ev.session
            self._audio_format = ev.session.audio_format
