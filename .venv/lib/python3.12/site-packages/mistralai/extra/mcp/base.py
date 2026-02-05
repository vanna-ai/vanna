import logging
import typing
from collections.abc import Sequence
from contextlib import AsyncExitStack
from typing import Any, Protocol

from mcp import ClientSession  # pyright: ignore[reportMissingImports]
from mcp.types import (  # pyright: ignore[reportMissingImports]
    ContentBlock,
    ListPromptsResult,
)

from mistralai.extra.exceptions import MCPException
from mistralai.models import (
    FunctionTool,
    Function,
    SystemMessageTypedDict,
    AssistantMessageTypedDict,
    TextChunkTypedDict,
)

logger = logging.getLogger(__name__)


class MCPSystemPrompt(typing.TypedDict):
    description: str | None
    messages: list[SystemMessageTypedDict | AssistantMessageTypedDict]


class MCPClientProtocol(Protocol):
    """MCP client that converts MCP artifacts to Mistral format."""

    _name: str

    async def initialize(self, exit_stack: AsyncExitStack | None) -> None:
        ...

    async def aclose(self) -> None:
        ...

    async def get_tools(self) -> list[FunctionTool]:
        ...

    async def execute_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextChunkTypedDict]:
        ...

    async def get_system_prompt(
        self, name: str, arguments: dict[str, Any]
    ) -> MCPSystemPrompt:
        ...

    async def list_system_prompts(self) -> ListPromptsResult:
        ...


class MCPClientBase(MCPClientProtocol):
    """Base class to implement functionalities from an initialized MCP session."""

    _session: ClientSession

    def __init__(self, name: str | None = None):
        self._name = name or self.__class__.__name__
        self._exit_stack: AsyncExitStack | None = None
        self._is_initialized = False

    def _convert_content(self, mcp_content: ContentBlock) -> TextChunkTypedDict:
        if not mcp_content.type == "text":
            raise MCPException("Only supporting text tool responses for now.")
        return {"type": "text", "text": mcp_content.text}

    def _convert_content_list(
        self, mcp_contents: Sequence[ContentBlock]
    ) -> list[TextChunkTypedDict]:
        content_chunks = []
        for mcp_content in mcp_contents:
            content_chunks.append(self._convert_content(mcp_content))
        return content_chunks

    async def get_tools(self) -> list[FunctionTool]:
        mcp_tools = await self._session.list_tools()
        tools = []
        for mcp_tool in mcp_tools.tools:
            tools.append(
                FunctionTool(
                    type="function",
                    function=Function(
                        name=mcp_tool.name,
                        description=mcp_tool.description,
                        parameters=mcp_tool.inputSchema,
                        strict=True,
                    ),
                )
            )
        return tools

    async def execute_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextChunkTypedDict]:
        contents = await self._session.call_tool(name=name, arguments=arguments)
        return self._convert_content_list(contents.content)

    async def get_system_prompt(
        self, name: str, arguments: dict[str, Any]
    ) -> MCPSystemPrompt:
        prompt_result = await self._session.get_prompt(name=name, arguments=arguments)
        return {
            "description": prompt_result.description,
            "messages": [
                typing.cast(
                    SystemMessageTypedDict | AssistantMessageTypedDict,
                    {
                        "role": message.role,
                        "content": self._convert_content(mcp_content=message.content),
                    },
                )
                for message in prompt_result.messages
            ],
        }

    async def list_system_prompts(self) -> ListPromptsResult:
        return await self._session.list_prompts()

    async def initialize(self, exit_stack: AsyncExitStack | None = None) -> None:
        """Initialize the MCP session."""
        # client is already initialized so return
        if self._is_initialized:
            return
        if exit_stack is None:
            self._exit_stack = AsyncExitStack()
            exit_stack = self._exit_stack
        stdio_transport = await self._get_transport(exit_stack=exit_stack)
        mcp_session = await exit_stack.enter_async_context(
            ClientSession(
                read_stream=stdio_transport[0],
                write_stream=stdio_transport[1],
            )
        )
        await mcp_session.initialize()
        self._session = mcp_session
        self._is_initialized = True

    async def aclose(self):
        """Close the MCP session."""
        if self._exit_stack:
            await self._exit_stack.aclose()

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self._name!r} id=0x{id(self):x}>"

    def __str__(self):
        return f"{self.__class__.__name__}(name={self._name})"

    async def _get_transport(self, exit_stack: AsyncExitStack):
        raise NotImplementedError
