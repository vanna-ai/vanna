import datetime
import json
import typing
from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Tag

from mistralai.extra.utils.response_format import pydantic_model_from_json
from mistralai.models import (
    FunctionResultEntry,
    FunctionCallEntry,
    MessageOutputEntry,
    AgentHandoffEntry,
    ToolExecutionEntry,
    MessageInputEntry,
    AgentHandoffDoneEvent,
    AgentHandoffStartedEvent,
    ResponseDoneEvent,
    ResponseErrorEvent,
    ResponseStartedEvent,
    FunctionCallEvent,
    MessageOutputEvent,
    ToolExecutionDoneEvent,
    ToolExecutionStartedEvent,
    ConversationEventsData,
    MessageOutputEventContent,
    MessageOutputEntryContent,
    TextChunk,
    MessageOutputContentChunks,
    SSETypes,
    InputEntries,
    ToolFileChunk,
    ToolReferenceChunk,
    FunctionCallEntryArguments,
)
from mistralai.utils import get_discriminator

RunOutputEntries = (
    MessageOutputEntry
    | FunctionCallEntry
    | FunctionResultEntry
    | AgentHandoffEntry
    | ToolExecutionEntry
)

RunEntries = RunOutputEntries | MessageInputEntry


def as_text(entry: RunOutputEntries) -> str:
    """Keep only the messages and turn content into textual representation."""
    text = ""
    if isinstance(entry, MessageOutputEntry):
        if isinstance(entry.content, str):
            text += entry.content
        else:
            for chunk in entry.content:
                if isinstance(chunk, TextChunk):
                    text += chunk.text
                elif isinstance(chunk, ToolFileChunk):
                    text += f"<File id={chunk.file_id} name={chunk.file_name}>"
                elif isinstance(chunk, ToolReferenceChunk):
                    text += f"<Reference title={chunk.title}>"
    return text


def reconstitute_message_content(
    chunks: list[MessageOutputEventContent],
) -> MessageOutputEntryContent:
    """Given a list of MessageOutputEventContent, recreate a normalised MessageOutputEntryContent."""
    if all(isinstance(chunk, str) for chunk in chunks):
        return "".join(typing.cast(list[str], chunks))
    content: list[MessageOutputContentChunks] = []
    for chunk in chunks:
        if isinstance(chunk, str):
            chunk = TextChunk(text=chunk)
        if isinstance(chunk, TextChunk):
            if len(content) and isinstance(content[-1], TextChunk):
                content[-1].text += chunk.text
            else:
                content.append(chunk)
        else:
            content.append(chunk)
    return content


def reconstitute_function_call_args(chunks: list[str]) -> FunctionCallEntryArguments:
    """Recreates function call arguments from stream"""
    return typing.cast(FunctionCallEntryArguments, "".join(chunks))


def reconstitue_entries(
    received_event_tracker: dict[int, list[ConversationEventsData]],
) -> list[RunOutputEntries]:
    """Given a list of events, recreate the corresponding entries."""
    run_entries: list[RunOutputEntries] = []
    for idx, events in sorted(received_event_tracker.items(), key=lambda x: x[0]):
        first_event = events[0]
        if isinstance(first_event, MessageOutputEvent):
            message_events = typing.cast(list[MessageOutputEvent], events)
            run_entries.append(
                MessageOutputEntry(
                    content=reconstitute_message_content(
                        chunks=[
                            message_event.content for message_event in message_events
                        ]
                    ),
                    created_at=first_event.created_at,
                    id=first_event.id,
                    agent_id=first_event.agent_id,
                    model=first_event.model,
                    role=first_event.role,
                )
            )
        elif isinstance(first_event, FunctionCallEvent):
            function_call_events = typing.cast(list[FunctionCallEvent], events)
            run_entries.append(
                FunctionCallEntry(
                    name=first_event.name,
                    arguments=reconstitute_function_call_args(
                        chunks=[
                            function_call_event.arguments
                            for function_call_event in function_call_events
                        ]
                    ),
                    created_at=first_event.created_at,
                    id=first_event.id,
                    tool_call_id=first_event.tool_call_id,
                )
            )
    return run_entries


@dataclass
class RunFiles:
    id: str
    name: str
    content: bytes


@dataclass
class RunResult:
    input_entries: list[InputEntries]
    conversation_id: str | None = field(default=None)
    output_entries: list[RunOutputEntries] = field(default_factory=list)
    files: dict[str, RunFiles] = field(default_factory=dict)
    output_model: type[BaseModel] | None = field(default=None)

    def get_file(self, file_id: str) -> RunFiles | None:
        return self.files.get(file_id)

    @property
    def entries(self) -> list[RunEntries]:
        return [*self.input_entries, *self.output_entries]

    @property
    def output_as_text(self) -> str:
        if not self.output_entries:
            raise ValueError("No output entries were started.")
        return "\n".join(
            as_text(entry)
            for entry in self.output_entries
            if entry.type == "message.output"
        )

    @property
    def output_as_model(self) -> BaseModel:
        if self.output_model is None:
            raise ValueError("No output format was not set.")
        return pydantic_model_from_json(
            json.loads(self.output_as_text), self.output_model
        )


class FunctionResultEvent(BaseModel):
    id: str | None = None

    type: Literal["function.result"] | None = "function.result"

    result: str

    tool_call_id: str

    created_at: datetime.datetime | None = datetime.datetime.now(
        tz=datetime.timezone.utc
    )

    output_index: int | None = 0


RunResultEventsType = SSETypes | Literal["function.result"]

RunResultEventsData = typing.Annotated[
    Annotated[AgentHandoffDoneEvent, Tag("agent.handoff.done")]
    | Annotated[AgentHandoffStartedEvent, Tag("agent.handoff.started")]
    | Annotated[ResponseDoneEvent, Tag("conversation.response.done")]
    | Annotated[ResponseErrorEvent, Tag("conversation.response.error")]
    | Annotated[ResponseStartedEvent, Tag("conversation.response.started")]
    | Annotated[FunctionCallEvent, Tag("function.call.delta")]
    | Annotated[MessageOutputEvent, Tag("message.output.delta")]
    | Annotated[ToolExecutionDoneEvent, Tag("tool.execution.done")]
    | Annotated[ToolExecutionStartedEvent, Tag("tool.execution.started")]
    | Annotated[FunctionResultEvent, Tag("function.result")],
    Discriminator(lambda m: get_discriminator(m, "type", "type")),
]


class RunResultEvents(BaseModel):
    event: RunResultEventsType

    data: RunResultEventsData
