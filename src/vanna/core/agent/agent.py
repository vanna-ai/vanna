"""
Agent implementation for the Vanna Agents framework.

This module provides the main Agent class that orchestrates the interaction
between LLM services, tools, and conversation storage.
"""

import uuid
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional

from vanna.components import (
    UiComponent,
    SimpleTextComponent,
    ToolExecutionComponent,  # Legacy - will be removed
    RichTextComponent,
    StatusBarUpdateComponent,
    TaskTrackerUpdateComponent,
    ChatInputUpdateComponent,
    StatusCardComponent,
    Task,
)
from .config import AgentConfig
from vanna.core.storage import ConversationStore
from vanna.core.llm import LlmService
from vanna.core.system_prompt import SystemPromptBuilder
from vanna.core.storage import Conversation, Message
from vanna.core.llm import LlmMessage, LlmRequest, LlmResponse
from vanna.core.tool import ToolCall, ToolContext, ToolResult, ToolSchema
from vanna.core.user import User
from vanna.core.registry import ToolRegistry
from vanna.core.system_prompt import DefaultSystemPromptBuilder
from vanna.core.lifecycle import LifecycleHook
from vanna.core.middleware import LlmMiddleware
from vanna.core.recovery import ErrorRecoveryStrategy, RecoveryActionType
from vanna.core.enricher import ContextEnricher
from vanna.core.filter import ConversationFilter
from vanna.core.observability import ObservabilityProvider
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext

if TYPE_CHECKING:
    pass


class Agent:
    """Main agent implementation.

    The Agent class orchestrates LLM interactions, tool execution, and conversation
    management. It provides 6 extensibility points for customization:

    - lifecycle_hooks: Hook into message and tool execution lifecycle
    - llm_middlewares: Intercept and transform LLM requests/responses
    - error_recovery_strategy: Handle errors with retry logic
    - context_enrichers: Add data to tool execution context
    - conversation_filters: Filter conversation history before LLM calls
    - observability_provider: Collect telemetry and monitoring data

    Example:
        agent = Agent(
            llm_service=AnthropicLlmService(api_key="..."),
            tool_registry=registry,
            conversation_store=store,
            lifecycle_hooks=[QuotaCheckHook()],
            llm_middlewares=[CachingMiddleware()],
            observability_provider=LoggingProvider()
        )
    """

    def __init__(
        self,
        llm_service: LlmService,
        tool_registry: ToolRegistry,
        user_resolver: UserResolver,
        conversation_store: Optional[ConversationStore] = None,
        config: AgentConfig = AgentConfig(),
        system_prompt_builder: SystemPromptBuilder = DefaultSystemPromptBuilder(),
        lifecycle_hooks: List[LifecycleHook] = [],
        llm_middlewares: List[LlmMiddleware] = [],
        error_recovery_strategy: Optional[ErrorRecoveryStrategy] = None,
        context_enrichers: List[ContextEnricher] = [],
        conversation_filters: List[ConversationFilter] = [],
        observability_provider: Optional[ObservabilityProvider] = None,
    ):
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.user_resolver = user_resolver

        # Import here to avoid circular dependency
        if conversation_store is None:
            from vanna.integrations.local import MemoryConversationStore
            conversation_store = MemoryConversationStore()

        self.conversation_store = conversation_store
        self.config = config
        self.system_prompt_builder = system_prompt_builder
        self.lifecycle_hooks = lifecycle_hooks
        self.llm_middlewares = llm_middlewares
        self.error_recovery_strategy = error_recovery_strategy
        self.context_enrichers = context_enrichers
        self.conversation_filters = conversation_filters
        self.observability_provider = observability_provider

    async def send_message(
        self,
        request_context: RequestContext,
        message: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[UiComponent, None]:
        """
        Process a user message and yield UI components.

        Args:
            request_context: Request context for user resolution
            message: User's message content
            conversation_id: Optional conversation ID; if None, creates new conversation

        Yields:
            UiComponent instances for UI updates
        """
        # Resolve user from request context
        user = await self.user_resolver.resolve_user(request_context)

        # Create observability span for entire message processing
        message_span = None
        if self.observability_provider:
            message_span = await self.observability_provider.create_span(
                "agent.send_message",
                attributes={"user_id": user.id, "conversation_id": conversation_id or "new"}
            )

        # Run before_message hooks
        modified_message = message
        for hook in self.lifecycle_hooks:
            hook_result = await hook.before_message(user, modified_message)
            if hook_result is not None:
                modified_message = hook_result

        # Use the potentially modified message
        message = modified_message

        # Generate conversation ID and request ID if not provided
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        request_id = str(uuid.uuid4())

        # Update status to working
        yield UiComponent(  # type: ignore
            rich_component=StatusBarUpdateComponent(
                status="working",
                message="Processing your request...",
                detail="Analyzing query"
            )
        )

        # Load or create conversation
        conversation = await self.conversation_store.get_conversation(
            conversation_id, user
        )
        if not conversation:
            conversation = await self.conversation_store.create_conversation(
                conversation_id, user, message
            )
        else:
            # Add user message
            conversation.add_message(Message(role="user", content=message))

        # Add initial task
        context_task = Task(
            title="Load conversation context",
            description="Reading message history and user context",
            status="pending"
        )
        yield UiComponent(  # type: ignore
            rich_component=TaskTrackerUpdateComponent.add_task(context_task)
        )

        # Create context
        context = ToolContext(
            user=user, conversation_id=conversation_id, request_id=request_id
        )

        # Enrich context with additional data
        for enricher in self.context_enrichers:
            context = await enricher.enrich_context(context)

        # Get available tools for user
        tool_schemas = self.tool_registry.get_schemas(user)

        # Update task status to completed
        yield UiComponent(  # type: ignore
            rich_component=TaskTrackerUpdateComponent.update_task(
                context_task.id,
                status="completed"
            )
        )

        # Build system prompt
        system_prompt = await self.system_prompt_builder.build_system_prompt(
            user, tool_schemas
        )

        # Build LLM request
        request = await self._build_llm_request(conversation, tool_schemas, user, system_prompt)

        # Process with tool loop
        tool_iterations = 0

        while tool_iterations < self.config.max_tool_iterations:
            if self.config.include_thinking_indicators and tool_iterations == 0:
                # TODO: Yield thinking indicator
                pass

            # Get LLM response
            if self.config.stream_responses:
                response = await self._handle_streaming_response(request)
            else:
                response = await self._send_llm_request(request)

            # Handle tool calls
            if response.is_tool_call():
                tool_iterations += 1

                # First, add the assistant message with tool_calls to the conversation
                # This is required for OpenAI API - tool messages must follow assistant messages with tool_calls
                assistant_message = Message(
                    role="assistant",
                    content=response.content or "",  # Ensure content is not None
                    tool_calls=response.tool_calls,
                )
                conversation.add_message(assistant_message)

                if response.content is not None:
                    # Yield any partial content from the assistant before tool execution
                    yield UiComponent(
                        rich_component=RichTextComponent(content=response.content, markdown=True),
                        simple_component=SimpleTextComponent(text=response.content)
                    )

                # Update status to executing tools
                yield UiComponent(  # type: ignore
                    rich_component=StatusBarUpdateComponent(
                        status="working",
                        message="Executing tools...",
                        detail=f"Running {len(response.tool_calls or [])} tools"
                    )
                )

                # Collect all tool results first
                tool_results = []
                for i, tool_call in enumerate(response.tool_calls or []):
                    # Add task for this tool execution
                    tool_task = Task(
                        title=f"Execute {tool_call.name}",
                        description=f"Running tool with provided arguments",
                        status="in_progress"
                    )
                    yield UiComponent(  # type: ignore
                        rich_component=TaskTrackerUpdateComponent.add_task(tool_task)
                    )

                    response_str = response.content

                    # Use primitive StatusCard instead of semantic ToolExecutionComponent
                    tool_status_card = StatusCardComponent(
                        title=f"Executing {tool_call.name}",
                        status="running",
                        description=f"Running tool with {len(tool_call.arguments)} arguments",
                        icon="⚙️",
                        metadata=tool_call.arguments
                    )
                    yield UiComponent(
                        rich_component=tool_status_card,
                        simple_component=SimpleTextComponent(text=response_str or "")
                    )

                    # Run before_tool hooks
                    tool = self.tool_registry.get_tool(tool_call.name)
                    if tool:
                        for hook in self.lifecycle_hooks:
                            await hook.before_tool(tool, context)

                    # Execute tool
                    result = await self.tool_registry.execute(tool_call, context)

                    # Run after_tool hooks
                    for hook in self.lifecycle_hooks:
                        modified_result = await hook.after_tool(result)
                        if modified_result is not None:
                            result = modified_result

                    # Update status card to show completion
                    final_status = "success" if result.success else "error"
                    final_description = (
                        f"Tool completed successfully"
                        if result.success
                        else f"Tool failed: {result.error or 'Unknown error'}"
                    )

                    yield UiComponent(  # type: ignore
                        rich_component=tool_status_card.set_status(final_status, final_description)
                    )

                    # Update tool task to completed
                    yield UiComponent(  # type: ignore
                        rich_component=TaskTrackerUpdateComponent.update_task(
                            tool_task.id,
                            status="completed" if result.success else "failed",
                            detail=f"Tool {'completed successfully' if result.success else 'failed'}"
                        )
                    )

                    # Yield tool result
                    if result.ui_component:
                        yield result.ui_component

                    # Collect tool result data
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "content": (
                            result.result_for_llm
                            if result.success
                            else result.error or "Tool execution failed"
                        )
                    })

                # Add tool responses to conversation
                # For APIs that need all tool results in one message, this helps
                for tool_result in tool_results:
                    tool_response_message = Message(
                        role="tool",
                        content=tool_result["content"],
                        tool_call_id=tool_result["tool_call_id"],
                    )
                    conversation.add_message(tool_response_message)

                # Rebuild request with tool responses
                request = await self._build_llm_request(conversation, tool_schemas, user, system_prompt)
            else:
                # Update status to idle and set completion message
                yield UiComponent(  # type: ignore
                    rich_component=StatusBarUpdateComponent(
                        status="idle",
                        message="Response complete",
                        detail="Ready for next message"
                    )
                )

                # Update chat input placeholder
                yield UiComponent(  # type: ignore
                    rich_component=ChatInputUpdateComponent(
                        placeholder="Ask a follow-up question...",
                        disabled=False
                    )
                )

                # Yield final text response
                if response.content:
                    # Add assistant response to conversation
                    conversation.add_message(
                        Message(role="assistant", content=response.content)
                    )
                    yield UiComponent(
                        rich_component=RichTextComponent(content=response.content, markdown=True),
                        simple_component=SimpleTextComponent(text=response.content)
                    )
                break

        # Save conversation if configured
        if self.config.auto_save_conversations:
            await self.conversation_store.update_conversation(conversation)

        # Run after_message hooks
        for hook in self.lifecycle_hooks:
            await hook.after_message(conversation)

        # End observability span and record metrics
        if self.observability_provider and message_span:
            message_span.set_attribute("tool_iterations", tool_iterations)
            await self.observability_provider.end_span(message_span)
            if message_span.duration_ms():
                await self.observability_provider.record_metric(
                    "agent.message.duration", message_span.duration_ms() or 0, "ms",
                    tags={"user_id": user.id}
                )

    async def get_available_tools(self, user: User) -> List[ToolSchema]:
        """Get tools available to the user."""
        return self.tool_registry.get_schemas(user)

    async def _build_llm_request(
        self, conversation: Conversation, tool_schemas: List[ToolSchema], user: User, system_prompt: Optional[str] = None
    ) -> LlmRequest:
        """Build LLM request from conversation and tools."""
        # Apply conversation filters
        filtered_messages = conversation.messages
        for filter in self.conversation_filters:
            filtered_messages = await filter.filter_messages(filtered_messages)

        messages = []
        for msg in filtered_messages:
            llm_msg = LlmMessage(
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls,
                tool_call_id=msg.tool_call_id,
            )
            messages.append(llm_msg)

        return LlmRequest(
            messages=messages,
            tools=tool_schemas if tool_schemas else None,
            user=user,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=self.config.stream_responses,
            system_prompt=system_prompt,
        )

    async def _send_llm_request(self, request: LlmRequest) -> LlmResponse:
        """Send LLM request with middleware and observability."""
        # Apply before_llm_request middlewares
        for middleware in self.llm_middlewares:
            request = await middleware.before_llm_request(request)

        # Create observability span for LLM call
        llm_span = None
        if self.observability_provider:
            llm_span = await self.observability_provider.create_span(
                "llm.request",
                attributes={
                    "model": getattr(self.llm_service, "model", "unknown"),
                    "stream": request.stream
                }
            )

        # Send request
        response = await self.llm_service.send_request(request)

        # End span and record metrics
        if self.observability_provider and llm_span:
            await self.observability_provider.end_span(llm_span)
            if llm_span.duration_ms():
                await self.observability_provider.record_metric(
                    "llm.request.duration", llm_span.duration_ms() or 0, "ms"
                )

        # Apply after_llm_response middlewares
        for middleware in self.llm_middlewares:
            response = await middleware.after_llm_response(request, response)

        return response

    async def _handle_streaming_response(self, request: LlmRequest) -> LlmResponse:
        """Handle streaming response from LLM."""
        # Apply before_llm_request middlewares
        for middleware in self.llm_middlewares:
            request = await middleware.before_llm_request(request)

        accumulated_content = ""
        accumulated_tool_calls = []

        async for chunk in self.llm_service.stream_request(request):
            if chunk.content:
                accumulated_content += chunk.content
                # Could yield intermediate TextChunk here

            if chunk.tool_calls:
                accumulated_tool_calls.extend(chunk.tool_calls)

        response = LlmResponse(
            content=accumulated_content if accumulated_content else None,
            tool_calls=accumulated_tool_calls if accumulated_tool_calls else None,
        )

        # Apply after_llm_response middlewares
        for middleware in self.llm_middlewares:
            response = await middleware.after_llm_response(request, response)

        return response
