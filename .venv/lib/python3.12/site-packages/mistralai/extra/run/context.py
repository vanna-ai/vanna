import asyncio
import inspect
import typing
from collections.abc import Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from functools import wraps
from logging import getLogger

import pydantic

from mistralai.extra import response_format_from_pydantic_model
from mistralai.extra.exceptions import RunException
from mistralai.extra.mcp.base import MCPClientProtocol
from mistralai.extra.run.result import RunResult
from mistralai.extra.run.tools import (
    RunCoroutine,
    RunFunction,
    RunMCPTool,
    RunTool,
    create_function_result,
    create_tool_call,
)
from mistralai.models import (
    CompletionArgs,
    CompletionArgsTypedDict,
    ConversationInputs,
    ConversationInputsTypedDict,
    FunctionCallEntry,
    FunctionResultEntry,
    FunctionTool,
    InputEntries,
    MessageInputEntry,
    ResponseFormat,
    Tools,
    ToolsTypedDict,
)
from mistralai.types.basemodel import BaseModel, OptionalNullable, UNSET

if typing.TYPE_CHECKING:
    from mistralai import Beta, OptionalNullable

logger = getLogger(__name__)


class AgentRequestKwargs(typing.TypedDict):
    agent_id: str


class ModelRequestKwargs(typing.TypedDict):
    model: str
    instructions: OptionalNullable[str]
    tools: OptionalNullable[list[Tools] | list[ToolsTypedDict]]
    completion_args: OptionalNullable[CompletionArgs | CompletionArgsTypedDict]


@dataclass
class RunContext:
    """A context for running a conversation with an agent or a model.

    The context can be used to execute function calls, connect to MCP server, and keep track of information about
    the run.

    Args:
        conversation_id (Options[str]): The unique identifier for the conversation. This is
          passed if the user wants to continue an existing conversation.
        model (Options[str]): The model name to be used for the conversation. Can't be used along with 'agent_id'.
        agent_id (Options[str]): The agent id to be used for the conversation. Can't be used along with 'model'.
        output_format (type[BaseModel] | None): The output format expected from the conversation. It represents
          the `response_format` which is part of the `CompletionArgs`.
        request_count (int): The number of requests made in the current `RunContext`.
        continue_on_fn_error (bool): Flag to determine if the conversation should continue when function execution
          resulted in an error.
    """

    _exit_stack: AsyncExitStack = field(init=False)
    _callable_tools: dict[str, RunTool] = field(init=False, default_factory=dict)
    _mcp_clients: list[MCPClientProtocol] = field(init=False, default_factory=list)

    conversation_id: str | None = field(default=None)
    model: str | None = field(default=None)
    agent_id: str | None = field(default=None)
    output_format: type[BaseModel] | None = field(default=None)
    request_count: int = field(default=0)
    continue_on_fn_error: bool = field(default=False)

    def __post_init__(self):
        if self.model and self.agent_id:
            raise RunException("Only one for model or agent_id should be set")
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.aclose()
        for mcp_client in self._mcp_clients:
            await mcp_client.aclose()

    def register_func(self, func: Callable):
        """Add a function to the context."""
        if not inspect.isfunction(func):
            raise RunException(
                "Only object of type function can be registered at the moment."
            )

        if inspect.iscoroutinefunction(func):
            self._callable_tools[func.__name__] = RunCoroutine(
                name=func.__name__,
                awaitable=func,
                tool=create_tool_call(func),
            )
        else:
            self._callable_tools[func.__name__] = RunFunction(
                name=func.__name__,
                callable=func,
                tool=create_tool_call(func),
            )

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Executing {func.__name__}")
            return func(*args, **kwargs)

        return wrapper

    async def register_mcp_clients(self, mcp_clients: list[MCPClientProtocol]) -> None:
        """Registering multiple MCP clients at the same time in the same asyncio.Task."""
        for mcp_client in mcp_clients:
            await self.register_mcp_client(mcp_client)

    async def register_mcp_client(self, mcp_client: MCPClientProtocol) -> None:
        """Add a MCP client to the context."""
        await mcp_client.initialize(exit_stack=self._exit_stack)
        tools = await mcp_client.get_tools()
        for tool in tools:
            logger.info(
                f"Adding tool {tool.function.name} from {mcp_client._name or 'mcp client'}"
            )
            self._callable_tools[tool.function.name] = RunMCPTool(
                name=tool.function.name,
                tool=tool,
                mcp_client=mcp_client,
            )
        self._mcp_clients.append(mcp_client)

    async def execute_function_calls(
        self, function_calls: list[FunctionCallEntry]
    ) -> list[FunctionResultEntry]:
        """Execute function calls and create function results from them."""
        if not all(
            function_call.name in self._callable_tools
            for function_call in function_calls
        ):
            logger.warning("Can't execute all functions, stopping run here")
            return []
        function_result_tasks = []
        for function_call in function_calls:
            function_result_tasks.append(
                asyncio.create_task(
                    create_function_result(
                        function_call=function_call,
                        run_tool=self._callable_tools[function_call.name],
                        continue_on_fn_error=self.continue_on_fn_error,
                    )
                )
            )
        await asyncio.gather(*function_result_tasks)
        return [task.result() for task in function_result_tasks]

    def get_tools(self) -> list[FunctionTool]:
        """Get the tools that are part of the context."""
        callable_tools = [
            run_functions.tool for run_functions in self._callable_tools.values()
        ]
        return callable_tools

    async def prepare_agent_request(self, beta_client: "Beta") -> AgentRequestKwargs:
        """Prepare an agent request with the functions added to the context.

        Update the agent definition before making the request.
        """
        if self.agent_id is None:
            raise RunException(
                "Can't prepare an agent request, if no agent_id is provided"
            )
        agent = await beta_client.agents.get_async(agent_id=self.agent_id)
        agent_tools = agent.tools or []
        updated_tools = []
        for i in range(len(agent_tools)):
            tool = agent_tools[i]
            if tool.type != "function":
                updated_tools.append(tool)
            elif tool.function.name in self._callable_tools:
                # function already exists in the agent, don't add it again
                continue
            else:
                updated_tools.append(tool)
        updated_tools += self.get_tools()
        completion_args = (
            CompletionArgs(response_format=self.response_format)
            if self.output_format
            else None
        )
        beta_client.agents.update(
            agent_id=self.agent_id, tools=updated_tools, completion_args=completion_args
        )
        return AgentRequestKwargs(agent_id=self.agent_id)

    async def prepare_model_request(
        self,
        tools: OptionalNullable[list[Tools] | list[ToolsTypedDict]] = UNSET,
        completion_args: OptionalNullable[CompletionArgs | CompletionArgsTypedDict] = UNSET,
        instructions: OptionalNullable[str] = None,
    ) -> ModelRequestKwargs:
        if self.model is None:
            raise RunException("Can't prepare a model request, if no model is provided")
        if not completion_args and self.output_format:
            completion_args = CompletionArgs(response_format=self.response_format)
        elif isinstance(completion_args, CompletionArgs) and self.output_format:
            completion_args.response_format = self.response_format
        elif isinstance(completion_args, dict) and self.output_format:
            completion_args = CompletionArgs.model_validate(completion_args)
            completion_args.response_format = self.response_format
        request_tools = []
        if isinstance(tools, list):
            for tool in tools:
                request_tools.append(typing.cast(Tools, tool))
        for tool in self.get_tools():
            request_tools.append(tool)
        return ModelRequestKwargs(
            model=self.model,
            tools=request_tools,
            instructions=instructions,
            completion_args=completion_args,
        )

    @property
    def response_format(self) -> ResponseFormat:
        if not self.output_format:
            raise RunException("No response format exist for the current RunContext.")
        return response_format_from_pydantic_model(self.output_format)


async def _validate_run(
    *,
    beta_client: "Beta",
    run_ctx: RunContext,
    inputs: ConversationInputs | ConversationInputsTypedDict,
    instructions: OptionalNullable[str] = UNSET,
    tools: OptionalNullable[list[Tools] | list[ToolsTypedDict]] = UNSET,
    completion_args: OptionalNullable[CompletionArgs | CompletionArgsTypedDict] = UNSET,
) -> tuple[
    AgentRequestKwargs | ModelRequestKwargs, RunResult, list[InputEntries]
]:
    input_entries: list[InputEntries] = []
    if isinstance(inputs, str):
        input_entries.append(MessageInputEntry(role="user", content=inputs))
    else:
        for input in inputs:
            if isinstance(input, dict):
                input_entries.append(
                    pydantic.TypeAdapter(InputEntries).validate_python(input)
                )
    run_result = RunResult(
        input_entries=input_entries,
        output_model=run_ctx.output_format,
        conversation_id=run_ctx.conversation_id,
    )
    req: AgentRequestKwargs | ModelRequestKwargs
    if run_ctx.agent_id:
        if tools or completion_args:
            raise RunException("Can't set tools or completion_args when using an agent")
        req = await run_ctx.prepare_agent_request(beta_client=beta_client)
    elif run_ctx.model:
        req = await run_ctx.prepare_model_request(
            instructions=instructions,
            tools=tools,
            completion_args=completion_args,
        )
    else:
        raise RunException("Either agent_id or model must be set in the run context")
    return req, run_result, input_entries
