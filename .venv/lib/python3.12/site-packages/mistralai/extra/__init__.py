from typing import TYPE_CHECKING

from .struct_chat import (
    ParsedChatCompletionResponse,
    convert_to_parsed_chat_completion_response,
)
from .utils import response_format_from_pydantic_model
from .utils.response_format import CustomPydanticModel

if TYPE_CHECKING:
    from .realtime import (
        AudioEncoding,
        AudioFormat,
        RealtimeConnection,
        RealtimeTranscriptionError,
        RealtimeTranscriptionErrorDetail,
        RealtimeTranscriptionSession,
        RealtimeTranscriptionSessionCreated,
        RealtimeTranscriptionSessionUpdated,
        RealtimeTranscription,
        UnknownRealtimeEvent,
    )

_REALTIME_EXPORTS = {
    "RealtimeTranscription",
    "RealtimeConnection",
    "AudioEncoding",
    "AudioFormat",
    "UnknownRealtimeEvent",
    "RealtimeTranscriptionError",
    "RealtimeTranscriptionErrorDetail",
    "RealtimeTranscriptionSession",
    "RealtimeTranscriptionSessionCreated",
    "RealtimeTranscriptionSessionUpdated",
}


def __getattr__(name: str):
    if name in _REALTIME_EXPORTS:
        from . import realtime

        return getattr(realtime, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "convert_to_parsed_chat_completion_response",
    "response_format_from_pydantic_model",
    "CustomPydanticModel",
    "ParsedChatCompletionResponse",
    "RealtimeTranscription",
    "RealtimeConnection",
    "AudioEncoding",
    "AudioFormat",
    "UnknownRealtimeEvent",
    "RealtimeTranscriptionError",
    "RealtimeTranscriptionErrorDetail",
    "RealtimeTranscriptionSession",
    "RealtimeTranscriptionSessionCreated",
    "RealtimeTranscriptionSessionUpdated",
]
