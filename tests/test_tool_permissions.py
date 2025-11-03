"""
Tests for tool access control and permissions.
"""

import pytest
from pydantic import BaseModel, Field
from typing import Type

from vanna.core.tool import Tool, ToolContext, ToolResult, ToolCall
from vanna.core.user import User
from vanna.core.registry import ToolRegistry
from vanna.components import UiComponent, SimpleTextComponent


class SimpleToolArgs(BaseModel):
    """Simple args for testing."""
    message: str = Field(description="A message")


class MockTool(Tool[SimpleToolArgs]):
    """Mock tool for testing."""
    
    def __init__(self, tool_name: str = "mock_tool"):
        self._tool_name = tool_name
    
    @property
    def name(self) -> str:
        return self._tool_name
    
    @property
    def description(self) -> str:
        return f"A mock tool for testing: {self._tool_name}"
    
    def get_args_schema(self) -> Type[SimpleToolArgs]:
        return SimpleToolArgs
    
    async def execute(self, context: ToolContext, args: SimpleToolArgs) -> ToolResult:
        return ToolResult(
            success=True,
            result_for_llm=f"Mock tool executed: {args.message}"
        )


@pytest.fixture
def admin_user():
    """Admin user with admin group."""
    return User(
        id="admin_1",
        username="admin",
        email="admin@example.com",
        group_memberships=['admin', 'user']
    )


@pytest.fixture
def regular_user():
    """Regular user with user group."""
    return User(
        id="user_1",
        username="user",
        email="user@example.com",
        group_memberships=['user']
    )


@pytest.fixture
def analyst_user():
    """Analyst user with analyst group."""
    return User(
        id="analyst_1",
        username="analyst",
        email="analyst@example.com",
        group_memberships=['analyst', 'user']
    )


@pytest.fixture
def guest_user():
    """Guest user with no groups."""
    return User(
        id="guest_1",
        username="guest",
        email="guest@example.com",
        group_memberships=[]
    )


@pytest.mark.asyncio
async def test_tool_access_empty_groups_allows_all(regular_user):
    """Test that empty access_groups allows all users."""
    print("\n=== Empty Access Groups Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("public_tool")
    
    # Register with empty access groups
    registry.register_local_tool(tool, access_groups=[])
    
    # Create context
    context = ToolContext(
        user=regular_user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    # Execute tool
    tool_call = ToolCall(
        id="call_1",
        name="public_tool",
        arguments={"message": "hello"}
    )
    
    result = await registry.execute(tool_call, context)
    
    print(f"✓ Tool executed with empty access groups")
    print(f"  Success: {result.success}")
    
    assert result.success is True
    assert "Mock tool executed" in result.result_for_llm


@pytest.mark.asyncio
async def test_tool_access_granted_matching_group(admin_user):
    """Test that user with matching group can access tool."""
    print("\n=== Access Granted Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("admin_tool")
    
    # Register with admin-only access
    registry.register_local_tool(tool, access_groups=['admin'])
    
    context = ToolContext(
        user=admin_user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    tool_call = ToolCall(
        id="call_1",
        name="admin_tool",
        arguments={"message": "admin action"}
    )
    
    result = await registry.execute(tool_call, context)
    
    print(f"✓ Admin user accessed admin-only tool")
    print(f"  User groups: {admin_user.group_memberships}")
    print(f"  Tool access groups: ['admin']")
    print(f"  Success: {result.success}")
    
    assert result.success is True


@pytest.mark.asyncio
async def test_tool_access_denied_no_matching_group(regular_user):
    """Test that user without matching group cannot access tool."""
    print("\n=== Access Denied Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("admin_tool")
    
    # Register with admin-only access
    registry.register_local_tool(tool, access_groups=['admin'])
    
    context = ToolContext(
        user=regular_user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    tool_call = ToolCall(
        id="call_1",
        name="admin_tool",
        arguments={"message": "should fail"}
    )
    
    result = await registry.execute(tool_call, context)
    
    print(f"✓ Regular user denied access to admin-only tool")
    print(f"  User groups: {regular_user.group_memberships}")
    print(f"  Tool access groups: ['admin']")
    print(f"  Success: {result.success}")
    print(f"  Error: {result.error}")
    
    assert result.success is False
    assert "Insufficient group access" in result.result_for_llm
    assert "admin_tool" in result.result_for_llm


@pytest.mark.asyncio
async def test_tool_access_multiple_allowed_groups(analyst_user, admin_user, regular_user):
    """Test tool with multiple allowed groups."""
    print("\n=== Multiple Allowed Groups Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("data_tool")
    
    # Allow both admin and analyst groups
    registry.register_local_tool(tool, access_groups=['admin', 'analyst'])
    
    # Test analyst can access
    analyst_context = ToolContext(
        user=analyst_user,
        conversation_id="test_conv",
        request_id="test_req_1"
    )
    
    tool_call = ToolCall(id="call_1", name="data_tool", arguments={"message": "test"})
    result = await registry.execute(tool_call, analyst_context)
    
    print(f"✓ Analyst accessed tool")
    assert result.success is True
    
    # Test admin can access
    admin_context = ToolContext(
        user=admin_user,
        conversation_id="test_conv",
        request_id="test_req_2"
    )
    
    result = await registry.execute(tool_call, admin_context)
    
    print(f"✓ Admin accessed tool")
    assert result.success is True
    
    # Test regular user cannot access
    user_context = ToolContext(
        user=regular_user,
        conversation_id="test_conv",
        request_id="test_req_3"
    )
    
    result = await registry.execute(tool_call, user_context)
    
    print(f"✓ Regular user denied access")
    assert result.success is False


@pytest.mark.asyncio
async def test_tool_access_guest_user_denied(guest_user):
    """Test that guest user with no groups cannot access restricted tools."""
    print("\n=== Guest User Denied Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("restricted_tool")
    
    registry.register_local_tool(tool, access_groups=['user'])
    
    context = ToolContext(
        user=guest_user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    tool_call = ToolCall(id="call_1", name="restricted_tool", arguments={"message": "test"})
    result = await registry.execute(tool_call, context)
    
    print(f"✓ Guest user with no groups denied access")
    print(f"  User groups: {guest_user.group_memberships}")
    print(f"  Tool access groups: ['user']")
    
    assert result.success is False
    assert "Insufficient group access" in result.result_for_llm


@pytest.mark.asyncio
async def test_get_schemas_filters_by_user(admin_user, regular_user):
    """Test that get_schemas only returns tools accessible to user."""
    print("\n=== Schema Filtering Test ===")
    
    registry = ToolRegistry()
    
    # Register tools with different access levels
    registry.register_local_tool(MockTool("public_tool"), access_groups=[])
    registry.register_local_tool(MockTool("admin_tool"), access_groups=['admin'])
    registry.register_local_tool(MockTool("user_tool"), access_groups=['user'])
    
    # Admin user should see all tools
    admin_schemas = await registry.get_schemas(admin_user)
    admin_tool_names = [s.name for s in admin_schemas]
    
    print(f"✓ Admin user schemas: {admin_tool_names}")
    assert "public_tool" in admin_tool_names
    assert "admin_tool" in admin_tool_names
    assert "user_tool" in admin_tool_names
    assert len(admin_tool_names) == 3
    
    # Regular user should only see public and user tools
    user_schemas = await registry.get_schemas(regular_user)
    user_tool_names = [s.name for s in user_schemas]
    
    print(f"✓ Regular user schemas: {user_tool_names}")
    assert "public_tool" in user_tool_names
    assert "user_tool" in user_tool_names
    assert "admin_tool" not in user_tool_names
    assert len(user_tool_names) == 2


@pytest.mark.asyncio
async def test_tool_not_found():
    """Test execution of non-existent tool."""
    print("\n=== Tool Not Found Test ===")
    
    registry = ToolRegistry()
    
    user = User(id="user", username="user", group_memberships=['user'])
    context = ToolContext(
        user=user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    tool_call = ToolCall(
        id="call_1",
        name="nonexistent_tool",
        arguments={"message": "test"}
    )
    
    result = await registry.execute(tool_call, context)
    
    print(f"✓ Non-existent tool handled gracefully")
    print(f"  Error: {result.error}")
    
    assert result.success is False
    assert "not found" in result.result_for_llm.lower()


@pytest.mark.asyncio
async def test_duplicate_tool_registration():
    """Test that registering the same tool twice raises error."""
    print("\n=== Duplicate Registration Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("duplicate_tool")
    
    # First registration should succeed
    registry.register_local_tool(tool, access_groups=[])
    print(f"✓ First registration succeeded")
    
    # Second registration should fail
    with pytest.raises(ValueError, match="already registered"):
        registry.register_local_tool(tool, access_groups=[])
    
    print(f"✓ Duplicate registration properly rejected")


@pytest.mark.asyncio
async def test_tool_access_group_intersection(admin_user):
    """Test that access is granted on ANY matching group (not all groups)."""
    print("\n=== Group Intersection Test ===")
    
    registry = ToolRegistry()
    tool = MockTool("multi_group_tool")
    
    # Tool requires either admin OR analyst
    registry.register_local_tool(tool, access_groups=['admin', 'analyst'])
    
    # User has admin (but not analyst) - should still have access
    context = ToolContext(
        user=admin_user,
        conversation_id="test_conv",
        request_id="test_req"
    )
    
    tool_call = ToolCall(id="call_1", name="multi_group_tool", arguments={"message": "test"})
    result = await registry.execute(tool_call, context)
    
    print(f"✓ User with ONE matching group granted access")
    print(f"  User groups: {admin_user.group_memberships}")
    print(f"  Tool requires: ['admin', 'analyst']")
    print(f"  Intersection: {set(admin_user.group_memberships) & set(['admin', 'analyst'])}")
    
    assert result.success is True


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing all registered tools."""
    print("\n=== List Tools Test ===")
    
    registry = ToolRegistry()
    
    registry.register_local_tool(MockTool("tool1"), access_groups=[])
    registry.register_local_tool(MockTool("tool2"), access_groups=['admin'])
    registry.register_local_tool(MockTool("tool3"), access_groups=['user'])
    
    tools = await registry.list_tools()
    
    print(f"✓ Listed {len(tools)} tools")
    print(f"  Tools: {tools}")
    
    assert len(tools) == 3
    assert "tool1" in tools
    assert "tool2" in tools
    assert "tool3" in tools
