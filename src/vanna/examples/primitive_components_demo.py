"""
Demonstration of the new primitive component system.

This example shows how tools now compose UI from primitive, domain-agnostic
components instead of using semantic components like ToolExecutionComponent.

Usage:
  PYTHONPATH=. python vanna/examples/primitive_components_demo.py
"""

import asyncio
import uuid
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
)


class PrimitiveComponentsAgent(Agent):
    """Agent that demonstrates the new primitive component system."""

    async def send_message(
        self,
        user: User,
        message: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[UiComponent, None]:
        """Send message and demonstrate primitive component composition."""

        session_id = str(uuid.uuid4())[:8]

        # Demo 1: Tool execution using primitive components
        yield UiComponent(rich_component=RichTextComponent(
            content="## Primitive Components Demo\n\nShowing how tools now compose UI from primitive components:",
            markdown=True
        ))

        # Status card for overall operation
        operation_status = StatusCardComponent(
            id=f"operation-{session_id}",
            title="Data Analysis Pipeline",
            status="running",
            description="Processing user data through multiple analysis stages",
            icon="⚙️"
        )
        yield UiComponent(rich_component=operation_status)

        # Progress display for overall progress
        overall_progress = ProgressDisplayComponent(
            id=f"progress-{session_id}",
            label="Overall Progress",
            value=0.0,
            description="Starting analysis...",
            animated=True
        )
        yield UiComponent(rich_component=overall_progress)

        # Log viewer for detailed output
        log_viewer = LogViewerComponent(
            id=f"logs-{session_id}",
            title="Analysis Log",
            entries=[],
            show_timestamps=True,
            auto_scroll=True
        )
        yield UiComponent(rich_component=log_viewer)

        # Simulate analysis stages
        stages = [
            ("Data Loading", "📊", 0.2),
            ("Data Validation", "✅", 0.4),
            ("Statistical Analysis", "🧮", 0.6),
            ("Report Generation", "📄", 0.8),
            ("Finalization", "🎯", 1.0)
        ]

        for i, (stage_name, stage_icon, progress_value) in enumerate(stages):
            await asyncio.sleep(0.8)

            # Update overall status
            status = "success" if progress_value == 1.0 else "running"
            yield UiComponent(rich_component=operation_status.set_status(status, f"Executing: {stage_name}"))

            # Update progress
            yield UiComponent(rich_component=overall_progress.update_progress(progress_value, f"Executing {stage_name}..."))

            # Add log entry
            yield UiComponent(rich_component=log_viewer.add_entry(f"Starting {stage_name}", "info"))

            # Create a status card for this specific stage
            stage_status = StatusCardComponent(
                id=f"stage-{i}-{session_id}",
                title=stage_name,
                status="running" if progress_value < 1.0 else "success",
                description=f"Processing stage {i+1} of {len(stages)}",
                icon=stage_icon
            )
            yield UiComponent(rich_component=stage_status)

            await asyncio.sleep(0.5)

            # Complete the stage
            final_stage_status = "success" if progress_value < 1.0 else "completed"
            yield UiComponent(rich_component=stage_status.set_status(final_stage_status, f"{stage_name} completed successfully"))
            yield UiComponent(rich_component=log_viewer.add_entry(f"Completed {stage_name}", "info"))

        # Demo 2: Badge and IconText primitives
        yield UiComponent(rich_component=RichTextComponent(
            content="\n### Primitive Component Examples\n\nShowing individual primitive components:",
            markdown=True
        ))

        # Various badge examples
        badges = [
            BadgeComponent(text="Processing", variant="primary", size="small"),
            BadgeComponent(text="Complete", variant="success", size="medium"),
            BadgeComponent(text="Warning", variant="warning", size="large", icon="⚠️"),
            BadgeComponent(text="Error", variant="error", size="medium", icon="❌"),
        ]

        for badge in badges:
            yield UiComponent(rich_component=badge)

        # IconText examples
        icon_texts = [
            IconTextComponent(icon="📊", text="Data Analysis Complete", variant="primary", size="large"),
            IconTextComponent(icon="✅", text="All tests passed", variant="default", size="medium"),
            IconTextComponent(icon="⏱️", text="Processing time: 2.3s", variant="secondary", size="small"),
        ]

        for icon_text in icon_texts:
            yield UiComponent(rich_component=icon_text)

        # Demo 3: Comparison with old approach
        yield UiComponent(rich_component=RichTextComponent(
            content=f"""
## Key Benefits of Primitive Components

**Before (Semantic Components)):**
```python
# Tool creates semantic component
tool_execution = ToolExecutionComponent(
    tool_name="analyze_data",
    status="running",
    # Mixed UI and business logic
)
```

**After (Primitive Components):**
```python
# Tool composes UI from primitives
status_card = StatusCardComponent(
    title="Data Analysis",
    status="running",  # Pure UI state
    icon="📊"
)
progress = ProgressDisplayComponent(
    label="Analysis Progress",
    value=0.5
)
logs = LogViewerComponent(
    title="Analysis Log",
    entries=log_entries
)
```

### Benefits:
- **Separation of Concerns**: UI components are purely presentational
- **Reusability**: Status cards work for any process, not just tools
- **Composability**: Tools build exactly the UI they need
- **Maintainability**: Changes to business logic don't affect UI components
- **Extensibility**: New tools don't require new component types

Your message was: "{message}"
""",
            markdown=True
        ))


def create_primitive_demo_agent() -> PrimitiveComponentsAgent:
    """Create a primitive components demo agent.

    Returns:
        Configured PrimitiveComponentsAgent instance
    """
    llm_service = MockLlmService(
        response_content="Primitive components demo response"
    )

    return PrimitiveComponentsAgent(
        llm_service=llm_service,
        config=AgentConfig(
            stream_responses=True,
            include_thinking_indicators=False,
        ),
    )


async def main() -> None:
    """Run the primitive components demo."""

    # Create agent
    agent = create_primitive_demo_agent()

    # Create a test user
    user = User(
        id="user123",
        username="demo_user",
        email="demo@example.com",
        permissions=[]
    )

    # Start a conversation
    conversation_id = "primitive_demo_123"
    user_message = "Show me how the new primitive component system works!"

    print(f"User: {user_message}")
    print("Agent response (primitive components):")
    print("=" * 60)

    # Send message and display components
    component_count = 0
    async for component in agent.send_message(
        user=user,
        message=user_message
    ,
        conversation_id=conversation_id
    ):
        component_count += 1
        component_type = getattr(component, 'type', component.__class__.__name__)
        component_id = getattr(component, 'id', 'N/A')

        print(f"[{component_count:2d}] {component_type.value if hasattr(component_type, 'value') else component_type} (id: {component_id[:12] if len(str(component_id)) > 12 else component_id})")

        rich_comp = component.rich_component
        
        # Show component details
        if hasattr(rich_comp, 'title'):
            print(f"     Title: {rich_comp.title}")
        if hasattr(rich_comp, 'status'):
            print(f"     Status: {rich_comp.status}")
        if hasattr(rich_comp, 'description') and rich_comp.description:
            desc = rich_comp.description[:60] + "..." if len(rich_comp.description) > 60 else rich_comp.description
            print(f"     Description: {desc}")
        if hasattr(rich_comp, 'value') and hasattr(rich_comp.type, 'value') and rich_comp.type.value == 'progress_display':
            print(f"     Progress: {rich_comp.value:.1%}")

        print()

    print("=" * 60)
    print(f"Total components emitted: {component_count}")
    print("\nThis demonstrates how tools can now compose rich UIs")
    print("from primitive, reusable components without semantic coupling!")


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting Primitive Components Demo...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()
