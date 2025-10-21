"""
Core components of the Vanna Agents framework.

This package contains the fundamental abstractions and implementations
that form the foundation of the agent framework.
"""

# Core domains - re-export from new structure
from .tool import T, Tool, ToolCall, ToolContext, ToolResult, ToolSchema
from .llm import LlmMessage, LlmRequest, LlmResponse, LlmService, LlmStreamChunk
from .storage import Conversation, ConversationStore, Message
from .user import User, UserService
from .agent import Agent, AgentConfig
from .system_prompt import DefaultSystemPromptBuilder, SystemPromptBuilder
from .lifecycle import LifecycleHook
from .middleware import LlmMiddleware
from .workflow import WorkflowTrigger, TriggerResult
from .recovery import ErrorRecoveryStrategy, RecoveryAction, RecoveryActionType
from .enricher import ContextEnricher
from .filter import ConversationFilter
from .observability import ObservabilityProvider, Span, Metric
from .audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    ToolAccessCheckEvent,
    ToolInvocationEvent,
    ToolResultEvent,
    UiFeatureAccessCheckEvent,
    AiResponseEvent,
)

# UI Components
from .components import UiComponent
from .rich_component import RichComponent
from ..components import (
    SimpleComponent,
    SimpleComponentType,
    SimpleImageComponent,
    SimpleLinkComponent,
    SimpleTextComponent,
    ArtifactComponent,
    BadgeComponent,
    CardComponent,
    DataFrameComponent,
    IconTextComponent,
    LogViewerComponent,
    NotificationComponent,
    ProgressBarComponent,
    ProgressDisplayComponent,
    RichTextComponent,
    StatusCardComponent,
    TaskListComponent,
    ToolExecutionComponent,
)

# Exceptions
from .errors import (
    AgentError,
    ConversationNotFoundError,
    LlmServiceError,
    PermissionError,
    ToolExecutionError,
    ToolNotFoundError,
    ValidationError,
)

# Core implementations
from .registry import ToolRegistry

# Evaluation framework
from .evaluation import (
    Evaluator,
    TestCase,
    ExpectedOutcome,
    AgentResult,
    EvaluationResult,
    TestCaseResult,
    AgentVariant,
    EvaluationRunner,
    TrajectoryEvaluator,
    OutputEvaluator,
    LLMAsJudgeEvaluator,
    EfficiencyEvaluator,
    EvaluationReport,
    ComparisonReport,
    EvaluationDataset,
)

# Rebuild models to resolve forward references after all imports
from .tool.models import ToolContext, ToolResult
from .components import UiComponent  # Import UiComponent to ensure it's available
ToolContext.model_rebuild()
ToolResult.model_rebuild()

__all__ = [
    # Models
    "User",
    "Message",
    "Conversation",
    "ToolCall",
    "ToolResult",
    "ToolContext",
    "ToolSchema",
    "LlmMessage",
    "LlmRequest",
    "LlmResponse",
    "LlmStreamChunk",
    "RecoveryAction",
    "RecoveryActionType",
    "Span",
    "Metric",
    # Interfaces
    "Tool",
    "Agent",
    "LlmService",
    "ConversationStore",
    "UserService",
    "SystemPromptBuilder",
    "LifecycleHook",
    "LlmMiddleware",
    "WorkflowTrigger",
    "TriggerResult",
    "ErrorRecoveryStrategy",
    "ContextEnricher",
    "ConversationFilter",
    "ObservabilityProvider",
    "AuditLogger",
    "T",
    # Audit
    "AuditEvent",
    "AuditEventType",
    "ToolAccessCheckEvent",
    "ToolInvocationEvent",
    "ToolResultEvent",
    "UiFeatureAccessCheckEvent",
    "AiResponseEvent",
    # UI Components
    "UiComponent",
    # Simple Components
    "SimpleComponent",
    "SimpleComponentType",
    "SimpleTextComponent",
    "SimpleImageComponent",
    "SimpleLinkComponent",
    # Rich Components
    "RichComponent",
    "ArtifactComponent",
    "BadgeComponent",
    "CardComponent",
    "DataFrameComponent",
    "IconTextComponent",
    "LogViewerComponent",
    "NotificationComponent",
    "ProgressBarComponent",
    "ProgressDisplayComponent",
    "RichTextComponent",
    "StatusCardComponent",
    "TaskListComponent",
    "ToolExecutionComponent",
    # Core implementations
    "ToolRegistry",
    "Agent",
    "AgentConfig",
    "DefaultSystemPromptBuilder",
    # Evaluation
    "Evaluator",
    "TestCase",
    "ExpectedOutcome",
    "AgentResult",
    "EvaluationResult",
    "TestCaseResult",
    "AgentVariant",
    "EvaluationRunner",
    "TrajectoryEvaluator",
    "OutputEvaluator",
    "LLMAsJudgeEvaluator",
    "EfficiencyEvaluator",
    "EvaluationReport",
    "ComparisonReport",
    "EvaluationDataset",
    # Exceptions
    "AgentError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "PermissionError",
    "ConversationNotFoundError",
    "LlmServiceError",
    "ValidationError",
]
