"""UI Component system for Vanna Agents."""

# Base component
from .base import UiComponent

# Simple components
from .simple import (
    SimpleComponent,
    SimpleComponentType,
    SimpleTextComponent,
    SimpleImageComponent,
    SimpleLinkComponent,
)

# Rich components - re-export all
from .rich import (
    # Base
    RichComponent,
    ComponentType,
    ComponentLifecycle,
    # Text
    RichTextComponent,
    # Data
    DataFrameComponent,
    TableComponent,
    TableColumn,
    ChartComponent,
    CodeBlockComponent,
    # Feedback
    NotificationComponent,
    StatusCardComponent,
    ProgressBarComponent,
    ProgressDisplayComponent,
    StatusIndicatorComponent,
    LogViewerComponent,
    LogEntry,
    BadgeComponent,
    IconTextComponent,
    # Interactive
    TaskListComponent,
    Task,
    StatusBarUpdateComponent,
    TaskTrackerUpdateComponent,
    ChatInputUpdateComponent,
    TaskOperation,
    ButtonComponent,
    ButtonGroupComponent,
    # Containers
    CardComponent,
    ContainerComponent,
    # Specialized
    ArtifactComponent,
    ToolExecutionComponent,
)

__all__ = [
    # Base
    "UiComponent",
    # Simple components
    "SimpleComponent",
    "SimpleComponentType",
    "SimpleTextComponent",
    "SimpleImageComponent",
    "SimpleLinkComponent",
    # Rich components - Base
    "RichComponent",
    "ComponentType",
    "ComponentLifecycle",
    # Rich components - Text
    "RichTextComponent",
    # Rich components - Data
    "DataFrameComponent",
    "TableComponent",
    "TableColumn",
    "ChartComponent",
    "CodeBlockComponent",
    # Rich components - Feedback
    "NotificationComponent",
    "StatusCardComponent",
    "ProgressBarComponent",
    "ProgressDisplayComponent",
    "StatusIndicatorComponent",
    "LogViewerComponent",
    "LogEntry",
    "BadgeComponent",
    "IconTextComponent",
    # Rich components - Interactive
    "TaskListComponent",
    "Task",
    "StatusBarUpdateComponent",
    "TaskTrackerUpdateComponent",
    "ChatInputUpdateComponent",
    "TaskOperation",
    "ButtonComponent",
    "ButtonGroupComponent",
    # Rich components - Containers
    "CardComponent",
    "ContainerComponent",
    # Rich components - Specialized
    "ArtifactComponent",
    "ToolExecutionComponent",
]
