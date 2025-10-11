"""UI state update components for controlling interface elements."""

from enum import Enum
from typing import Any, Optional
from .task_list import Task
from ....core.rich_component import RichComponent, ComponentType


class StatusBarUpdateComponent(RichComponent):
    """Component for updating the status bar above chat input."""

    type: ComponentType = ComponentType.STATUS_BAR_UPDATE
    status: str  # "idle", "working", "success", "error"
    message: str
    detail: Optional[str] = None

    def __init__(self, **kwargs: Any) -> None:
        # Set a fixed ID for status bar updates
        kwargs.setdefault('id', 'vanna-status-bar')
        super().__init__(**kwargs)


class TaskOperation(str, Enum):
    """Operations for task tracker updates."""

    ADD_TASK = "add_task"
    UPDATE_TASK = "update_task"
    REMOVE_TASK = "remove_task"
    CLEAR_TASKS = "clear_tasks"


class TaskTrackerUpdateComponent(RichComponent):
    """Component for updating the task tracker in the sidebar."""

    type: ComponentType = ComponentType.TASK_TRACKER_UPDATE
    operation: TaskOperation
    task: Optional[Task] = None  # Used for ADD_TASK
    task_id: Optional[str] = None  # Used for UPDATE_TASK and REMOVE_TASK
    status: Optional[str] = None  # Used for UPDATE_TASK
    progress: Optional[float] = None  # Used for UPDATE_TASK
    detail: Optional[str] = None  # Used for UPDATE_TASK

    def __init__(self, **kwargs: Any) -> None:
        # Set a fixed ID for task tracker updates
        kwargs.setdefault('id', 'vanna-task-tracker')
        super().__init__(**kwargs)

    @classmethod
    def add_task(cls, task: Task) -> "TaskTrackerUpdateComponent":
        """Create a component to add a new task."""
        return cls(operation=TaskOperation.ADD_TASK, task=task)

    @classmethod
    def update_task(cls, task_id: str, status: Optional[str] = None,
                   progress: Optional[float] = None, detail: Optional[str] = None) -> "TaskTrackerUpdateComponent":
        """Create a component to update an existing task."""
        return cls(
            operation=TaskOperation.UPDATE_TASK,
            task_id=task_id,
            status=status,
            progress=progress,
            detail=detail
        )

    @classmethod
    def remove_task(cls, task_id: str) -> "TaskTrackerUpdateComponent":
        """Create a component to remove a task."""
        return cls(operation=TaskOperation.REMOVE_TASK, task_id=task_id)

    @classmethod
    def clear_tasks(cls) -> "TaskTrackerUpdateComponent":
        """Create a component to clear all tasks."""
        return cls(operation=TaskOperation.CLEAR_TASKS)


class ChatInputUpdateComponent(RichComponent):
    """Component for updating chat input state and appearance."""

    type: ComponentType = ComponentType.CHAT_INPUT_UPDATE
    placeholder: Optional[str] = None
    disabled: Optional[bool] = None
    value: Optional[str] = None  # Set input text value
    focus: Optional[bool] = None  # Focus/unfocus the input

    def __init__(self, **kwargs: Any) -> None:
        # Set a fixed ID for chat input updates
        kwargs.setdefault('id', 'vanna-chat-input')
        super().__init__(**kwargs)
