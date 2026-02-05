#!/usr/bin/env python3
"""
Comprehensive test backend for vanna-webcomponent validation.

This backend exercises all component types and update patterns to validate
that nothing breaks during webcomponent pruning.

Usage:
    python test_backend.py --mode rapid      # Fast stress test
    python test_backend.py --mode realistic  # Realistic conversation flow
"""

import argparse
import asyncio
import json
import sys
import time
import traceback
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# Add vanna to path
sys.path.insert(0, "../vanna/src")

from vanna.core.rich_component import RichComponent, ComponentLifecycle
from vanna.components.rich import (
    RichTextComponent,
    StatusCardComponent,
    ProgressDisplayComponent,
    ProgressBarComponent,
    NotificationComponent,
    StatusIndicatorComponent,
    ButtonComponent,
    ButtonGroupComponent,
    CardComponent,
    TaskListComponent,
    Task,
    BadgeComponent,
    IconTextComponent,
    DataFrameComponent,
    ChartComponent,
    ArtifactComponent,
    LogViewerComponent,
    LogEntry,
    StatusBarUpdateComponent,
    TaskTrackerUpdateComponent,
    ChatInputUpdateComponent,
    TaskOperation,
)
from vanna.servers.base.models import ChatStreamChunk

# Request/Response models
class ChatRequest(BaseModel):
    """Chat request matching vanna API."""
    message: str
    conversation_id: Optional[str] = None
    request_id: Optional[str] = None
    request_context: Dict[str, Any] = {}


class UiComponent(BaseModel):
    """UI component wrapper."""
    rich_component: RichComponent


# Test state
test_state: Dict[str, Any] = {
    "mode": "realistic",
    "component_ids": {},  # Track component IDs for updates
    "action_count": 0,
}


async def yield_chunk(component: RichComponent, conversation_id: str, request_id: str) -> ChatStreamChunk:
    """Convert component to ChatStreamChunk."""
    return ChatStreamChunk(
        rich=component.serialize_for_frontend(),
        simple=None,
        conversation_id=conversation_id,
        request_id=request_id,
        timestamp=time.time(),
    )


async def delay(mode: str, short: float = 0.1, long: float = 0.5):
    """Add delay based on mode."""
    if mode == "realistic":
        await asyncio.sleep(long)
    elif mode == "rapid":
        await asyncio.sleep(short)


async def test_text_component(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test text component with markdown."""
    text_id = str(uuid.uuid4())
    test_state["component_ids"]["text"] = text_id

    # Create with comprehensive markdown
    text = RichTextComponent(
        id=text_id,
        content="""# Test Text Component

This component demonstrates **markdown rendering** with various formatting:

## Formatting Examples
- **Bold text** for emphasis
- *Italic text* for style
- `inline code` for snippets
- ~~Strikethrough~~ for deletions

### Lists
1. First ordered item
2. Second ordered item
3. Third ordered item

### Code Block
```python
def hello():
    return "Markdown works!"
```

> Blockquote to test quote rendering

This validates that markdown is properly parsed and displayed.""",
        markdown=True,
    )
    yield await yield_chunk(text, conversation_id, request_id)
    await delay(mode)

    # Update with simpler markdown
    text_updated = text.update(content="""# Updated Text Component

Text has been **successfully updated** with new markdown content!

- Update operation works ✓
- Markdown still renders ✓""")
    yield await yield_chunk(text_updated, conversation_id, request_id)
    await delay(mode)


async def test_status_card(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test status card with all states."""
    card_id = str(uuid.uuid4())
    test_state["component_ids"]["status_card"] = card_id

    # Create - pending
    status_card = StatusCardComponent(
        id=card_id,
        title="Status Card Test",
        status="pending",
        description="Testing status card component...",
        icon="⏳",
        collapsible=True,
        collapsed=False,
    )
    yield await yield_chunk(status_card, conversation_id, request_id)
    await delay(mode)

    # Update to running
    status_card_running = status_card.set_status("running", "Processing test...")
    yield await yield_chunk(status_card_running, conversation_id, request_id)
    await delay(mode)

    # Update to completed
    status_card_done = status_card.set_status("completed", "Test completed successfully!")
    status_card_done.icon = "✅"
    yield await yield_chunk(status_card_done, conversation_id, request_id)
    await delay(mode)


async def test_progress_display(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test progress display component."""
    progress_id = str(uuid.uuid4())
    test_state["component_ids"]["progress_display"] = progress_id

    # Create at 0%
    progress = ProgressDisplayComponent(
        id=progress_id,
        label="Test Progress",
        value=0.0,
        description="Starting test...",
        status="info",
        animated=True,
    )
    yield await yield_chunk(progress, conversation_id, request_id)
    await delay(mode, 0.05, 0.3)

    # Update to 50%
    progress_half = progress.update_progress(0.5, "Halfway there...")
    yield await yield_chunk(progress_half, conversation_id, request_id)
    await delay(mode, 0.05, 0.3)

    # Update to 100%
    progress_done = progress.update_progress(1.0, "Complete!")
    progress_done.status = "success"
    yield await yield_chunk(progress_done, conversation_id, request_id)
    await delay(mode)


async def test_card_component(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test card component with actions."""
    card_id = str(uuid.uuid4())
    test_state["component_ids"]["card"] = card_id

    # Create card with markdown content and buttons
    card = CardComponent(
        id=card_id,
        title="Test Card with Markdown",
        content="""# Card Content

This card demonstrates **markdown rendering** within cards:

- Interactive action buttons
- Collapsible sections
- Status indicators
- `Formatted text`

Click the buttons below to test interactivity!""",
        icon="🃏",
        status="info",
        markdown=True,
        collapsible=True,
        collapsed=False,
        actions=[
            {"label": "Test Action", "action": "/test-action", "variant": "primary"},
            {"label": "Cancel", "action": "/cancel", "variant": "secondary"},
        ],
    )
    yield await yield_chunk(card, conversation_id, request_id)
    await delay(mode)

    # Update card status and content
    card_updated = card.update(
        status="success",
        content="""# Card Updated Successfully!

The card content has been **updated** with:
- New status (success)
- New markdown content
- Same action buttons

✓ Update operation verified""",
        markdown=True
    )
    yield await yield_chunk(card_updated, conversation_id, request_id)
    await delay(mode)


async def test_task_list(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test task list component."""
    task_list_id = str(uuid.uuid4())
    test_state["component_ids"]["task_list"] = task_list_id

    # Create task list
    tasks = [
        Task(title="Setup development environment", description="Install dependencies and configure tools", status="completed", progress=1.0),
        Task(title="Write test suite", description="Create comprehensive component tests", status="in_progress", progress=0.7),
        Task(title="Run validation", description="Validate all components render correctly", status="pending"),
        Task(title="Prune webcomponent", description="Remove unused code and cruft", status="pending"),
    ]
    task_list = TaskListComponent(
        id=task_list_id,
        title="Webcomponent Validation Workflow",
        tasks=tasks,
        show_progress=True,
        show_timestamps=True,
    )
    yield await yield_chunk(task_list, conversation_id, request_id)
    await delay(mode)

    # Update task statuses
    tasks[1].status = "completed"
    tasks[1].progress = 1.0
    tasks[2].status = "in_progress"
    tasks[2].progress = 0.3
    task_list_updated = TaskListComponent(
        id=task_list_id,
        title="Webcomponent Validation Workflow (Updated)",
        tasks=tasks,
        show_progress=True,
        show_timestamps=True,
    )
    task_list_updated.lifecycle = ComponentLifecycle.UPDATE
    yield await yield_chunk(task_list_updated, conversation_id, request_id)
    await delay(mode)


async def test_progress_bar(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test progress bar component."""
    bar_id = str(uuid.uuid4())
    test_state["component_ids"]["progress_bar"] = bar_id

    # Create
    bar = ProgressBarComponent(
        id=bar_id,
        value=0.3,
        label="Loading",
        status="info",
    )
    yield await yield_chunk(bar, conversation_id, request_id)
    await delay(mode, 0.05, 0.2)

    # Update
    bar_updated = bar.update(value=0.8, status="success")
    yield await yield_chunk(bar_updated, conversation_id, request_id)
    await delay(mode)


async def test_notification(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test notification component."""
    for level in ["info", "success", "warning", "error"]:
        notif = NotificationComponent(
            id=str(uuid.uuid4()),
            message=f"This is a {level} notification",
            level=level,
            title=f"{level.capitalize()} Test",
        )
        yield await yield_chunk(notif, conversation_id, request_id)
        await delay(mode, 0.05, 0.2)


async def test_status_indicator(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test status indicator component."""
    indicator_id = str(uuid.uuid4())
    test_state["component_ids"]["status_indicator"] = indicator_id

    # Create with pulse
    indicator = StatusIndicatorComponent(
        id=indicator_id,
        status="running",
        message="Processing...",
        pulse=True,
    )
    yield await yield_chunk(indicator, conversation_id, request_id)
    await delay(mode)

    # Update to success
    indicator_success = indicator.update(status="success", message="Done!", pulse=False)
    yield await yield_chunk(indicator_success, conversation_id, request_id)
    await delay(mode)


async def test_badge(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test badge component."""
    badge = BadgeComponent(
        id=str(uuid.uuid4()),
        text="Test Badge",
        variant="primary",
    )
    yield await yield_chunk(badge, conversation_id, request_id)
    await delay(mode)


async def test_icon_text(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test icon_text component."""
    icon_text = IconTextComponent(
        id=str(uuid.uuid4()),
        icon="🔧",
        text="Tool Icon Test",
    )
    yield await yield_chunk(icon_text, conversation_id, request_id)
    await delay(mode)


async def test_buttons(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test button and button_group components."""
    # Single button
    button = ButtonComponent(
        label="Single Button",
        action="/button-test",
        variant="primary",
        icon="🔘",
    )
    yield await yield_chunk(button, conversation_id, request_id)
    await delay(mode, 0.05, 0.2)

    # Button group
    button_group = ButtonGroupComponent(
        buttons=[
            {"label": "Option 1", "action": "/option1", "variant": "primary"},
            {"label": "Option 2", "action": "/option2", "variant": "secondary"},
            {"label": "Option 3", "action": "/option3", "variant": "success"},
        ],
        orientation="horizontal",
    )
    yield await yield_chunk(button_group, conversation_id, request_id)
    await delay(mode)


async def test_dataframe(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test dataframe component with sample data."""
    dataframe_id = str(uuid.uuid4())
    test_state["component_ids"]["dataframe"] = dataframe_id

    # Create sample data
    sample_data = [
        {"id": 1, "name": "Alice", "age": 30, "city": "New York", "salary": 75000},
        {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco", "salary": 85000},
        {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago", "salary": 70000},
        {"id": 4, "name": "Diana", "age": 28, "city": "Boston", "salary": 80000},
        {"id": 5, "name": "Eve", "age": 32, "city": "Seattle", "salary": 90000},
    ]

    dataframe = DataFrameComponent.from_records(
        records=sample_data,
        title="📊 Employee Data",
        description="""Sample employee dataset demonstrating **DataFrame** features:

- **Searchable**: Try searching for names or cities
- **Sortable**: Click column headers to sort
- **Exportable**: Export to CSV/Excel
- **Paginated**: Navigate through rows

*5 employees across different cities*""",
        id=dataframe_id,
        searchable=True,
        sortable=True,
        exportable=True,
    )
    yield await yield_chunk(dataframe, conversation_id, request_id)
    await delay(mode)

    # Update with more data
    updated_data = sample_data + [
        {"id": 6, "name": "Frank", "age": 29, "city": "Austin", "salary": 78000},
    ]
    dataframe_updated = DataFrameComponent.from_records(
        records=updated_data,
        title="📊 Employee Data (Updated)",
        description="""Dataset **updated** with new employee!

✓ Added Frank from Austin
✓ Now showing 6 employees
✓ Update operation verified""",
        id=dataframe_id,
    )
    dataframe_updated.lifecycle = ComponentLifecycle.UPDATE
    yield await yield_chunk(dataframe_updated, conversation_id, request_id)
    await delay(mode)


async def test_chart(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test chart component with Plotly data."""
    chart_id = str(uuid.uuid4())
    test_state["component_ids"]["chart"] = chart_id

    # Create a simple bar chart
    chart_data = {
        "data": [
            {
                "x": ["Product A", "Product B", "Product C", "Product D"],
                "y": [20, 35, 30, 25],
                "type": "bar",
                "name": "Sales",
                "marker": {"color": "#667eea"},
            }
        ],
        "layout": {
            "title": "Product Sales",
            "xaxis": {"title": "Products"},
            "yaxis": {"title": "Sales (units)"},
        },
    }

    chart = ChartComponent(
        id=chart_id,
        chart_type="bar",
        data=chart_data,
        title="Sales Chart",
    )
    yield await yield_chunk(chart, conversation_id, request_id)
    await delay(mode)

    # Update to line chart
    line_chart_data = {
        "data": [
            {
                "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                "y": [10, 15, 13, 17, 21],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Revenue",
                "line": {"color": "#10b981", "width": 3},
            }
        ],
        "layout": {
            "title": "Monthly Revenue Trend",
            "xaxis": {"title": "Month"},
            "yaxis": {"title": "Revenue ($1000s)"},
        },
    }

    chart_updated = ChartComponent(
        id=chart_id,
        chart_type="line",
        data=line_chart_data,
        title="Revenue Chart",
    )
    chart_updated.lifecycle = ComponentLifecycle.UPDATE
    yield await yield_chunk(chart_updated, conversation_id, request_id)
    await delay(mode)

async def test_artifact(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test artifact component with HTML/SVG content."""
    artifact_id = str(uuid.uuid4())
    test_state["component_ids"]["artifact"] = artifact_id

    # Create SVG artifact
    svg_content = '''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="80" fill="#667eea" opacity="0.8"/>
    <circle cx="100" cy="100" r="60" fill="#764ba2" opacity="0.6"/>
    <circle cx="100" cy="100" r="40" fill="#f093fb" opacity="0.4"/>
    <text x="100" y="105" text-anchor="middle" fill="white" font-size="20" font-weight="bold">
        Test SVG
    </text>
</svg>'''

    artifact = ArtifactComponent(
        id=artifact_id,
        content=svg_content,
        artifact_type="svg",
        title="SVG Circle Visualization",
        description="Concentric circles demonstration",
        fullscreen_capable=True,
    )
    yield await yield_chunk(artifact, conversation_id, request_id)
    await delay(mode)


async def test_log_viewer(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test log viewer component."""
    log_id = str(uuid.uuid4())
    test_state["component_ids"]["log_viewer"] = log_id

    # Create initial log viewer with entries
    log_viewer = LogViewerComponent(
        id=log_id,
        title="System Logs",
        entries=[
            LogEntry(message="System started", level="info"),
            LogEntry(message="Loading configuration...", level="info"),
            LogEntry(message="Configuration loaded successfully", level="info"),
        ],
        searchable=True,
        auto_scroll=True,
    )
    yield await yield_chunk(log_viewer, conversation_id, request_id)
    await delay(mode, 0.05, 0.3)

    # Add warning
    log_viewer = log_viewer.add_entry("Memory usage at 75%", level="warning")
    yield await yield_chunk(log_viewer, conversation_id, request_id)
    await delay(mode, 0.05, 0.3)

    # Add error
    log_viewer = log_viewer.add_entry("Connection timeout", level="error", data={"host": "api.example.com", "port": 443})
    yield await yield_chunk(log_viewer, conversation_id, request_id)
    await delay(mode, 0.05, 0.3)

    # Add success
    log_viewer = log_viewer.add_entry("Reconnected successfully", level="info")
    yield await yield_chunk(log_viewer, conversation_id, request_id)
    await delay(mode)

async def test_ui_state_updates(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Test UI state update components."""
    # Status bar update
    status_bar = StatusBarUpdateComponent(
        message="Running comprehensive component test...",
        status="info",
    )
    yield await yield_chunk(status_bar, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    # Task tracker - add tasks to sidebar
    task1 = Task(
        title="Validate Text Components",
        description="Test text, markdown, and formatting",
        status="completed",
        progress=1.0,
    )
    task_tracker_add1 = TaskTrackerUpdateComponent.add_task(task1)
    yield await yield_chunk(task_tracker_add1, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    task2 = Task(
        title="Validate Data Components",
        description="Test DataFrame, Chart, Code blocks",
        status="in_progress",
        progress=0.6,
    )
    task_tracker_add2 = TaskTrackerUpdateComponent.add_task(task2)
    yield await yield_chunk(task_tracker_add2, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    task3 = Task(
        title="Validate Interactive Components",
        description="Test buttons, actions, and UI state",
        status="pending",
    )
    task_tracker_add3 = TaskTrackerUpdateComponent.add_task(task3)
    yield await yield_chunk(task_tracker_add3, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    # Update task 2 to completed
    task_tracker_update = TaskTrackerUpdateComponent(
        operation=TaskOperation.UPDATE_TASK,
        task_id=task2.id,
        status="completed",
        progress=1.0,
    )
    yield await yield_chunk(task_tracker_update, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    # Update status bar
    status_bar_complete = StatusBarUpdateComponent(
        message="All components validated successfully!",
        status="success",
    )
    yield await yield_chunk(status_bar_complete, conversation_id, request_id)
    await delay(mode, 0.1, 0.3)

    # Chat input update - change placeholder
    chat_input = ChatInputUpdateComponent(
        placeholder="Type a message to test chat input updates...",
        disabled=False,
    )
    yield await yield_chunk(chat_input, conversation_id, request_id)
    await delay(mode)


async def run_comprehensive_test(conversation_id: str, request_id: str, mode: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Run all component tests."""
    # Introduction
    intro = RichTextComponent(
        content=f"""# 🧪 Comprehensive Component Test

**Mode**: {mode}

## Test Coverage
This test validates **16 component types** supported by the webcomponent:
- ✅ Component creation
- ✅ Incremental updates
- ✅ Markdown rendering
- ✅ Interactive actions
- ✅ Data visualization

### Component Categories
1. **Primitive**: Text, Badge, Icon Text
2. **Feedback**: Status Card, Progress, Notifications, Logs
3. **Data**: Card, Task List, DataFrame, Chart, Code
4. **Specialized**: Artifact (SVG/HTML)
5. **Interactive**: Buttons with actions

Watch the sidebar checklist as components render! ➡️""",
        markdown=True,
    )
    yield await yield_chunk(intro, conversation_id, request_id)
    await delay(mode)

    # Run all tests
    async for chunk in test_text_component(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_status_card(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_progress_display(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_card_component(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_task_list(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_progress_bar(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_notification(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_status_indicator(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_badge(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_icon_text(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_buttons(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_dataframe(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_chart(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_artifact(conversation_id, request_id, mode):
        yield chunk

    async for chunk in test_log_viewer(conversation_id, request_id, mode):
        yield chunk

    # NOTE: Table, Container, and CodeBlock components are defined in vanna Python package
    # but NOT supported by the webcomponent (no renderers). Skipping these tests.
    # These are candidates for removal from the vanna package.

    async for chunk in test_ui_state_updates(conversation_id, request_id, mode):
        yield chunk

    # Completion message
    done = StatusCardComponent(
        title="✅ Test Suite Complete",
        status="completed",
        description=f"""All **16 component types** successfully rendered in **{mode}** mode!

**Validated:**
- Component creation & updates
- Markdown rendering
- Interactive buttons
- Data visualization
- UI state management

Check the sidebar for the complete checklist.""",
        icon="✅",
    )
    yield await yield_chunk(done, conversation_id, request_id)


async def handle_action_message(message: str, conversation_id: str, request_id: str) -> AsyncGenerator[ChatStreamChunk, None]:
    """Handle button action messages."""
    test_state["action_count"] += 1

    response = NotificationComponent(
        message=f"Action received: {message}",
        level="success",
        title=f"Action #{test_state['action_count']}",
    )
    yield await yield_chunk(response, conversation_id, request_id)

    # Also show a card with details
    card = CardComponent(
        title="Action Handler Response",
        content=f"Received action: `{message}`\n\nThis confirms button interactivity is working!",
        icon="🎯",
        status="success",
    )
    yield await yield_chunk(card, conversation_id, request_id)


# FastAPI app
app = FastAPI(title="Vanna Webcomponent Test Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (static directory for webcomponent)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.post("/api/vanna/v2/chat_sse")
async def chat_sse(chat_request: ChatRequest) -> StreamingResponse:
    """SSE endpoint for streaming chat."""
    conversation_id = chat_request.conversation_id or str(uuid.uuid4())
    request_id = chat_request.request_id or str(uuid.uuid4())
    message = chat_request.message.strip()

    async def generate() -> AsyncGenerator[str, None]:
        """Generate SSE stream."""
        try:
            # Handle button actions
            if message.startswith("/") and message != "/test":
                async for chunk in handle_action_message(message, conversation_id, request_id):
                    yield f"data: {chunk.model_dump_json()}\n\n"

            # Handle test command or initial message
            elif message == "/test" or "test" in message.lower():
                async for chunk in run_comprehensive_test(conversation_id, request_id, test_state["mode"]):
                    yield f"data: {chunk.model_dump_json()}\n\n"

            # Default response
            else:
                response = RichTextComponent(
                    content=f"You said: {message}\n\nType `/test` to run the comprehensive component test.",
                    markdown=True,
                )
                chunk = await yield_chunk(response, conversation_id, request_id)
                yield f"data: {chunk.model_dump_json()}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_message = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"ERROR in chat_sse: {error_message}")  # Log to console
            error_chunk = {
                "type": "error",
                "data": {"message": error_message},
                "conversation_id": conversation_id,
                "request_id": request_id,
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "mode": test_state["mode"]}


@app.get("/")
async def root():
    """Serve test HTML page."""
    html_path = os.path.join(os.path.dirname(__file__), "test-comprehensive.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {
        "message": "Vanna Webcomponent Test Backend",
        "mode": test_state["mode"],
        "endpoints": {
            "chat": "POST /api/vanna/v2/chat_sse",
            "health": "GET /health",
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test backend for vanna-webcomponent")
    parser.add_argument(
        "--mode",
        choices=["rapid", "realistic"],
        default="realistic",
        help="Test mode: rapid (fast) or realistic (with delays)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5555, help="Port to bind to")

    args = parser.parse_args()
    test_state["mode"] = args.mode

    print(f"Starting test backend in {args.mode} mode...")
    print(f"Server running at http://{args.host}:{args.port}")
    print("Send message '/test' to run comprehensive component test")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
