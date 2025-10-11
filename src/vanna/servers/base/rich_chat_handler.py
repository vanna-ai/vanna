# """
# Rich component-aware chat handling logic.
# """

# import uuid
# from typing import AsyncGenerator, Callable, List, Optional, Union

# from ...core import Agent, User
# from ...core.rich_components import RichComponent
# from ...core.component_manager import ComponentManager, ComponentUpdate
# from .models import ChatRequest, ChatResponse, ChatStreamChunk


# class RichChatHandler:
#     """Rich component-aware chat handling logic."""

#     def __init__(
#         self,
#         agent: Agent,
#         default_user_factory: Optional[Callable[[Optional[str]], User]] = None,
#     ):
#         """Initialize rich chat handler.

#         Args:
#             agent: The agent to handle chat requests
#             default_user_factory: Function to create default user from user_id
#         """
#         self.agent = agent
#         self.default_user_factory = default_user_factory or self._create_default_user
#         self.component_managers: dict[str, ComponentManager] = {}  # Per conversation

#     async def handle_stream(
#         self, request: ChatRequest
#     ) -> AsyncGenerator[ChatStreamChunk, None]:
#         """Stream chat responses with rich component support.

#         Args:
#             request: Chat request

#         Yields:
#             Chat stream chunks including rich component updates
#         """
#         user = self._resolve_user(request.user_id)
#         conversation_id = request.conversation_id or self._generate_conversation_id()
#         request_id = request.request_id or str(uuid.uuid4())

#         # Get or create component manager for this conversation
#         if conversation_id not in self.component_managers:
#             self.component_managers[conversation_id] = ComponentManager()

#         component_manager = self.component_managers[conversation_id]

#         async for component in self.agent.send_message(
#             conversation_id=conversation_id,
#             user=user,
#             message=request.message,
#             request_id=request_id,
#         ):
#             if isinstance(component, RichComponent):
#                 # Handle rich component through manager
#                 update = component_manager.emit(component)
#                 yield ChatStreamChunk.from_component_update(update, conversation_id, request_id)
#             else:
#                 # Handle legacy components
#                 yield ChatStreamChunk.from_component(component, conversation_id, request_id)

#     async def handle_poll(self, request: ChatRequest) -> ChatResponse:
#         """Handle polling request with rich component support.

#         Args:
#             request: Chat request

#         Returns:
#             Complete chat response with all components
#         """
#         chunks: List[ChatStreamChunk] = []

#         async for chunk in self.handle_stream(request):
#             chunks.append(chunk)

#         return ChatResponse.from_chunks(chunks)

#     def get_component_manager(self, conversation_id: str) -> Optional[ComponentManager]:
#         """Get the component manager for a conversation."""
#         return self.component_managers.get(conversation_id)

#     def get_component(self, conversation_id: str, component_id: str) -> Optional[RichComponent]:
#         """Get a specific component from a conversation."""
#         manager = self.get_component_manager(conversation_id)
#         return manager.get_component(component_id) if manager else None

#     def get_all_components(self, conversation_id: str) -> List[RichComponent]:
#         """Get all components in a conversation."""
#         manager = self.get_component_manager(conversation_id)
#         return manager.get_all_components() if manager else []

#     def update_component(
#         self,
#         conversation_id: str,
#         component_id: str,
#         **updates
#     ) -> Optional[ComponentUpdate]:
#         """Update a component in a conversation."""
#         manager = self.get_component_manager(conversation_id)
#         return manager.update_component(component_id, **updates) if manager else None

#     def remove_component(
#         self,
#         conversation_id: str,
#         component_id: str
#     ) -> Optional[ComponentUpdate]:
#         """Remove a component from a conversation."""
#         manager = self.get_component_manager(conversation_id)
#         return manager.remove_component(component_id) if manager else None

#     def clear_conversation_components(self, conversation_id: str):
#         """Clear all components for a conversation."""
#         if conversation_id in self.component_managers:
#             del self.component_managers[conversation_id]

#     def _resolve_user(self, user_id: Optional[str]) -> User:
#         """Resolve user from ID or create default."""
#         if user_id:
#             # In a real implementation, you'd fetch from a user store
#             return User(id=user_id, username=f"user_{user_id}", email="", permissions=[])

#         return self.default_user_factory(user_id)

#     def _create_default_user(self, user_id: Optional[str]) -> User:
#         """Create a default user."""
#         user_id = user_id or "anonymous"
#         return User(
#             id=user_id,
#             username=f"user_{user_id}",
#             email="",
#             permissions=[]
#         )

#     def _generate_conversation_id(self) -> str:
#         """Generate a new conversation ID."""
#         return str(uuid.uuid4())