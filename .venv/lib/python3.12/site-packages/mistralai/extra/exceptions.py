from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mistralai.models import RealtimeTranscriptionError


class MistralClientException(Exception):
    """Base exception for client errors."""


class RunException(MistralClientException):
    """Conversation run errors."""


class MCPException(MistralClientException):
    """MCP operation errors."""


class MCPAuthException(MCPException):
    """MCP authentication errors."""


class RealtimeTranscriptionException(MistralClientException):
    """Base realtime transcription exception."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[int] = None,
        payload: Optional[object] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.payload = payload


class RealtimeTranscriptionWSError(RealtimeTranscriptionException):
    def __init__(
        self,
        message: str,
        *,
        payload: Optional["RealtimeTranscriptionError"] = None,
        raw: Optional[object] = None,
    ) -> None:
        code: Optional[int] = None
        if payload is not None:
            try:
                maybe_code = getattr(payload.error, "code", None)
                if isinstance(maybe_code, int):
                    code = maybe_code
            except Exception:
                code = None

        super().__init__(
            message, code=code, payload=payload if payload is not None else raw
        )
        self.payload_typed = payload
        self.payload_raw = raw
