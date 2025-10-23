"""
Agent configuration.

This module contains configuration models that control agent behavior.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from pydantic import BaseModel, Field

try:
    from enum import StrEnum  # Py 3.11+
except ImportError:  # Py < 3.11
    from enum import Enum
    class StrEnum(str, Enum):  # minimal backport
        pass

if TYPE_CHECKING:
    from ..user import User


class UiFeature(StrEnum):
    UI_FEATURE_SHOW_TOOL_NAMES = "tool_names"
    UI_FEATURE_SHOW_TOOL_ARGUMENTS = "tool_arguments"
    UI_FEATURE_SHOW_TOOL_ERROR = "tool_error"
    UI_FEATURE_SHOW_TOOL_INVOCATION_MESSAGE_IN_CHAT = "tool_invocation_message_in_chat"

# Optional: you can also define defaults if you want a shared baseline
DEFAULT_UI_FEATURES: Dict[str, List[str]] = {
    UiFeature.UI_FEATURE_SHOW_TOOL_NAMES: ["admin", "user"],
    UiFeature.UI_FEATURE_SHOW_TOOL_ARGUMENTS: ["admin"],
    UiFeature.UI_FEATURE_SHOW_TOOL_ERROR: ["admin"],
    UiFeature.UI_FEATURE_SHOW_TOOL_INVOCATION_MESSAGE_IN_CHAT: ["admin"],
}

class UiFeatures(BaseModel):
    """UI features with group-based access control using the same pattern as tools.
    
    Each field specifies which groups can access that UI feature.
    Empty list means the feature is accessible to all users.
    Uses the same intersection logic as tool access control.
    """
    
    # Custom features for extensibility
    feature_group_access: Dict[str, List[str]] = Field(
        default_factory=lambda: DEFAULT_UI_FEATURES.copy(),
        description="Which groups can access UI features",
    )
    
    def can_user_access_feature(self, feature_name: str, user: "User") -> bool:
        """Check if user can access a UI feature using same logic as tools.
        
        Args:
            feature_name: Name of the UI feature to check
            user: User object with group_memberships
            
        Returns:
            True if user has access, False otherwise
        """
        # Then try custom features
        if feature_name in self.feature_group_access:
            allowed_groups = self.feature_group_access[feature_name]
        else:
            # Feature doesn't exist, deny access
            return False
        
        # Empty list means all users can access (same as tools)
        if not allowed_groups:
            return True
        
        # Same intersection logic as tool access control
        user_groups = set(user.group_memberships)
        feature_groups = set(allowed_groups)
        return bool(user_groups & feature_groups)
    
    def register_feature(self, name: str, access_groups: List[str]) -> None:
        """Register a custom UI feature with group access control.

        Args:
            name: Name of the custom feature
            access_groups: List of groups that can access this feature
        """
        self.feature_group_access[name] = access_groups


class AuditConfig(BaseModel):
    """Configuration for audit logging."""

    enabled: bool = Field(default=True, description="Enable audit logging")
    log_tool_access_checks: bool = Field(
        default=True, description="Log tool access permission checks"
    )
    log_tool_invocations: bool = Field(
        default=True, description="Log tool invocations with parameters"
    )
    log_tool_results: bool = Field(
        default=True, description="Log tool execution results"
    )
    log_ui_feature_checks: bool = Field(
        default=False, description="Log UI feature access checks (can be noisy)"
    )
    log_ai_responses: bool = Field(
        default=True, description="Log AI-generated responses"
    )
    include_full_ai_responses: bool = Field(
        default=False,
        description="Include full AI response text in logs (privacy concern)",
    )
    sanitize_tool_parameters: bool = Field(
        default=True, description="Sanitize sensitive parameters (passwords, tokens)"
    )


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""

    max_tool_iterations: int = Field(default=10, gt=0)
    stream_responses: bool = Field(default=True)
    auto_save_conversations: bool = Field(default=True)
    include_thinking_indicators: bool = Field(default=True)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    ui_features: UiFeatures = Field(default_factory=UiFeatures)
    audit_config: AuditConfig = Field(default_factory=AuditConfig)
