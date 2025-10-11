"""
Email authentication example for the Vanna Agents framework.

This example demonstrates how to create an agent with email-based authentication
where users are prompted for their email address in chat and the system creates
a user profile based on that email.

## What This Example Shows

1. **UserService Implementation**: A demo `DemoEmailUserService` that:
   - Stores users in memory
   - Authenticates users by email validation
   - Creates user profiles automatically
   - Manages user permissions

2. **Authentication Tool**: An `AuthTool` that:
   - Takes an email address as input
   - Uses the UserService to authenticate/create users
   - Returns rich UI components for success/error feedback
   - Provides structured results for the LLM

3. **In-Chat Authentication Flow**: Shows how:
   - Users can provide their email in natural conversation
   - The agent can prompt for authentication when needed
   - Authentication results are displayed with rich UI components
   - The system maintains user context across conversations

## Key Components

- `DemoEmailUserService`: Implements the `UserService` interface
- `AuthTool`: Implements the `Tool` interface for authentication
- Rich UI components for authentication feedback
- Integration with the agent's tool registry and conversation store

## Usage

Interactive: python -m vanna.examples.email_auth_example

## Note

This example uses a simplified mock LLM that doesn't actually call tools.
In a real implementation with OpenAI or Anthropic, the LLM would automatically
detect email addresses in user messages and call the authenticate_user tool.

For production use, you would:
- Replace DemoEmailUserService with a database-backed implementation
- Add proper email validation and security measures
- Implement session management in the server layer
- Add proper error handling and rate limiting
"""

import asyncio
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field

from vanna import (
    AgentConfig,
    Agent,
    MemoryConversationStore,
    MockLlmService,
    User,
)
from vanna.core import Tool, UserService
from vanna.core import ToolContext, ToolResult
from vanna.core.registry import ToolRegistry
from vanna.core.components import UiComponent
from vanna.core import RichComponent


# Demo User Service Implementation
class DemoEmailUserService(UserService):
    """Demo user service that authenticates users by email."""
    
    def __init__(self):
        """Initialize with in-memory user store."""
        self._users: Dict[str, User] = {}  # user_id -> User
        self._email_to_id: Dict[str, str] = {}  # email -> user_id
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user by email."""
        email = credentials.get("email")
        if not email or not self._is_valid_email(email):
            return None
        
        # Check if user exists
        user_id = self._email_to_id.get(email)
        if user_id:
            return self._users[user_id]
        
        # Create new user
        user_id = f"user_{len(self._users) + 1}"
        username = email.split("@")[0]
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            permissions=["basic_user"],
            metadata={"auth_method": "email"}
        )
        
        self._users[user_id] = user
        self._email_to_id[email] = user_id
        return user
    
    async def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has permission."""
        return permission in user.permissions
    
    def _is_valid_email(self, email: str) -> bool:
        """Simple email validation."""
        return "@" in email and "." in email.split("@")[1]


# Authentication Tool
class AuthArgs(BaseModel):
    """Arguments for authentication."""
    email: str = Field(description="User's email address")


class AuthTool(Tool[AuthArgs]):
    """Tool to authenticate users by email."""
    
    def __init__(self, user_service: DemoEmailUserService):
        self.user_service = user_service
    
    @property
    def name(self) -> str:
        return "authenticate_user"
    
    @property 
    def description(self) -> str:
        return "Authenticate a user by their email address. Use this when the user provides an email."
    
    def get_args_schema(self) -> Type[AuthArgs]:
        return AuthArgs
    
    async def execute(self, context: ToolContext, args: AuthArgs) -> ToolResult:
        """Execute authentication."""
        user = await self.user_service.authenticate({"email": args.email})
        
        if user:
            success_msg = f"✅ Welcome {user.username}! You're now authenticated as {user.email}"
            
            auth_component = RichComponent(
                type="status_card",
                data={
                    "title": "Authentication Success",
                    "status": "success", 
                    "description": success_msg,
                    "icon": "✅",
                    "metadata": {
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                    }
                }
            )
            
            return ToolResult(
                success=True,
                result_for_llm=f"User successfully authenticated as {user.username} ({user.email}). They can now access personalized features.",
                ui_component=UiComponent(rich_component=auth_component)
            )
        else:
            error_msg = f"❌ Invalid email format: {args.email}"
            error_component = RichComponent(
                type="status_card",
                data={
                    "title": "Authentication Failed",
                    "status": "error",
                    "description": error_msg,
                    "icon": "❌",
                    "metadata": {"email": args.email}
                }
            )
            
            return ToolResult(
                success=False,
                result_for_llm=f"Authentication failed for {args.email}. Please provide a valid email address.",
                ui_component=UiComponent(rich_component=error_component),
                error=error_msg
            )


def create_demo_agent() -> Agent:
    """Create a demo agent for REPL and server usage.
    
    Returns:
        Configured Agent instance with email authentication
    """
    return create_auth_agent()


def create_auth_agent() -> Agent:
    """Create agent with email authentication."""
    
    # Create user service
    user_service = DemoEmailUserService()
    
    # Use simple mock LLM - the system prompt will guide behavior
    llm_service = MockLlmService(
        response_content="Hello! I'm your AI assistant. To provide you with personalized help, I'll need your email address for authentication. Please share your email with me, and I'll use the authenticate_user tool to set up your profile."
    )
    
    # Create tool registry with auth tool
    tool_registry = ToolRegistry()
    auth_tool = AuthTool(user_service)
    tool_registry.register(auth_tool)
    
    # Create agent with authentication system prompt
    agent = Agent(
        llm_service=llm_service,
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=False,  # Cleaner output for demo
            system_prompt="""You are a helpful AI assistant with an email-based authentication system.

AUTHENTICATION BEHAVIOR:
1. When a user provides an email address in their message, immediately use the 'authenticate_user' tool
2. Look for emails in patterns like "my email is...", "I'm john@example.com", or any text with @ symbols  
3. If user isn't authenticated, politely ask for their email address to get started
4. After successful authentication, welcome them by name and offer personalized assistance
5. Be friendly and helpful throughout the process

Remember: Authentication is required for personalized features!"""
        ),
        tool_registry=tool_registry,
        conversation_store=MemoryConversationStore(),
    )
    
    return agent


async def demo_auth_flow():
    """Demonstrate the authentication flow with simple output."""
    agent = create_auth_agent()
    
    # Start with anonymous user
    user = User(id="anonymous", username="guest", email=None, permissions=[])
    conversation_id = "auth_demo_conv"
    
    print("=== Email Authentication Demo ===")
    print("This example shows how an agent can authenticate users via email in chat.")
    print("Note: This uses a simple mock LLM for demonstration purposes.\n")
    
    # Demo conversation
    print("🔹 Step 1: Initial greeting")
    print("User: Hello!")
    print("Agent: ", end="")
    
    async for component in agent.send_message(
        user=user, message="Hello!", conversation_id=conversation_id
    ):
        if hasattr(component, 'rich_component') and component.rich_component.type.value == "text":
            content = component.rich_component.data.get("content") or getattr(component.rich_component, "content", "")
            if content:
                print(content)
                break
    
    print("\n" + "="*60)
    
    print("\n🔹 Step 2: User provides email for authentication")
    print("User: My email is alice@example.com")
    print("Agent: ", end="")
    
    # This should trigger the auth tool
    auth_shown = False
    async for component in agent.send_message(
        user=user, message="My email is alice@example.com", conversation_id=conversation_id
    ):
        if hasattr(component, 'rich_component'):
            rich_comp = component.rich_component
            if rich_comp.type.value == "status_card" and not auth_shown:
                status = rich_comp.data.get("status", "")
                desc = rich_comp.data.get("description", "")
                if status == "success":
                    auth_shown = True
                    print(f"🔐 {desc}")
                    break
    
    print("\n" + "="*60)
    
    print("\n🔹 Step 3: Post-authentication interaction") 
    print("User: What can you help me with now?")
    print("Agent: ", end="")
    
    async for component in agent.send_message(
        user=user, message="What can you help me with now?", conversation_id=conversation_id
    ):
        if hasattr(component, 'rich_component') and component.rich_component.type.value == "text":
            content = component.rich_component.data.get("content") or getattr(component.rich_component, "content", "")
            if content:
                print(content)
                break
    
    print("\n" + "="*60)
    print("\n✅ Authentication demo complete!")
    print("\nKey Features Demonstrated:")
    print("• Email-based user authentication")
    print("• Tool-based authentication flow")
    print("• In-memory user storage and management")
    print("• Rich UI components for auth feedback")


async def main():
    """Run the authentication example."""
    await demo_auth_flow()


def run_interactive():
    """Entry point for interactive usage."""
    print("Starting email authentication example...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()