"""
Tests for the default workflow handler, including memory display and deletion.
"""

import pytest
import uuid
from datetime import datetime
from vanna.core.workflow.default import DefaultWorkflowHandler
from vanna.core.user import User
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext
from vanna.core.storage import Conversation
from vanna.core.tool import ToolContext
from vanna.capabilities.agent_memory import ToolMemory, TextMemory
from vanna.integrations.local.agent_memory import DemoAgentMemory


class SimpleUserResolver(UserResolver):
    """Simple user resolver for tests."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="test_user", email="test@example.com", group_memberships=["user"]
        )


class MockAgent:
    """Mock agent for testing workflow handlers."""

    def __init__(self, agent_memory=None, tool_registry=None):
        self.agent_memory = agent_memory
        self.tool_registry = tool_registry or MockToolRegistry()


class MockToolRegistry:
    """Mock tool registry for testing."""

    async def get_schemas(self, user):
        """Return mock tool schemas."""
        return []


class MockConversation:
    """Mock conversation for testing."""

    def __init__(self, conversation_id=None):
        self.id = conversation_id or str(uuid.uuid4())


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(id="test_user", email="test@example.com", group_memberships=["user"])


@pytest.fixture
def test_conversation():
    """Create a test conversation."""
    return MockConversation()


@pytest.fixture
def workflow_handler():
    """Create a workflow handler instance."""
    return DefaultWorkflowHandler()


@pytest.fixture
def agent_with_memory():
    """Create a mock agent with memory."""
    memory = DemoAgentMemory(max_items=100)
    return MockAgent(agent_memory=memory)


@pytest.fixture
def agent_without_memory():
    """Create a mock agent without memory."""
    return MockAgent(agent_memory=None)


class TestWorkflowCommands:
    """Test basic workflow command handling."""

    @pytest.mark.asyncio
    async def test_help_command(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that /help command returns help message."""
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, "/help"
        )

        assert result.should_skip_llm is True
        assert len(result.components) > 0

        # Check that help content includes all commands
        help_component = result.components[0]
        content = help_component.rich_component.content
        assert "/help" in content
        assert "/status" in content
        assert "/memories" in content
        assert "/delete [id]" in content

    @pytest.mark.asyncio
    async def test_status_command(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that /status command returns status information."""
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, "/status"
        )

        assert result.should_skip_llm is True
        assert len(result.components) > 0

    @pytest.mark.asyncio
    async def test_memories_command(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that /memories command returns memory list."""
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, "/memories"
        )

        assert result.should_skip_llm is True
        assert len(result.components) > 0

    @pytest.mark.asyncio
    async def test_unknown_command(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that unknown commands are passed to LLM."""
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, "What is the weather?"
        )

        assert result.should_skip_llm is False


class TestMemoriesView:
    """Test the memories view functionality."""

    @pytest.mark.asyncio
    async def test_memories_no_agent_memory(self, workflow_handler, agent_without_memory, test_user, test_conversation):
        """Test memories view when agent has no memory capability."""
        result = await workflow_handler._get_recent_memories(
            agent_without_memory, test_user, test_conversation
        )

        assert result.should_skip_llm is True
        assert len(result.components) == 1

        content = result.components[0].rich_component.content
        assert "No Memory System" in content

    @pytest.mark.asyncio
    async def test_memories_empty(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test memories view when no memories exist."""
        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        assert result.should_skip_llm is True
        assert len(result.components) == 1

        content = result.components[0].rich_component.content
        assert "No recent memories found" in content

    @pytest.mark.asyncio
    async def test_memories_with_tool_memories(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test memories view displays tool memories correctly."""
        # Create a context and add some tool memories
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        # Add tool memories
        await agent_with_memory.agent_memory.save_tool_usage(
            question="What is the total sales?",
            tool_name="run_sql",
            args={"query": "SELECT SUM(total) FROM invoices"},
            context=context,
            success=True,
        )

        await agent_with_memory.agent_memory.save_tool_usage(
            question="Show me customer names",
            tool_name="run_sql",
            args={"query": "SELECT name FROM customers"},
            context=context,
            success=True,
        )

        # Get memories view
        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        assert result.should_skip_llm is True
        assert len(result.components) > 1  # Header + at least one memory card

        # Check header
        header = result.components[0].rich_component.content
        assert "Recent Memories" in header
        assert "2" in header  # Should show count

        # Check that we have tool memory section
        found_tool_section = False
        for component in result.components:
            if hasattr(component.rich_component, 'content'):
                if "Tool Memories" in component.rich_component.content:
                    found_tool_section = True
                    break

        assert found_tool_section

    @pytest.mark.asyncio
    async def test_memories_with_text_memories(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test memories view displays text memories correctly."""
        # Create a context and add some text memories
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        # Add text memories
        await agent_with_memory.agent_memory.save_text_memory(
            content="Remember to always check the data quality",
            context=context,
        )

        await agent_with_memory.agent_memory.save_text_memory(
            content="The fiscal year starts in April",
            context=context,
        )

        # Get memories view
        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        assert result.should_skip_llm is True
        assert len(result.components) > 1  # Header + at least one memory card

        # Check that we have text memory section
        found_text_section = False
        for component in result.components:
            if hasattr(component.rich_component, 'content'):
                if "Text Memories" in component.rich_component.content:
                    found_text_section = True
                    break

        assert found_text_section

    @pytest.mark.asyncio
    async def test_memories_with_both_types(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test memories view displays both tool and text memories."""
        # Create a context
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        # Add tool memory
        await agent_with_memory.agent_memory.save_tool_usage(
            question="What is the total sales?",
            tool_name="run_sql",
            args={"query": "SELECT SUM(total) FROM invoices"},
            context=context,
            success=True,
        )

        # Add text memory
        await agent_with_memory.agent_memory.save_text_memory(
            content="Important note about the data",
            context=context,
        )

        # Get memories view
        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        assert result.should_skip_llm is True

        # Should have header + text section + text cards + tool section + tool cards
        assert len(result.components) >= 4

        # Check both sections exist
        content_str = str([c.rich_component.content if hasattr(c.rich_component, 'content') else str(c.rich_component) for c in result.components])
        assert "Text Memories" in content_str
        assert "Tool Memories" in content_str

    @pytest.mark.asyncio
    async def test_memories_have_delete_buttons(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that memory cards include delete buttons."""
        # Create a context and add a memory
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        await agent_with_memory.agent_memory.save_tool_usage(
            question="Test question",
            tool_name="test_tool",
            args={"param": "value"},
            context=context,
            success=True,
        )

        # Get memories view
        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        # Find a card component with actions
        found_delete_button = False
        for component in result.components:
            if hasattr(component.rich_component, 'actions') and component.rich_component.actions:
                for action in component.rich_component.actions:
                    if '/delete' in action.get('action', ''):
                        found_delete_button = True
                        break

        assert found_delete_button, "Should have delete button in memory cards"


class TestMemoryDeletion:
    """Test memory deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_no_agent_memory(self, workflow_handler, agent_without_memory, test_user, test_conversation):
        """Test delete command when agent has no memory capability."""
        result = await workflow_handler._delete_memory(
            agent_without_memory, test_user, test_conversation, "test-id"
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "No Memory System" in content

    @pytest.mark.asyncio
    async def test_delete_no_id_provided(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test delete command without memory ID."""
        result = await workflow_handler._delete_memory(
            agent_with_memory, test_user, test_conversation, ""
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "Invalid Command" in content
        assert "memory_id" in content

    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test deleting a memory that doesn't exist."""
        result = await workflow_handler._delete_memory(
            agent_with_memory, test_user, test_conversation, "nonexistent-id"
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "Memory Not Found" in content

    @pytest.mark.asyncio
    async def test_delete_tool_memory_success(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test successfully deleting a tool memory."""
        # Create a context and add a memory
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        await agent_with_memory.agent_memory.save_tool_usage(
            question="Test question",
            tool_name="test_tool",
            args={"param": "value"},
            context=context,
            success=True,
        )

        # Get the memory ID
        memories = await agent_with_memory.agent_memory.get_recent_memories(context, limit=1)
        assert len(memories) == 1
        memory_id = memories[0].memory_id

        # Delete the memory
        result = await workflow_handler._delete_memory(
            agent_with_memory, test_user, test_conversation, memory_id
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "Memory Deleted" in content
        assert memory_id in content

        # Verify memory is gone
        memories_after = await agent_with_memory.agent_memory.get_recent_memories(context, limit=10)
        assert len(memories_after) == 0

    @pytest.mark.asyncio
    async def test_delete_text_memory_success(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test successfully deleting a text memory."""
        # Create a context and add a text memory
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        text_memory = await agent_with_memory.agent_memory.save_text_memory(
            content="Test text memory",
            context=context,
        )

        memory_id = text_memory.memory_id

        # Delete the memory
        result = await workflow_handler._delete_memory(
            agent_with_memory, test_user, test_conversation, memory_id
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "Memory Deleted" in content

        # Verify memory is gone
        text_memories_after = await agent_with_memory.agent_memory.get_recent_text_memories(context, limit=10)
        assert len(text_memories_after) == 0

    @pytest.mark.asyncio
    async def test_delete_command_parsing(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that /delete command is properly parsed."""
        # Add a memory first
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        await agent_with_memory.agent_memory.save_tool_usage(
            question="Test",
            tool_name="test",
            args={},
            context=context,
            success=True,
        )

        memories = await agent_with_memory.agent_memory.get_recent_memories(context, limit=1)
        memory_id = memories[0].memory_id

        # Test command parsing
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, f"/delete {memory_id}"
        )

        assert result.should_skip_llm is True
        content = result.components[0].rich_component.content
        assert "Memory Deleted" in content or "Memory Not Found" in content


class TestWorkflowComponentStructure:
    """Test the structure of components returned by workflow."""

    @pytest.mark.asyncio
    async def test_help_has_rich_component(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that help command returns properly structured components."""
        result = await workflow_handler.try_handle(
            agent_with_memory, test_user, test_conversation, "/help"
        )

        assert len(result.components) > 0
        for component in result.components:
            assert hasattr(component, 'rich_component')
            assert hasattr(component, 'simple_component')

    @pytest.mark.asyncio
    async def test_memories_cards_have_proper_structure(self, workflow_handler, agent_with_memory, test_user, test_conversation):
        """Test that memory cards have proper structure."""
        # Add a memory
        context = ToolContext(
            user=test_user,
            conversation_id=test_conversation.id,
            request_id=str(uuid.uuid4()),
            agent_memory=agent_with_memory.agent_memory,
        )

        await agent_with_memory.agent_memory.save_tool_usage(
            question="Test",
            tool_name="test_tool",
            args={"key": "value"},
            context=context,
            success=True,
        )

        result = await workflow_handler._get_recent_memories(
            agent_with_memory, test_user, test_conversation
        )

        # Find card components
        card_found = False
        for component in result.components:
            if hasattr(component.rich_component, 'type'):
                from vanna.core.rich_component import ComponentType
                if component.rich_component.type == ComponentType.CARD:
                    card_found = True
                    # Check card has required fields
                    assert hasattr(component.rich_component, 'title')
                    assert hasattr(component.rich_component, 'content')
                    assert hasattr(component.rich_component, 'actions')
                    assert len(component.rich_component.actions) > 0

        assert card_found, "Should have at least one card component"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
