"""
Agent memory tools with dependency injection support.

This module provides agent memory operations through an abstract AgentMemory interface,
allowing for different implementations (local vector DB, remote cloud service, etc.).
The tools accept an AgentMemory instance via dependency injection.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from vanna.core.tool import Tool, ToolContext, ToolResult
from vanna.capabilities.agent_memory import AgentMemory
from vanna.components import (
    UiComponent,
    StatusBarUpdateComponent,
)


class SaveQuestionToolArgsParams(BaseModel):
    """Parameters for saving question-tool-argument combinations."""
    question: str = Field(description="The original question that was asked")
    tool_name: str = Field(description="The name of the tool that was used successfully")
    args: Dict[str, Any] = Field(description="The arguments that were passed to the tool")


class SearchSavedCorrectToolUsesParams(BaseModel):
    """Parameters for searching saved tool usage patterns."""
    question: str = Field(description="The question to find similar tool usage patterns for")
    limit: Optional[int] = Field(default=10, description="Maximum number of results to return")
    similarity_threshold: Optional[float] = Field(
        default=0.7, 
        description="Minimum similarity score for results (0.0-1.0)"
    )
    tool_name_filter: Optional[str] = Field(
        default=None,
        description="Filter results to specific tool name"
    )


class SaveQuestionToolArgsTool(Tool[SaveQuestionToolArgsParams]):
    """Tool for saving successful question-tool-argument combinations."""

    def __init__(self, agent_memory: AgentMemory):
        self.agent_memory = agent_memory

    @property
    def name(self) -> str:
        return "save_question_tool_args"

    @property
    def description(self) -> str:
        return "Save a successful question-tool-argument combination for future reference"

    def get_args_schema(self) -> Type[SaveQuestionToolArgsParams]:
        return SaveQuestionToolArgsParams

    async def execute(self, context: ToolContext, args: SaveQuestionToolArgsParams) -> ToolResult:
        """Save the tool usage pattern to agent memory."""
        try:
            await self.agent_memory.save_tool_usage(
                question=args.question,
                tool_name=args.tool_name,
                args=args.args,
                context=context,
                success=True
            )

            success_msg = f"Successfully saved usage pattern for '{args.tool_name}' tool"
            return ToolResult(
                success=True,
                result_for_llm=success_msg,
                ui_component=UiComponent(
                    rich_component=StatusBarUpdateComponent(
                        status="success",
                        message="Saved to memory",
                        detail=f"Saved pattern for '{args.tool_name}'"
                    )
                )
            )
            
        except Exception as e:
            error_message = f"Failed to save memory: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_message,
                ui_component=UiComponent(
                    rich_component=StatusBarUpdateComponent(
                        status="error",
                        message="Failed to save memory",
                        detail=str(e)
                    )
                ),
                error=str(e)
            )


class SearchSavedCorrectToolUsesTool(Tool[SearchSavedCorrectToolUsesParams]):
    """Tool for searching saved tool usage patterns."""

    def __init__(self, agent_memory: AgentMemory):
        self.agent_memory = agent_memory

    @property
    def name(self) -> str:
        return "search_saved_correct_tool_uses"

    @property
    def description(self) -> str:
        return "Search for similar tool usage patterns based on a question"

    def get_args_schema(self) -> Type[SearchSavedCorrectToolUsesParams]:
        return SearchSavedCorrectToolUsesParams

    async def execute(self, context: ToolContext, args: SearchSavedCorrectToolUsesParams) -> ToolResult:
        """Search for similar tool usage patterns."""
        try:
            results = await self.agent_memory.search_similar_usage(
                question=args.question,
                context=context,
                limit=args.limit or 10,
                similarity_threshold=args.similarity_threshold or 0.7,
                tool_name_filter=args.tool_name_filter
            )

            if not results:
                no_results_msg = "No similar tool usage patterns found for this question."
                return ToolResult(
                    success=True,
                    result_for_llm=no_results_msg,
                    ui_component=UiComponent(
                        rich_component=StatusBarUpdateComponent(
                            status="idle",
                            message="No similar patterns found",
                            detail="Searched agent memory"
                        )
                    )
                )

            # Format results for LLM
            results_text = f"Found {len(results)} similar tool usage pattern(s):\n\n"
            for i, result in enumerate(results, 1):
                memory = result.memory
                results_text += f"{i}. {memory.tool_name} (similarity: {result.similarity_score:.2f})\n"
                results_text += f"   Question: {memory.question}\n"
                results_text += f"   Args: {memory.args}\n\n"

            logger.info(f"Agent memory search results: {results_text.strip()}")

            return ToolResult(
                success=True,
                result_for_llm=results_text.strip(),
                ui_component=UiComponent(
                    rich_component=StatusBarUpdateComponent(
                        status="success",
                        message=f"Found {len(results)} similar pattern(s)",
                        detail="Retrieved from agent memory"
                    )
                )
            )

        except Exception as e:
            error_message = f"Failed to search memories: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_message,
                ui_component=UiComponent(
                    rich_component=StatusBarUpdateComponent(
                        status="error",
                        message="Failed to search memory",
                        detail=str(e)
                    )
                ),
                error=str(e)
            )


def create_memory_tools(agent_memory: AgentMemory) -> List[Tool]:
    """Create agent memory tools with the given implementation."""
    return [
        SaveQuestionToolArgsTool(agent_memory),
        SearchSavedCorrectToolUsesTool(agent_memory)
    ]