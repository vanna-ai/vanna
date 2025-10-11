"""Tool execution component (legacy)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ....core.rich_component import RichComponent, ComponentType


class LogEntry(BaseModel):
    """Log entry for tool execution."""

    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "info"  # "debug", "info", "warning", "error"
    message: str
    data: Optional[Dict[str, Any]] = None


class ToolExecutionComponent(RichComponent):
    """Component for displaying tool execution status and progress.

    DEPRECATED: Use StatusCardComponent instead for new code.
    This component is maintained for backward compatibility.
    """

    type: ComponentType = ComponentType.TOOL_EXECUTION
    tool_name: str
    status: str = "pending"  # "pending", "running", "completed", "failed"
    progress: Optional[float] = None  # 0.0 to 1.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None  # seconds
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    logs: List[LogEntry] = Field(default_factory=list)
    show_logs: bool = True
    show_arguments: bool = True
    collapsible: bool = True

    def start(self) -> "ToolExecutionComponent":
        """Mark tool execution as started."""
        return self.update(
            status="running",
            start_time=datetime.utcnow().isoformat(),
            progress=0.0
        )

    def update_progress(self, progress: float, message: Optional[str] = None) -> "ToolExecutionComponent":
        """Update execution progress."""
        updates: Dict[str, Any] = {"progress": progress}
        if message:
            new_log = LogEntry(message=message, level="info")
            updates["logs"] = self.logs + [new_log]
        return self.update(**updates)

    def complete(self, result: Any = None) -> "ToolExecutionComponent":
        """Mark tool execution as completed."""
        end_time = datetime.utcnow().isoformat()
        updates = {
            "status": "completed",
            "progress": 1.0,
            "end_time": end_time,
            "result": result
        }

        # Calculate duration if start_time is available
        if self.start_time:
            try:
                start_dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                updates["duration"] = (end_dt - start_dt).total_seconds()
            except ValueError:
                pass  # Skip duration calculation if parsing fails

        return self.update(**updates)

    def fail(self, error: str) -> "ToolExecutionComponent":
        """Mark tool execution as failed."""
        return self.update(
            status="failed",
            error=error,
            end_time=datetime.utcnow().isoformat()
        )

    def add_log(self, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> "ToolExecutionComponent":
        """Add a log entry."""
        new_log = LogEntry(message=message, level=level, data=data)
        return self.update(logs=self.logs + [new_log])
