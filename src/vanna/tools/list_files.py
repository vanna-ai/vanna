"""Simple mock tool for listing files."""
import os
from typing import Type
from pydantic import BaseModel
from vanna.core.interfaces import Tool
from vanna.core.models import ToolContext, ToolResult


class ListFilesArgs(BaseModel):
    """Arguments for list_files tool (no arguments required)."""
    pass


class ListFilesTool(Tool[ListFilesArgs]):
    """Mock tool that lists files in the current directory."""

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files in the current directory"

    def get_args_schema(self) -> Type[ListFilesArgs]:
        return ListFilesArgs

    async def execute(self, context: ToolContext, args: ListFilesArgs) -> ToolResult:
        """List files in the current directory."""
        try:
            files = os.listdir('.')
            files = [f for f in files if os.path.isfile(f)]
            if not files:
                result = "No files found in current directory"
            else:
                result = "Files in current directory:\n" + "\n".join(f"- {file}" for file in sorted(files))

            return ToolResult(
                success=True,
                result_for_llm=result,
                metadata={"file_count": len(files)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result_for_llm=f"Error listing files: {str(e)}",
                error=str(e),
                metadata={}
            )