"""
Base audit logger interface.

Audit loggers enable tracking user actions, tool invocations, and access control
decisions for security, compliance, and debugging.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .models import (
    AiResponseEvent,
    AuditEvent,
    ToolAccessCheckEvent,
    ToolInvocationEvent,
    ToolResultEvent,
    UiFeatureAccessCheckEvent,
)

if TYPE_CHECKING:
    from ..tool.models import ToolCall, ToolContext, ToolResult
    from ..user.models import User


class AuditLogger(ABC):
    """Abstract base class for audit logging implementations.

    Implementations can:
    - Write to files (JSON, CSV, etc.)
    - Send to databases (Postgres, MongoDB, etc.)
    - Stream to cloud services (CloudWatch, Datadog, etc.)
    - Send to SIEM systems (Splunk, Elastic, etc.)

    Example:
        class PostgresAuditLogger(AuditLogger):
            async def log_event(self, event: AuditEvent) -> None:
                await self.db.execute(
                    "INSERT INTO audit_log (...) VALUES (...)",
                    event.model_dump()
                )

        agent = Agent(
            llm_service=...,
            audit_logger=PostgresAuditLogger(db_pool)
        )
    """

    @abstractmethod
    async def log_event(self, event: AuditEvent) -> None:
        """Log a single audit event.

        Args:
            event: The audit event to log

        Raises:
            Exception: If logging fails critically
        """
        pass

    async def log_tool_access_check(
        self,
        user: "User",
        tool_name: str,
        access_granted: bool,
        required_groups: List[str],
        context: "ToolContext",
        reason: Optional[str] = None,
    ) -> None:
        """Convenience method for logging tool access checks.

        Args:
            user: User attempting to access the tool
            tool_name: Name of the tool being accessed
            access_granted: Whether access was granted
            required_groups: Groups required to access the tool
            context: Tool execution context
            reason: Optional reason for denial
        """
        event = ToolAccessCheckEvent(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            user_groups=user.group_memberships,
            conversation_id=context.conversation_id,
            request_id=context.request_id,
            tool_name=tool_name,
            access_granted=access_granted,
            required_groups=required_groups,
            reason=reason,
        )
        await self.log_event(event)

    async def log_tool_invocation(
        self,
        user: "User",
        tool_call: "ToolCall",
        ui_features: List[str],
        context: "ToolContext",
        sanitize_parameters: bool = True,
    ) -> None:
        """Convenience method for logging tool invocations.

        Args:
            user: User invoking the tool
            tool_call: Tool call information
            ui_features: List of UI features available to the user
            context: Tool execution context
            sanitize_parameters: Whether to sanitize sensitive parameters
        """
        parameters = tool_call.arguments.copy()
        sanitized = False

        if sanitize_parameters:
            parameters, sanitized = self._sanitize_parameters(parameters)

        event = ToolInvocationEvent(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            user_groups=user.group_memberships,
            conversation_id=context.conversation_id,
            request_id=context.request_id,
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            parameters=parameters,
            parameters_sanitized=sanitized,
            ui_features_available=ui_features,
        )
        await self.log_event(event)

    async def log_tool_result(
        self,
        user: "User",
        tool_call: "ToolCall",
        result: "ToolResult",
        context: "ToolContext",
    ) -> None:
        """Convenience method for logging tool results.

        Args:
            user: User who invoked the tool
            tool_call: Tool call information
            result: Tool execution result
            context: Tool execution context
        """
        event = ToolResultEvent(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            user_groups=user.group_memberships,
            conversation_id=context.conversation_id,
            request_id=context.request_id,
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            success=result.success,
            error=result.error,
            execution_time_ms=result.metadata.get("execution_time_ms", 0.0),
            result_size_bytes=(
                len(result.result_for_llm.encode("utf-8"))
                if result.result_for_llm
                else 0
            ),
            ui_component_type=(
                result.ui_component.__class__.__name__
                if result.ui_component
                else None
            ),
        )
        await self.log_event(event)

    async def log_ui_feature_access(
        self,
        user: "User",
        feature_name: str,
        access_granted: bool,
        required_groups: List[str],
        conversation_id: str,
        request_id: str,
    ) -> None:
        """Convenience method for logging UI feature access checks.

        Args:
            user: User attempting to access the feature
            feature_name: Name of the UI feature
            access_granted: Whether access was granted
            required_groups: Groups required to access the feature
            conversation_id: Conversation identifier
            request_id: Request identifier
        """
        event = UiFeatureAccessCheckEvent(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            user_groups=user.group_memberships,
            conversation_id=conversation_id,
            request_id=request_id,
            feature_name=feature_name,
            access_granted=access_granted,
            required_groups=required_groups,
        )
        await self.log_event(event)

    async def log_ai_response(
        self,
        user: "User",
        conversation_id: str,
        request_id: str,
        response_text: str,
        tool_calls: List["ToolCall"],
        model_info: Optional[Dict[str, Any]] = None,
        include_full_text: bool = False,
    ) -> None:
        """Convenience method for logging AI responses.

        Args:
            user: User receiving the response
            conversation_id: Conversation identifier
            request_id: Request identifier
            response_text: The AI-generated response text
            tool_calls: List of tool calls in the response
            model_info: Optional model configuration info
            include_full_text: Whether to include full response text
        """
        response_hash = hashlib.sha256(response_text.encode("utf-8")).hexdigest()

        event = AiResponseEvent(
            user_id=user.id,
            username=user.username,
            user_email=user.email,
            user_groups=user.group_memberships,
            conversation_id=conversation_id,
            request_id=request_id,
            response_length_chars=len(response_text),
            response_text=response_text if include_full_text else None,
            response_hash=response_hash,
            model_name=model_info.get("model") if model_info else None,
            temperature=model_info.get("temperature") if model_info else None,
            tool_calls_count=len(tool_calls),
            tool_names=[tc.name for tc in tool_calls],
        )
        await self.log_event(event)

    async def query_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events (optional, for implementations that support it).

        Args:
            filters: Filter criteria (user_id, event_type, etc.)
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching audit events

        Raises:
            NotImplementedError: If query not supported by implementation
        """
        raise NotImplementedError("Query not supported by this implementation")

    def _sanitize_parameters(
        self, parameters: Dict[str, Any]
    ) -> tuple[Dict[str, Any], bool]:
        """Sanitize sensitive data from parameters.

        Args:
            parameters: Raw parameters dict

        Returns:
            Tuple of (sanitized_parameters, was_sanitized)
        """
        sanitized = parameters.copy()
        was_sanitized = False

        # Common sensitive field patterns
        sensitive_patterns = [
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "credential",
            "auth",
            "private_key",
            "access_key",
        ]

        for key in list(sanitized.keys()):
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in sensitive_patterns):
                sanitized[key] = "[REDACTED]"
                was_sanitized = True

        return sanitized, was_sanitized
