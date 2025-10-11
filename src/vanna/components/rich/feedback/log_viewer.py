"""Log viewer component."""

import uuid
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


class LogViewerComponent(RichComponent):
    """Generic log viewer for displaying timestamped entries."""

    type: ComponentType = ComponentType.LOG_VIEWER
    title: str = "Logs"
    entries: List[LogEntry] = Field(default_factory=list)
    max_entries: int = 100
    searchable: bool = True
    show_timestamps: bool = True
    auto_scroll: bool = True

    def add_entry(self, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> "LogViewerComponent":
        """Add a new log entry."""
        new_entry = LogEntry(message=message, level=level, data=data)
        new_entries = self.entries + [new_entry]

        # Limit to max_entries
        if len(new_entries) > self.max_entries:
            new_entries = new_entries[-self.max_entries:]

        return self.update(entries=new_entries)
