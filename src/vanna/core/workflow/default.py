"""
Default workflow handler implementation with setup health checking.

This module provides a default implementation of the WorkflowHandler interface
that provides a smart starter UI based on available tools and setup status.
"""

from typing import TYPE_CHECKING, List, Optional, Dict, Any
import traceback
import uuid
from .base import WorkflowHandler, WorkflowResult

if TYPE_CHECKING:
    from ..agent.agent import Agent
    from ..user.models import User
    from ..storage import Conversation

# Import components at module level to avoid circular imports
from vanna.components import (
    UiComponent,
    RichTextComponent,
    StatusCardComponent,
    ButtonComponent,
    ButtonGroupComponent,
    SimpleTextComponent,
)


class DefaultWorkflowHandler(WorkflowHandler):
    """Default workflow handler that provides setup health checking and starter UI.

    This handler provides a starter UI that:
    - Checks if run_sql tool is available (critical)
    - Checks if memory tools are available (warning if missing)
    - Checks if visualization tools are available
    - Provides appropriate setup guidance based on what's missing
    """

    def __init__(self, welcome_message: Optional[str] = None):
        """Initialize with optional custom welcome message.

        Args:
            welcome_message: Optional custom welcome message. If not provided,
                           generates one based on available tools.
        """
        self.welcome_message = welcome_message

    async def try_handle(
        self, agent: "Agent", user: "User", conversation: "Conversation", message: str
    ) -> WorkflowResult:
        """Handle basic commands, but mostly passes through to LLM."""

        # Handle basic help command
        if message.strip().lower() in ["/help", "help", "/h"]:
            return WorkflowResult(
                should_skip_llm=True,
                components=[
                    UiComponent(
                        rich_component=RichTextComponent(
                            content="## 🤖 Vanna AI Assistant\n\n"
                            "I'm your AI data analyst! Here's what I can help you with:\n\n"
                            "**💬 Natural Language Queries**\n"
                            '- "Show me sales data for last quarter"\n'
                            '- "Which customers have the highest orders?"\n'
                            '- "Create a chart of revenue by month"\n\n'
                            "**🔧 Commands**\n"
                            "- `/help` - Show this help message\n"
                            "- `/status` - Check setup status\n"
                            "- `/memories` - View recent memories\n\n"
                            "Just ask me anything about your data in plain English!",
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                ],
            )

        # Handle status check command
        if message.strip().lower() in ["/status", "status"]:
            return await self._generate_status_check(agent, user)

        # Handle get recent memories command
        if message.strip().lower() in [
            "/memories",
            "memories",
            "/recent_memories",
            "recent_memories",
        ]:
            return await self._get_recent_memories(agent, user, conversation)

        # Don't handle other messages, pass to LLM
        return WorkflowResult(should_skip_llm=False)

    async def get_starter_ui(
        self, agent: "Agent", user: "User", conversation: "Conversation"
    ) -> Optional[List[UiComponent]]:
        """Generate starter UI based on available tools and setup status."""

        # Get available tools
        tools = await agent.tool_registry.get_schemas(user)
        tool_names = [tool.name for tool in tools]

        # Analyze setup
        setup_analysis = self._analyze_setup(tool_names)

        components = []

        # Welcome message
        if self.welcome_message:
            components.append(
                UiComponent(
                    rich_component=RichTextComponent(
                        content=self.welcome_message, markdown=True
                    ),
                    simple_component=None,
                )
            )
        else:
            # Generate dynamic welcome based on setup
            components.append(self._generate_welcome_message(setup_analysis))

        # Add setup status cards
        components.extend(self._generate_setup_status_cards(setup_analysis))

        # Add quick action buttons if setup is good
        if setup_analysis["has_sql"]:
            quick_actions = self._generate_quick_actions(setup_analysis)
            if quick_actions:
                components.append(quick_actions)

        # Add setup guidance if needed
        if not setup_analysis["is_complete"]:
            setup_guidance = self._generate_setup_guidance(setup_analysis)
            if setup_guidance:
                components.append(setup_guidance)

        return components

    def _analyze_setup(self, tool_names: List[str]) -> Dict[str, Any]:
        """Analyze the current tool setup and return status."""

        # Critical tools
        has_sql = any(
            name in tool_names
            for name in ["run_sql", "sql_query", "execute_sql", "query_sql"]
        )

        # Memory tools (important but not critical)
        has_search = "search_saved_correct_tool_uses" in tool_names
        has_save = "save_question_tool_args" in tool_names
        has_memory = has_search and has_save

        # Visualization tools (nice to have)
        has_viz = any(
            name in tool_names
            for name in [
                "visualize_data",
                "create_chart",
                "plot_data",
                "generate_chart",
            ]
        )

        # Other useful tools
        has_calculator = any(
            name in tool_names for name in ["calculator", "calc", "calculate"]
        )

        # Determine overall status
        is_complete = has_sql and has_memory and has_viz
        is_functional = has_sql

        return {
            "has_sql": has_sql,
            "has_memory": has_memory,
            "has_search": has_search,
            "has_save": has_save,
            "has_viz": has_viz,
            "has_calculator": has_calculator,
            "is_complete": is_complete,
            "is_functional": is_functional,
            "tool_count": len(tool_names),
            "tool_names": tool_names,
        }

    def _generate_welcome_message(self, analysis: Dict[str, Any]) -> UiComponent:
        """Generate a dynamic welcome message based on setup analysis."""

        if not analysis["has_sql"]:
            # Critical issue - no SQL tool
            content = (
                "# ⚠️ Setup Required\n\n"
                "Welcome to **Vanna AI**! I'm your data analysis assistant, but I need a SQL connection to help you.\n\n"
                "Please configure a SQL tool to get started."
            )

        elif analysis["is_complete"]:
            # Perfect setup
            content = (
                "# 🎉 Welcome to Vanna AI!\n\n"
                "I'm your AI data analyst assistant, ready to help you explore and analyze your data!\n\n"
                "✅ **Your setup is complete** - SQL, memory, and visualization tools are all configured.\n\n"
                "Ask me anything about your data in plain English, and I'll help you find insights!"
            )

        elif analysis["is_functional"]:
            # Functional but could be better
            content = (
                "# 👋 Welcome to Vanna AI!\n\n"
                "I'm your AI data analyst assistant, ready to help you explore your data!\n\n"
                "✅ **SQL connection detected** - I can query your database.\n\n"
            )

            if not analysis["has_memory"]:
                content += "💡 *Consider adding memory tools to help me learn from successful queries.*\n\n"
            if not analysis["has_viz"]:
                content += (
                    "📊 *Add visualization tools to create charts and graphs.*\n\n"
                )

            content += "Go ahead and ask me anything about your data!"

        else:
            # Fallback
            content = (
                "# 🤖 Welcome to Vanna AI!\n\n"
                "I'm your AI data analyst assistant. Let me help you explore your data!\n\n"
                "Ask me anything about your data in natural language."
            )

        return UiComponent(
            rich_component=RichTextComponent(content=content, markdown=True),
            simple_component=None,
        )

    def _generate_setup_status_cards(
        self, analysis: Dict[str, Any]
    ) -> List[UiComponent]:
        """Generate status cards showing setup health."""

        cards = []

        # SQL Tool Status (Critical)
        if analysis["has_sql"]:
            sql_card = StatusCardComponent(
                title="SQL Connection",
                status="success",
                description="Database connection configured and ready",
                icon="✅",
            )
        else:
            sql_card = StatusCardComponent(
                title="SQL Connection",
                status="error",
                description="No SQL tool detected - this is required for data analysis",
                icon="❌",
            )
        cards.append(UiComponent(rich_component=sql_card, simple_component=None))

        # Memory Tools Status (Important)
        if analysis["has_memory"]:
            memory_card = StatusCardComponent(
                title="Memory System",
                status="success",
                description="Search and save tools configured - I can learn from successful queries",
                icon="🧠",
            )
        elif analysis["has_search"] or analysis["has_save"]:
            memory_card = StatusCardComponent(
                title="Memory System",
                status="warning",
                description="Partial memory setup - both search and save tools recommended",
                icon="⚠️",
            )
        else:
            memory_card = StatusCardComponent(
                title="Memory System",
                status="warning",
                description="Memory tools not configured - I won't remember successful patterns",
                icon="⚠️",
            )
        cards.append(UiComponent(rich_component=memory_card, simple_component=None))

        # Visualization Status (Nice to have)
        if analysis["has_viz"]:
            viz_card = StatusCardComponent(
                title="Visualization",
                status="success",
                description="Chart creation tools available",
                icon="📊",
            )
        else:
            viz_card = StatusCardComponent(
                title="Visualization",
                status="info",
                description="No visualization tools - results will be text/tables only",
                icon="📋",
            )
        cards.append(UiComponent(rich_component=viz_card, simple_component=None))

        return cards

    def _generate_quick_actions(self, analysis: Dict[str, Any]) -> UiComponent:
        """Generate quick action buttons for common tasks."""

        buttons = []

        # Always add help
        buttons.append(
            {"label": "💡 Show Help", "action": "/help", "variant": "secondary"}
        )

        # Add data exploration suggestions if SQL is available
        if analysis["has_sql"]:
            buttons.extend(
                [
                    {
                        "label": "🔍 Explore Tables",
                        "action": "What tables are available in the database?",
                        "variant": "secondary",
                    },
                    {
                        "label": "📊 Sample Data",
                        "action": "Show me a sample of data from the main tables",
                        "variant": "secondary",
                    },
                ]
            )

        # Add memory button if memory tools are available
        if analysis["has_memory"]:
            buttons.append(
                {
                    "label": "🧠 Recent Memories",
                    "action": "/memories",
                    "variant": "secondary",
                }
            )

        # Add visualization suggestion if viz tools available
        if analysis["has_viz"]:
            buttons.append(
                {
                    "label": "📈 Create Chart",
                    "action": "Create a chart showing trends in the data",
                    "variant": "secondary",
                }
            )

        return UiComponent(
            rich_component=ButtonGroupComponent(
                buttons=buttons,
                orientation="horizontal" if len(buttons) <= 3 else "vertical",
            ),
            simple_component=None,
        )

    def _generate_setup_guidance(
        self, analysis: Dict[str, Any]
    ) -> Optional[UiComponent]:
        """Generate setup guidance based on what's missing."""

        if not analysis["has_sql"]:
            # Critical guidance - need SQL
            content = (
                "## 🚨 Setup Required\n\n"
                "To get started with Vanna AI, you need to configure a SQL connection tool:\n\n"
                "```python\n"
                "from vanna.tools import RunSqlTool\n\n"
                "# Add SQL tool to your agent\n"
                "tool_registry.register(RunSqlTool(\n"
                '    connection_string="your-database-connection"\n'
                "))\n"
                "```\n\n"
                "**Next Steps:**\n"
                "1. Configure your database connection\n"
                "2. Add memory tools for learning\n"
                "3. Add visualization tools for charts"
            )

        else:
            # Improvement suggestions
            suggestions = []

            if not analysis["has_memory"]:
                suggestions.append(
                    "**🧠 Add Memory Tools** - Help me learn from successful queries:\n"
                    "```python\n"
                    "from vanna.tools import SearchSavedCorrectToolUses, SaveQuestionToolArgs\n"
                    "tool_registry.register(SearchSavedCorrectToolUses())\n"
                    "tool_registry.register(SaveQuestionToolArgs())\n"
                    "```"
                )

            if not analysis["has_viz"]:
                suggestions.append(
                    "**📊 Add Visualization** - Create charts and graphs:\n"
                    "```python\n"
                    "from vanna.tools import VisualizeDataTool\n"
                    "tool_registry.register(VisualizeDataTool())\n"
                    "```"
                )

            if suggestions:
                content = "## 💡 Suggested Improvements\n\n" + "\n\n".join(suggestions)
            else:
                return None  # No guidance needed

        return UiComponent(
            rich_component=RichTextComponent(content=content, markdown=True),
            simple_component=None,
        )

    async def _generate_status_check(
        self, agent: "Agent", user: "User"
    ) -> WorkflowResult:
        """Generate a detailed status check response."""

        # Get available tools
        tools = await agent.tool_registry.get_schemas(user)
        tool_names = [tool.name for tool in tools]
        analysis = self._analyze_setup(tool_names)

        # Generate status report
        status_content = "# 🔍 Setup Status Report\n\n"

        if analysis["is_complete"]:
            status_content += (
                "🎉 **Excellent!** Your Vanna AI setup is complete and optimized.\n\n"
            )
        elif analysis["is_functional"]:
            status_content += (
                "✅ **Good!** Your setup is functional with room for improvement.\n\n"
            )
        else:
            status_content += (
                "⚠️ **Action Required** - Your setup needs configuration.\n\n"
            )

        status_content += f"**Tools Detected:** {analysis['tool_count']} total\n\n"

        # Tool breakdown
        status_content += "## Tool Status\n\n"
        status_content += f"- **SQL Connection:** {'✅ Available' if analysis['has_sql'] else '❌ Missing (Required)'}\n"
        status_content += f"- **Memory System:** {'✅ Complete' if analysis['has_memory'] else '⚠️ Incomplete' if analysis['has_search'] or analysis['has_save'] else '❌ Missing'}\n"
        status_content += f"- **Visualization:** {'✅ Available' if analysis['has_viz'] else '📋 Text/Tables Only'}\n"
        status_content += f"- **Calculator:** {'✅ Available' if analysis['has_calculator'] else '➖ Not Available'}\n\n"

        if analysis["tool_names"]:
            status_content += (
                f"**Available Tools:** {', '.join(sorted(analysis['tool_names']))}"
            )

        components = [
            UiComponent(
                rich_component=RichTextComponent(content=status_content, markdown=True),
                simple_component=None,
            )
        ]

        # Add status cards
        components.extend(self._generate_setup_status_cards(analysis))

        # Add guidance if needed
        guidance = self._generate_setup_guidance(analysis)
        if guidance:
            components.append(guidance)

        return WorkflowResult(should_skip_llm=True, components=components)

    async def _get_recent_memories(
        self, agent: "Agent", user: "User", conversation: "Conversation"
    ) -> WorkflowResult:
        """Get and display recent memories from agent memory."""
        try:
            # Check if agent has memory capability
            if not hasattr(agent, "agent_memory") or agent.agent_memory is None:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# ⚠️ No Memory System\n\n"
                                "Agent memory is not configured. Recent memories are not available.\n\n"
                                "To enable memory, configure an AgentMemory implementation in your agent setup.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )

            # Create tool context
            from vanna.core.tool import ToolContext

            context = ToolContext(
                user=user,
                conversation_id=conversation.id,
                request_id=str(uuid.uuid4()),
                agent_memory=agent.agent_memory,
            )

            # Get recent memories
            memories = await agent.agent_memory.get_recent_memories(
                context=context, limit=10
            )

            if not memories:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# 🧠 Recent Memories\n\n"
                                "No recent memories found. As you use tools and ask questions, "
                                "successful patterns will be saved here for future reference.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )

            # Format memories for display
            memories_content = "# 🧠 Recent Memories\n\n"
            memories_content += f"Found {len(memories)} recent memor{'y' if len(memories) == 1 else 'ies'}:\n\n"

            for i, memory in enumerate(memories, 1):
                memories_content += f"## {i}. {memory.tool_name}\n"
                memories_content += f"**Question:** {memory.question}\n\n"
                memories_content += f"**Arguments:** `{memory.args}`\n\n"
                memories_content += (
                    f"**Success:** {'✅ Yes' if memory.success else '❌ No'}\n\n"
                )
                if memory.timestamp:
                    memories_content += f"**Timestamp:** {memory.timestamp}\n\n"
                memories_content += "---\n\n"

            return WorkflowResult(
                should_skip_llm=True,
                components=[
                    UiComponent(
                        rich_component=RichTextComponent(
                            content=memories_content, markdown=True
                        ),
                        simple_component=None,
                    )
                ],
            )

        except Exception as e:
            traceback.print_exc()
            return WorkflowResult(
                should_skip_llm=True,
                components=[
                    UiComponent(
                        rich_component=RichTextComponent(
                            content=f"# ❌ Error Retrieving Memories\n\n"
                            f"Failed to get recent memories: {str(e)}\n\n"
                            f"This may indicate an issue with the agent memory configuration.",
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                ],
            )
