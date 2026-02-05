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
    ChartComponent,
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
    # Specialized
    ArtifactComponent,
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
    "ChartComponent",
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
    # Rich components - Specialized
    "ArtifactComponent",
]
