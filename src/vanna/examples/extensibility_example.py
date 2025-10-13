"""
Comprehensive example demonstrating all extensibility interfaces.

This example shows how to use:
- LlmMiddleware for caching
- ErrorRecoveryStrategy for retry logic
- ContextEnricher for adding user preferences
- ConversationFilter for context window management
- ObservabilityProvider for monitoring
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from vanna.core import (
    Agent,
    LlmMiddleware,
    ErrorRecoveryStrategy,
    ContextEnricher,
    ConversationFilter,
    ObservabilityProvider,
    User,
    ToolContext,
    Conversation,
    Message,
    LlmRequest,
    LlmResponse,
    Span,
    Metric,
)
from vanna.core.recovery import RecoveryAction, RecoveryActionType
from vanna.core.registry import ToolRegistry


# 1. LlmMiddleware Example: Simple Caching
class CachingMiddleware(LlmMiddleware):
    """Cache LLM responses to reduce costs and latency."""

    def __init__(self) -> None:
        self.cache: Dict[str, LlmResponse] = {}
        self.hits = 0
        self.misses = 0

    def _compute_cache_key(self, request: LlmRequest) -> str:
        """Create cache key from request."""
        messages_str = str([(m.role, m.content) for m in request.messages])
        return f"{messages_str}:{request.temperature}"

    async def before_llm_request(self, request: LlmRequest) -> LlmRequest:
        """Check cache before sending request."""
        cache_key = self._compute_cache_key(request)
        if cache_key in self.cache:
            self.hits += 1
            print(f"[CACHE HIT] Cache stats: {self.hits} hits, {self.misses} misses")
        return request

    async def after_llm_response(
        self, request: LlmRequest, response: LlmResponse
    ) -> LlmResponse:
        """Cache the response."""
        cache_key = self._compute_cache_key(request)
        if cache_key not in self.cache:
            self.cache[cache_key] = response
            self.misses += 1
            print(f"[CACHE MISS] Caching response")
        return response


# 2. ErrorRecoveryStrategy Example: Exponential Backoff
class ExponentialBackoffStrategy(ErrorRecoveryStrategy):
    """Retry failed operations with exponential backoff."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    async def handle_tool_error(
        self, error: Exception, context: ToolContext, attempt: int = 1
    ) -> RecoveryAction:
        """Retry tool errors with exponential backoff."""
        if attempt < self.max_retries:
            delay_ms = (2 ** (attempt - 1)) * 1000
            print(f"[RETRY] Tool failed, retrying in {delay_ms}ms (attempt {attempt}/{self.max_retries})")
            return RecoveryAction(
                action=RecoveryActionType.RETRY,
                retry_delay_ms=delay_ms,
                message=f"Retrying after {delay_ms}ms"
            )

        print(f"[FAIL] Max retries exceeded for tool error: {error}")
        return RecoveryAction(
            action=RecoveryActionType.FAIL,
            message=f"Tool error after {self.max_retries} attempts: {str(error)}"
        )

    async def handle_llm_error(
        self, error: Exception, request: LlmRequest, attempt: int = 1
    ) -> RecoveryAction:
        """Retry LLM errors with backoff."""
        if attempt < self.max_retries:
            delay_ms = (2 ** (attempt - 1)) * 1000
            print(f"[RETRY] LLM failed, retrying in {delay_ms}ms (attempt {attempt}/{self.max_retries})")
            return RecoveryAction(
                action=RecoveryActionType.RETRY,
                retry_delay_ms=delay_ms,
                message=f"Retrying LLM after {delay_ms}ms"
            )

        print(f"[FAIL] Max retries exceeded for LLM error: {error}")
        return RecoveryAction(
            action=RecoveryActionType.FAIL,
            message=f"LLM error after {self.max_retries} attempts: {str(error)}"
        )


# 3. ContextEnricher Example: Add User Preferences
class UserPreferencesEnricher(ContextEnricher):
    """Enrich context with user preferences."""

    def __init__(self) -> None:
        # Mock user preferences database
        self.preferences: Dict[str, Dict[str, Any]] = {
            "user123": {
                "timezone": "America/New_York",
                "language": "en",
                "theme": "dark"
            }
        }

    async def enrich_context(self, context: ToolContext) -> ToolContext:
        """Add user preferences to context."""
        prefs = self.preferences.get(context.user.id, {})
        context.metadata["user_preferences"] = prefs
        context.metadata["timezone"] = prefs.get("timezone", "UTC")
        print(f"[ENRICH] Added preferences for user {context.user.id}: {prefs}")
        return context


# 4. ConversationFilter Example: Context Window Management
class ContextWindowFilter(ConversationFilter):
    """Limit conversation to fit within context window."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages

    async def filter_messages(self, messages: List[Message]) -> List[Message]:
        """Keep only recent messages within limit."""
        if len(messages) <= self.max_messages:
            return messages

        # Keep system messages and recent messages
        system_messages = [m for m in messages if m.role == "system"]
        other_messages = [m for m in messages if m.role != "system"]

        # Take the most recent messages
        recent_messages = other_messages[-self.max_messages:]
        filtered = system_messages + recent_messages

        print(f"[FILTER] Reduced {len(messages)} messages to {len(filtered)}")
        return filtered


# 5. ObservabilityProvider Example: Simple Logging
class LoggingObservabilityProvider(ObservabilityProvider):
    """Log metrics and spans for monitoring."""

    def __init__(self) -> None:
        self.metrics: List[Metric] = []
        self.spans: List[Span] = []

    async def record_metric(
        self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record and log a metric."""
        metric = Metric(name=name, value=value, unit=unit, tags=tags or {})
        self.metrics.append(metric)
        tags_str = ", ".join(f"{k}={v}" for k, v in (tags or {}).items())
        print(f"[METRIC] {name}: {value}{unit} {tags_str}")

    async def create_span(
        self, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Create a span for tracing."""
        span = Span(name=name, attributes=attributes or {})
        print(f"[SPAN START] {name}")
        return span

    async def end_span(self, span: Span) -> None:
        """End and record a span."""
        span.end()
        self.spans.append(span)
        duration = span.duration_ms() or 0
        print(f"[SPAN END] {span.name}: {duration:.2f}ms")


async def run_example() -> None:
    """
    Example showing all extensibility interfaces working together.
    """
    from vanna.integrations.anthropic import AnthropicLlmService

    # Create all extensibility components
    caching_middleware = CachingMiddleware()
    retry_strategy = ExponentialBackoffStrategy(max_retries=3)
    preferences_enricher = UserPreferencesEnricher()
    context_filter = ContextWindowFilter(max_messages=20)
    observability = LoggingObservabilityProvider()

    # Mock conversation store
    class MockStore:
        async def get_conversation(
            self, cid: str, uid: str
        ) -> Optional[Conversation]:
            return None

        async def create_conversation(self, cid: str, uid: str, title: str) -> Conversation:
            return Conversation(id=cid, user_id=uid, messages=[Message(role="user", content=title)])

        async def update_conversation(self, conv: Conversation) -> None:
            pass

        async def delete_conversation(self, cid: str, uid: str) -> bool:
            return False

        async def list_conversations(self, uid: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
            return []

    # Create agent with all extensibility components
    agent = Agent(
        llm_service=AnthropicLlmService(api_key="test-key"),
        tool_registry=ToolRegistry(),
        conversation_store=MockStore(),  # type: ignore
        llm_middlewares=[caching_middleware],
        error_recovery_strategy=retry_strategy,
        context_enrichers=[preferences_enricher],
        conversation_filters=[context_filter],
        observability_provider=observability,
    )

    print("✓ Agent created with all extensibility components:")
    print(f"  - LLM Middleware: {len(agent.llm_middlewares)} middlewares")
    print(f"  - Error Recovery: {type(agent.error_recovery_strategy).__name__}")
    print(f"  - Context Enrichers: {len(agent.context_enrichers)} enrichers")
    print(f"  - Conversation Filters: {len(agent.conversation_filters)} filters")
    print(f"  - Observability: {type(agent.observability_provider).__name__}")
    print("\n🎉 All extensibility interfaces integrated successfully!")


if __name__ == "__main__":
    asyncio.run(run_example())
