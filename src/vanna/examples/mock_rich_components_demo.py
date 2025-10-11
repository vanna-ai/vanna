"""
Mock rich components demonstration example.

This example shows how to create an agent that emits rich, stateful components
including cards, task lists, and tool execution displays using a mock LLM service.

Usage:
  PYTHONPATH=. python vanna/examples/mock_rich_components_demo.py
"""

import asyncio
import time
from datetime import datetime
from typing import AsyncGenerator, Optional

from vanna import (
    AgentConfig,
    Agent,
    MemoryConversationStore,
    MockLlmService,
    User,
)
from vanna.core.components import UiComponent
from vanna.core.rich_components import (
    StatusCardComponent,
    ProgressDisplayComponent,
    LogViewerComponent,
    BadgeComponent,
    IconTextComponent,
    RichTextComponent,
    Task,
)


class RichComponentsAgent(Agent):
    """Agent that demonstrates rich component capabilities."""

    async def send_message(
        self,
        user: User,
        message: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[UiComponent, None]:
        """Send message and yield UiComponent(rich_component=rich) components."""

        # Welcome message using IconText
        yield UiComponent(rich_component=IconTextComponent(
            id="welcome-message",
            icon="👋",
            text=f"Hello {user.username}! I'll demonstrate primitive components.",
            variant="primary",
            size="large"
        ))

        # Status card showing we're processing
        status_card = StatusCardComponent(
            id="processing-status",
            title="Processing Request",
            status="running",
            description="Processing your request...",
            icon="⚙️"
        )
        yield UiComponent(rich_component=status_card)

        # Simulate some processing time
        await asyncio.sleep(1)

        # Update status to success
        yield UiComponent(rich_component=status_card.set_status("success", "Request processed successfully!"))

        # Create a status card for overall demo progress
        demo_card = StatusCardComponent(
            id="demo-progress",
            title="Demo Progress",
            status="running",
            description="Starting primitive components demonstration...",
            icon="🎯"
        )
        yield UiComponent(rich_component=demo_card)

        # Create badges for different stages
        stages = [
            ("Initialize", "success", "✅"),
            ("Components", "running", "⚙️"),
            ("Progress", "pending", "⏳"),
            ("Logs", "pending", "📋"),
            ("Complete", "pending", "🎉"),
        ]

        for stage_name, stage_status, stage_icon in stages:
            yield UiComponent(rich_component=BadgeComponent(
                id=f"stage-{stage_name.lower()}",
                text=stage_name,
                variant=stage_status if stage_status != "pending" else "default",
                icon=stage_icon,
                size="md"
            ))

        # Progress display
        progress_display = ProgressDisplayComponent(
            id="demo-progress-bar",
            label="Overall Progress",
            value=0.2,
            description="Initializing demonstration...",
            status="info",
            animated=True
        )
        yield UiComponent(rich_component=progress_display)

        # Create log viewer for detailed progress
        log_viewer = LogViewerComponent(
            id="demo-logs",
            title="Demo Activity Log"
        )
        yield UiComponent(rich_component=log_viewer)

        # Simulate work with updates
        for i in range(3):
            await asyncio.sleep(1)

            # Update progress
            progress_value = 0.2 + (i + 1) * 0.2
            step_name = ["Creating components", "Updating progress", "Finalizing demo"][i]

            yield UiComponent(rich_component=progress_display.update_progress(
                progress_value,
                f"Step {i + 2} of 5: {step_name}..."
            ))

            # Update demo card
            yield UiComponent(rich_component=demo_card.set_status(
                "running",
                f"Step {i + 2} of 5 completed. Progress: {int(progress_value * 100)}%"
            ))

            # Add log entry
            yield UiComponent(rich_component=log_viewer.add_entry(f"Completed step: {step_name}", "info"))

            # Update stage badges
            if i == 0:
                yield UiComponent(rich_component=BadgeComponent(
                    id="stage-components",
                    text="Components",
                    variant="success",
                    icon="✅",
                    size="md"
                ))
            elif i == 1:
                yield UiComponent(rich_component=BadgeComponent(
                    id="stage-progress",
                    text="Progress",
                    variant="success",
                    icon="✅",
                    size="md"
                ))
                yield UiComponent(rich_component=BadgeComponent(
                    id="stage-logs",
                    text="Logs",
                    variant="running",
                    icon="📋",
                    size="md"
                ))

        # Tool execution using primitive components
        tool_status = StatusCardComponent(
            id="demo-tool",
            title="Analyze Data Tool",
            status="running",
            description="Running regression analysis on user_data.csv",
            icon="🔬"
        )
        yield UiComponent(rich_component=tool_status)

        # Tool progress
        tool_progress = ProgressDisplayComponent(
            id="tool-progress",
            label="Tool Execution",
            value=0.0,
            description="Initializing tool...",
            animated=True
        )
        yield UiComponent(rich_component=tool_progress)

        # Tool logs
        tool_logs = LogViewerComponent(
            id="tool-logs",
            title="Tool Execution Log"
        )
        yield UiComponent(rich_component=tool_logs)

        # Simulate tool execution steps
        tool_steps = [
            (0.2, "Loading dataset...", "info"),
            (0.4, "Dataset loaded: 1000 rows, 5 columns", "info"),
            (0.6, "Preprocessing data...", "info"),
            (0.8, "Running regression analysis...", "info"),
            (1.0, "Analysis complete!", "info")
        ]

        for progress_val, log_message, log_level in tool_steps:
            await asyncio.sleep(0.5)

            yield UiComponent(rich_component=tool_progress.update_progress(
                progress_val,
                f"Progress: {int(progress_val * 100)}%"
            ))
            yield UiComponent(rich_component=tool_logs.add_entry(log_message, log_level))

        # Complete tool execution
        yield UiComponent(rich_component=tool_status.set_status(
            "success",
            "Tool completed successfully. R² = 0.85, strong correlation found."
        ))

        # Show results using IconText
        yield UiComponent(rich_component=IconTextComponent(
            id="tool-results",
            icon="📊",
            text="Analysis Results: R² = 0.85 (Strong correlation)",
            variant="success",
            size="medium"
        ))

        # Update final stage badge
        yield UiComponent(rich_component=BadgeComponent(
            id="stage-logs",
            text="Logs",
            variant="success",
            icon="✅",
            size="md"
        ))
        yield UiComponent(rich_component=BadgeComponent(
            id="stage-complete",
            text="Complete",
            variant="success",
            icon="🎉",
            size="md"
        ))

        # Final updates
        yield UiComponent(rich_component=progress_display.update_progress(1.0, "Demo completed successfully!"))

        yield UiComponent(rich_component=demo_card.set_status(
            "success",
            "Primitive components demonstration finished successfully!"
        ))

        # Add final log entry
        yield UiComponent(rich_component=tool_logs.add_entry("Demo completed successfully!", "info"))

        # Add final text response
        yield UiComponent(rich_component=RichTextComponent(
            content=f"""## Primitive Components Demo Complete!

I've demonstrated the new primitive component system:

- **Status Cards**: Domain-agnostic status displays that work for any process
- **Progress Displays**: Reusable progress indicators with animations
- **Log Viewers**: Structured log display for any activity
- **Badges**: Flexible status and category indicators
- **Icon Text**: Composable icon+text combinations

### Key Benefits of Primitive Components:

- **Separation of Concerns**: UI components are purely presentational
- **Reusability**: Components work across different domains and tools
- **Composability**: Tools build exactly the UI they need from primitives
- **Maintainability**: Business logic changes don't affect UI components
- **Extensibility**: New tools don't require new component types

**Before**: Semantic `ToolExecutionComponent` mixed UI with business logic
**After**: Tools compose UI from primitive `StatusCard` + `ProgressDisplay` + `LogViewer`

Your message was: "{message}"
""",
            markdown=True
        ))


# CLI compatibility alias
create_demo_agent = lambda: create_rich_demo_agent()


def create_rich_demo_agent() -> RichComponentsAgent:
    """Create a primitive components demo agent.

    Returns:
        Configured RichComponentsAgent instance
    """
    llm_service = MockLlmService(
        response_content="Primitive components demo response"
    )

    return RichComponentsAgent(
        llm_service=llm_service,
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=False,  # We'll use custom status cards
        ),
    )


async def main() -> None:
    """Run the primitive components demo."""

    # Create agent
    agent = create_rich_demo_agent()

    # Create a test user
    user = User(
        id="user123",
        username="demo_user",
        email="demo@example.com",
        permissions=[]
    )

    # Start a conversation
    conversation_id = "primitive_demo_123"
    user_message = "Show me the primitive components demo!"

    print(f"User: {user_message}")
    print("Agent response (primitive components):")
    print("=" * 50)

    # Send message and display components
    component_count = 0
    async for component in agent.send_message(
        user=user,
        message=user_message
    ,
        conversation_id=conversation_id
    ):
        component_count += 1
        rich_comp = component.rich_component
        component_type = getattr(rich_comp, 'type', rich_comp.__class__.__name__)
        component_id = getattr(rich_comp, 'id', 'N/A')
        lifecycle = getattr(rich_comp, 'lifecycle', 'N/A')

        print(f"[{component_count:2d}] {component_type} (id: {component_id[:8]}, lifecycle: {lifecycle})")

        # Show some component details
        if hasattr(rich_comp, 'title'):
            print(f"     Title: {rich_comp.title}")
        if hasattr(rich_comp, 'content') and len(str(rich_comp.content)) < 100:
            print(f"     Content: {rich_comp.content}")
        if hasattr(rich_comp, 'status'):
            print(f"     Status: {rich_comp.status}")
        if hasattr(rich_comp, 'value') and hasattr(rich_comp.type, 'value') and rich_comp.type.value == 'progress_bar':
            print(f"     Progress: {rich_comp.value:.1%}")

        print()

    print("=" * 50)
    print(f"Total components emitted: {component_count}")


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting Primitive Components Demo...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()