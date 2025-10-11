"""
Example coding agent using the vanna-agents framework.

This example demonstrates building an agent that can edit code files,
following the concepts from the "How to Build an Agent" article.
The agent includes tools for file operations and uses an LLM service
that can understand and modify code.

Usage:
  PYTHONPATH=. python vanna/examples/coding_agent_example.py
"""

import asyncio
import uuid
from typing import AsyncGenerator, List, Optional

from vanna import (
    AgentConfig,
    Agent,
    ToolRegistry,
    User,
)
from vanna.core.interfaces import LlmService
from vanna.core.models import (
    LlmRequest,
    LlmResponse,
    LlmStreamChunk,
    ToolCall,
    ToolSchema,
)
from vanna.tools.file_system import create_file_system_tools
from vanna.tools.python import create_python_tools



class CodingLlmService(LlmService):
    """
    LLM service that simulates a coding assistant.

    This demonstrates the minimal implementation needed for an agent
    as described in the article - just needs to understand tool calls
    and respond appropriately.
    """

    async def send_request(self, request: LlmRequest) -> LlmResponse:
        """Handle non-streaming requests."""
        await asyncio.sleep(0.1)  # Simulate thinking time
        return self._build_response(request)

    async def stream_request(self, request: LlmRequest) -> AsyncGenerator[LlmStreamChunk, None]:
        """Handle streaming requests."""
        await asyncio.sleep(0.1)
        response = self._build_response(request)

        if response.tool_calls:
            yield LlmStreamChunk(tool_calls=response.tool_calls)
        if response.content:
            # Simulate streaming by chunking the response
            words = response.content.split()
            for i, word in enumerate(words):
                chunk = word if i == 0 else f" {word}"
                await asyncio.sleep(0.05)  # Simulate streaming delay
                yield LlmStreamChunk(content=chunk)

        yield LlmStreamChunk(finish_reason=response.finish_reason)

    async def validate_tools(self, tools: List[ToolSchema]) -> List[str]:
        """Validate tools - no errors for this simple implementation."""
        return []

    def _build_response(self, request: LlmRequest) -> LlmResponse:
        """Build a response based on the conversation context."""
        last_message = request.messages[-1] if request.messages else None

        # If we just got a tool result, respond to it
        if last_message and last_message.role == "tool":
            tool_result = last_message.content or "Tool executed"
            return LlmResponse(
                content=f"I've completed the operation. {tool_result}",
                finish_reason="stop"
            )

        # If user is asking for file operations, use tools
        if last_message and last_message.role == "user":
            user_message = last_message.content.lower()

            if "list files" in user_message or "show files" in user_message:
                return LlmResponse(
                    content="I'll list the files for you.",
                    tool_calls=[ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name="list_files",
                        arguments={}
                    )],
                    finish_reason="tool_calls"
                )

            elif "read" in user_message and ("file" in user_message or ".py" in user_message or ".txt" in user_message):
                filename = _extract_filename(user_message)

                if filename:
                    return LlmResponse(
                        content=f"I'll read the file '{filename}' for you.",
                        tool_calls=[ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name="read_file",
                            arguments={"filename": filename}
                        )],
                        finish_reason="tool_calls"
                    )

            elif "create" in user_message or "write" in user_message:
                # Suggest creating a simple example file
                return LlmResponse(
                    content="I'll create an example Python file for you.",
                    tool_calls=[ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name="write_file",
                        arguments={
                            "filename": "example.py",
                            "content": "# Example Python file\nprint('Hello from the coding agent!')\n\ndef greet(name):\n    return f'Hello, {name}!'\n\nif __name__ == '__main__':\n    print(greet('World'))\n",
                            "overwrite": True
                        }
                    )],
                    finish_reason="tool_calls",
                )

            elif ("run" in user_message or "execute" in user_message) and ".py" in user_message:
                filename = _extract_filename(user_message)
                if filename:
                    return LlmResponse(
                        content=f"I'll run the Python file '{filename}'.",
                        tool_calls=[ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name="run_python_file",
                            arguments={
                                "filename": filename,
                                "arguments": [],
                            }
                        )],
                        finish_reason="tool_calls",
                    )

            elif "edit" in user_message or "update" in user_message or "modify" in user_message:
                return LlmResponse(
                    content="I'll update the greet function to make it more descriptive.",
                    tool_calls=[ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name="edit_file",
                        arguments={
                            "filename": "example.py",
                            "edits": [
                                {
                                    "start_line": 4,
                                    "end_line": 5,
                                    "new_content": (
                                        "def greet(name):\n"
                                        "    \"\"\"Return a friendly greeting.\"\"\"\n"
                                        "    return f\"Hello, {name}! Welcome to the coding agent.\"\n"
                                    ),
                                }
                            ],
                        },
                    )],
                    finish_reason="tool_calls",
                )

        # Default response
        return LlmResponse(
            content=(
                "I'm a coding assistant. I can help you list, read, write, edit, and run Python files. "
                "Try asking me to 'list files', 'read example.py', 'create a Python file', 'run example.py', or 'update example.py'."
            ),
            finish_reason="stop"
        )


def create_demo_agent() -> Agent:
    """
    Create a coding agent with file operation tools.

    This follows the pattern from the article - minimal code
    to create a powerful code-editing agent. Uses dependency injection
    for file system operations with LocalFileSystem as default.
    """
    # Create tool registry and register file system tools
    tool_registry = ToolRegistry()

    # Use the convenience function to create tools with default LocalFileSystem
    for tool in create_file_system_tools():
        tool_registry.register(tool)

    for tool in create_python_tools():
        tool_registry.register(tool)

    # Create LLM service
    llm_service = CodingLlmService()

    # Create agent with configuration
    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=True,
            max_tool_iterations=3,
        ),
    )


async def main() -> None:
    """
    Demonstrate the coding agent in action.

    As the article mentions: "300 lines of code and three tools and now
    you're able to talk to an alien intelligence that edits your code."
    """
    print("🤖 Starting Coding Agent Demo")
    print("This demonstrates the concepts from 'How to Build an Agent'")
    print("-" * 50)

    # Create the agent
    agent = create_demo_agent()

    # Create a test user
    user = User(id="coder123", username="developer", permissions=[])

    # Show available tools
    tools = await agent.get_available_tools(user)
    print(f"Available tools: {[tool.name for tool in tools]}")
    print()

    # Demo conversation
    conversation_id = "coding-session"

    demos = [
        "Hello! Can you list the files in this directory?",
        "Can you create a simple Python file for me?",
        "Now read the example.py file you just created",
        "Please update the greet function to include a docstring and a friendlier message.",
        "Run example.py so I can see its output.",
        "Great, read example.py again to confirm the changes.",
    ]

    for i, message in enumerate(demos, 1):
        print(f"Demo {i}: {message}")
        print("Agent response:")

        async for component in agent.send_message(
            user=user,
            message=message,
            conversation_id=conversation_id
        ):
            if hasattr(component.rich_component, 'content') and component.rich_component.content:
                print(f"  📝 {component.rich_component.content}")
            elif hasattr(component.rich_component, 'message'):
                print(f"  💬 {component.rich_component.message}")
            elif component.simple_component and hasattr(component.simple_component, 'text'):
                print(f"  📄 {component.simple_component.text}")

        print("-" * 30)


def _extract_filename(message: str) -> Optional[str]:
    """Extract a likely filename token from a user message."""

    for token in message.replace("\n", " ").split():
        cleaned = token.strip("'\".,;!?")
        if "." in cleaned and not cleaned.startswith("."):
            return cleaned

    return None


if __name__ == "__main__":
    asyncio.run(main())
