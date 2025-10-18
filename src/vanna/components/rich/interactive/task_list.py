"""Task list component for interactive task tracking."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ....core.rich_component import RichComponent, ComponentType


class Task(BaseModel):
    """Individual task in a task list."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: str = "pending"  # "pending", "in_progress", "completed", "error"
    progress: Optional[float] = None  # 0.0 to 1.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskListComponent(RichComponent):
    """Interactive task list with progress tracking."""

    type: ComponentType = ComponentType.TASK_LIST
    title: str = "Tasks"
    tasks: List[Task] = Field(default_factory=list)
    show_progress: bool = True
    allow_reorder: bool = False
    show_timestamps: bool = True
    filter_status: Optional[str] = None  # Filter by task status

    def add_task(self, task: Task) -> "TaskListComponent":
        """Add a task to the list."""
        new_tasks = self.tasks + [task]
        return self.update(tasks=new_tasks)

    def update_task(self, task_id: str, **updates: Any) -> "TaskListComponent":
        """Update a specific task."""
        new_tasks = []
        for task in self.tasks:
            if task.id == task_id:
                task_data = task.model_dump()
                task_data.update(updates)
                new_tasks.append(Task(**task_data))
            else:
                new_tasks.append(task)
        return self.update(tasks=new_tasks)

    def complete_task(self, task_id: str) -> "TaskListComponent":
        """Mark a task as completed."""
        return self.update_task(
            task_id,
            status="completed",
            completed_at=datetime.utcnow().isoformat(),
            progress=1.0
        )
