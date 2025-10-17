"""
Mock example showing how to create and use custom tools.

This example demonstrates creating a simple calculator tool
and registering it with an agent that uses a mock LLM service.
It now includes a `MockCalculatorLlmService` that automatically
invokes the calculator tool with random numbers before echoing
back the computed answer.

Usage:
  Template: Copy this file and modify for your custom tools
  Interactive: python -m vanna.examples.mock_custom_tool
  REPL: from vanna.examples.mock_custom_tool import create_demo_agent
  Server: python -m vanna.servers --example mock_custom_tool
"""

import asyncio
import random
import uuid
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, Field

from vanna import (
    AgentConfig,
    Agent,
    Tool,
    ToolContext,
    ToolRegistry,
    ToolResult,
    User,
    UiComponent,
)
from vanna.core.interfaces import LlmService
from vanna.core.models import (
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
    ToolCall,
    ToolSchema,
)
from vanna.core.rich_components import (
    CardComponent,
    NotificationComponent,
    ComponentType,
)
from vanna.core.simple_components import (
    SimpleTextComponent,
)


class CalculatorArgs(BaseModel):
    """Arguments for the calculator tool."""

    operation: str = Field(
        description="The operation to perform: add, subtract, multiply, divide"
    )
    a: float = Field(description="First number")
    b: float = Field(description="Second number")


class CalculatorTool(Tool[CalculatorArgs]):
    """A simple calculator tool."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform basic arithmetic operations (add, subtract, multiply, divide)"

    def get_args_schema(self) -> Type[CalculatorArgs]:
        return CalculatorArgs

    async def execute(self, context: ToolContext, args: CalculatorArgs) -> ToolResult:
        """Execute the calculator operation."""
        symbol_map = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}

        try:
            if args.operation == "add":
                result = args.a + args.b
            elif args.operation == "subtract":
                result = args.a - args.b
            elif args.operation == "multiply":
                result = args.a * args.b
            elif args.operation == "divide":
                if args.b == 0:
                    message = "Cannot divide by zero"
                    await asyncio.sleep(3)
                    return ToolResult(
                        success=False,
                        result_for_llm=message,
                        ui_component=UiComponent(
                            rich_component=NotificationComponent(
                                type=ComponentType.NOTIFICATION,
                                level="error",
                                message=message,
                            ),
                            simple_component=SimpleTextComponent(text=message),
                        ),
                        error=message,
                    )
                result = args.a / args.b
            else:
                message = f"Unknown operation: {args.operation}"
                await asyncio.sleep(3)
                return ToolResult(
                    success=False,
                    result_for_llm=message,
                    ui_component=UiComponent(
                        rich_component=NotificationComponent(
                            type=ComponentType.NOTIFICATION,
                            level="warning",
                            message=message,
                        ),
                        simple_component=SimpleTextComponent(text=message),
                    ),
                    error=message,
                )

            await asyncio.sleep(3)

            symbol = symbol_map.get(args.operation, args.operation)
            expression = f"{args.a:g} {symbol} {args.b:g} = {result:g}"
            return ToolResult(
                success=True,
                result_for_llm=str(result),
                ui_component=UiComponent(
                    rich_component=CardComponent(
                        type=ComponentType.CARD,
                        title="Calculator Result",
                        content=expression,
                    ),
                    simple_component=SimpleTextComponent(text=expression),
                ),
                error=None,
            )

        except Exception as e:
            message = str(e)
            await asyncio.sleep(3)
            return ToolResult(
                success=False,
                result_for_llm=message,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=message,
                    ),
                    simple_component=SimpleTextComponent(text=message),
                ),
                error=message,
            )


class MockCalculatorLlmService(LlmService):
    """LLM service that exercises the calculator tool before echoing the result."""

    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random(seed)

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Handle non-streaming calculator interactions."""
        await asyncio.sleep(0.05)
        return self._build_response(request)

    async def stream_request(
        self, request: LlmRequest
    ) -> AsyncGenerator[LlmStreamChunk, None]:
        """Provide streaming compatibility by yielding a single chunk."""
        await asyncio.sleep(0.05)
        response = self._build_response(request)

        if response.tool_calls:
            yield LlmStreamChunk(tool_calls=response.tool_calls)
        if response.content is not None:
            yield LlmStreamChunk(content=response.content, finish_reason=response.finish_reason)
        else:
            yield LlmStreamChunk(finish_reason=response.finish_reason)

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Mock validation - no errors."""
        return []

    def _build_response(self, request: LlmRequest) -> LlmResponse:
        """Create a response that either calls the tool or echoes its result."""
        last_message = request.messages[-1] if request.messages else None

        if last_message and last_message.role == "tool":
            answer = last_message.content or "No result provided"
            return LlmResponse(
                content=answer,
                finish_reason="stop",
                usage={"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
            )

        operation, a, b = self._random_operands()
        tool_call = ToolCall(
            id=f"call_{uuid.uuid4().hex[:8]}",
            name="calculator",
            arguments={"operation": operation, "a": a, "b": b},
        )

        return LlmResponse(
            content="Let me ask my calculator friend for help...",
            tool_calls=[tool_call],
            finish_reason="tool_calls",
            usage={"prompt_tokens": 30, "completion_tokens": 5, "total_tokens": 35},
        )

    def _random_operands(self) -> Tuple[str, float, float]:
        """Generate operation and operands suited for the calculator tool."""
        operation = self._random.choice(["add", "subtract", "multiply", "divide"])

        if operation == "divide":
            b = float(self._random.randint(1, 10))
            multiplier = self._random.randint(1, 10)
            a = float(b * multiplier)
        elif operation == "subtract":
            b = float(self._random.randint(1, 10))
            a = b + float(self._random.randint(0, 10))
        else:
            a = float(self._random.randint(1, 12))
            b = float(self._random.randint(1, 12))

        return operation, a, b


def create_demo_agent() -> Agent:
    """Create a demo agent with custom calculator tool.

    Returns:
        Configured Agent with calculator tool and mock calculator LLM
    """
    tool_registry = ToolRegistry()
    calculator_tool = CalculatorTool()
    tool_registry.register(calculator_tool)

    llm_service = MockCalculatorLlmService()

    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        config=AgentConfig(
            stream_responses=False,
            include_thinking_indicators=False,
        ),
    )


async def main() -> None:
    """Run the mock custom tool example."""

    # Create agent using factory function
    agent = create_demo_agent()
    tool_registry = agent.tool_registry

    # Create a test user
    user = User(id="user123", username="testuser", permissions=[])

    # Test the tool directly
    print("Testing calculator tool directly:")
    tool_call = ToolCall(
        id="test123", name="calculator", arguments={"operation": "add", "a": 5, "b": 3}
    )

    context = ToolContext(user=user, conversation_id="test", request_id="test")

    result = await tool_registry.execute(tool_call, context)
    print(f"5 + 3 = {result.result_for_llm if result.success else result.error}")

    # Show available tools
    schemas = await tool_registry.get_schemas(user)
    print(
        f"\nAvailable tools for user: {[schema.name for schema in schemas]}"
    )

    # Demonstrate the mock LLM triggering a tool call
    print("\nAgent conversation demo:")
    conversation_id = "calc-demo"
    async for component in agent.send_message(
        user=user,
        message="Can you compute something for me?",
        conversation_id=conversation_id
    ):
        print(f"- Component type: {component.rich_component.type}")
        if hasattr(component.rich_component, "content") and component.rich_component.content:
            print(f"Assistant: {component.rich_component.content}")
        elif component.simple_component and hasattr(component.simple_component, "text"):
            print(f"Assistant: {component.simple_component.text}")
        else:
            print(f"- Component data: {component.rich_component.data}")


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting mock custom tool example...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()
