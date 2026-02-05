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
    CardComponent,
)

# Note: StatusCardComponent and ButtonGroupComponent are kept for /status command compatibility


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
            # Check if user is admin
            is_admin = "admin" in user.group_memberships

            help_content = (
                "## 🤖 thaink² AI Assistant\n\n"
                "I'm your AI data analyst! Here's what I can help you with:\n\n"
                "**💬 Natural Language Queries**\n"
                '- "Show me sales data for last quarter"\n'
                '- "Which customers have the highest orders?"\n'
                '- "Create a chart of revenue by month"\n\n'
                "**🔧 Commands**\n"
                "- `/help` - Show this help message\n"
            )

            if is_admin:
                help_content += (
                    "\n**🔒 Admin Commands**\n"
                    "- `/status` - Check setup status\n"
                    "- `/memories` - View and manage recent memories\n"
                    "- `/delete [id]` - Delete a memory by ID\n"
                )

            help_content += "\n\nJust ask me anything about your data in plain English!"

            return WorkflowResult(
                should_skip_llm=True,
                components=[
                    UiComponent(
                        rich_component=RichTextComponent(
                            content=help_content,
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                ],
            )

        # Handle status check command (admin-only)
        if message.strip().lower() in ["/status", "status"]:
            # Check if user is admin
            if "admin" not in user.group_memberships:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# 🔒 Access Denied\n\n"
                                "The `/status` command is only available to administrators.\n\n"
                                "If you need access to system status information, please contact your system administrator.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )
            return await self._generate_status_check(agent, user)

        # Handle get recent memories command (admin-only)
        if message.strip().lower() in [
            "/memories",
            "memories",
            "/recent_memories",
            "recent_memories",
        ]:
            # Check if user is admin
            if "admin" not in user.group_memberships:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# 🔒 Access Denied\n\n"
                                "The `/memories` command is only available to administrators.\n\n"
                                "If you need access to memory management features, please contact your system administrator.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )
            return await self._get_recent_memories(agent, user, conversation)

        # Handle delete memory command (admin-only)
        if message.strip().lower().startswith("/delete "):
            # Check if user is admin
            if "admin" not in user.group_memberships:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# 🔒 Access Denied\n\n"
                                "The `/delete` command is only available to administrators.\n\n"
                                "If you need access to memory management features, please contact your system administrator.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )
            memory_id = message.strip()[8:].strip()  # Extract ID after "/delete "
            return await self._delete_memory(agent, user, conversation, memory_id)

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

        # Check if user is admin (has 'admin' in group memberships)
        is_admin = "admin" in user.group_memberships

        # Generate single concise card
        if self.welcome_message:
            # Use custom welcome message
            return [
                UiComponent(
                    rich_component=RichTextComponent(
                        content=self.welcome_message, markdown=True
                    ),
                    simple_component=None,
                )
            ]
        else:
            # Generate role-aware welcome card
            return [self._generate_starter_card(setup_analysis, is_admin)]

    def _generate_starter_card(
        self, analysis: Dict[str, Any], is_admin: bool
    ) -> UiComponent:
        """Generate a single concise starter card based on role and setup status."""

        if is_admin:
            # Admin view: includes setup status and memory management
            return self._generate_admin_starter_card(analysis)
        else:
            # User view: simple welcome message
            return self._generate_user_starter_card(analysis)

    def _generate_admin_starter_card(self, analysis: Dict[str, Any]) -> UiComponent:
        """Generate admin starter card with setup info and memory management."""

        # Build concise content
        if not analysis["has_sql"]:
            title = "Admin: Setup Required"
            content = "**🔒 Admin View** - You have admin privileges and will see additional system information.\n\n**thaink² AI** requires a SQL connection to function.\n\nPlease configure a SQL tool to get started."
            status = "error"
            icon = "⚠️"
        elif analysis["is_complete"]:
            title = "Admin: System Ready"
            content = "**🔒 Admin View** - You have admin privileges and will see additional system information.\n\n**thaink² AI** is fully configured and ready.\n\n"
            content += "**Setup:** SQL ✓ | Memory ✓ | Visualization ✓"
            status = "success"
            icon = "✅"
        else:
            title = "Admin: System Ready"
            content = "**🔒 Admin View** - You have admin privileges and will see additional system information.\n\n**thaink² AI** is ready to query your database.\n\n"
            setup_items = []
            setup_items.append("SQL ✓")
            setup_items.append("Memory ✓" if analysis["has_memory"] else "Memory ✗")
            setup_items.append("Viz ✓" if analysis["has_viz"] else "Viz ✗")
            content += f"**Setup:** {' | '.join(setup_items)}"
            status = "warning" if not analysis["has_memory"] else "success"
            icon = "⚠️" if not analysis["has_memory"] else "✅"

        # Add memory management info for admins
        actions: List[Dict[str, Any]] = []
        if analysis["has_sql"]:
            actions.append(
                {
                    "label": "💡 Help",
                    "action": "/help",
                    "variant": "secondary",
                }
            )

        if analysis["has_memory"]:
            content += "\n\n**Memory Management:** Tool and text memories are available. As an admin, you can view and manage these memories to help me learn from successful queries."
            actions.append(
                {
                    "label": "🧠 View Memories",
                    "action": "/memories",
                    "variant": "secondary",
                }
            )

        return UiComponent(
            rich_component=CardComponent(
                title=title,
                content=content,
                icon=icon,
                status=status,
                actions=actions,
                markdown=True,
            ),
            simple_component=None,
        )

    def _generate_user_starter_card(self, analysis: Dict[str, Any]) -> UiComponent:
        """Generate simple user starter view using RichTextComponent."""

        if not analysis["has_sql"]:
            content = (
                "# ⚠️ Setup Required\n\n"
                "thaink² AI requires configuration before it can help you analyze data."
            )
        else:
            content = (
                "# 👋 Welcome to thaink² AI\n\n"
                "I'm your AI data analyst assistant. Ask me anything about your data in plain English!\n\n"
                "Type `/help` to see what I can do."
            )

        return UiComponent(
            rich_component=RichTextComponent(content=content, markdown=True),
            simple_component=None,
        )

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

    def _generate_setup_status_cards(
        self, analysis: Dict[str, Any]
    ) -> List[UiComponent]:
        """Generate status cards showing setup health (used by /status command)."""

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

    def _generate_setup_guidance(
        self, analysis: Dict[str, Any]
    ) -> Optional[UiComponent]:
        """Generate setup guidance based on what's missing (used by /status command)."""

        if not analysis["has_sql"]:
            # Critical guidance - need SQL
            content = (
                "## 🚨 Setup Required\n\n"
                "To get started with thaink² AI, you need to configure a SQL connection tool:\n\n"
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
                "🎉 **Excellent!** Your thaink² AI setup is complete and optimized.\n\n"
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

            # Get both tool memories and text memories
            tool_memories = await agent.agent_memory.get_recent_memories(
                context=context, limit=10
            )

            # Try to get text memories (may not be implemented in all memory backends)
            text_memories = []
            try:
                text_memories = await agent.agent_memory.get_recent_text_memories(
                    context=context, limit=10
                )
            except (AttributeError, NotImplementedError):
                # Text memories not supported by this implementation
                pass

            if not tool_memories and not text_memories:
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

            components = []

            # Header
            total_count = len(tool_memories) + len(text_memories)
            header_content = f"# 🧠 Recent Memories\n\nFound {total_count} recent memor{'y' if total_count == 1 else 'ies'}"
            components.append(
                UiComponent(
                    rich_component=RichTextComponent(
                        content=header_content, markdown=True
                    ),
                    simple_component=None,
                )
            )

            # Display text memories
            if text_memories:
                components.append(
                    UiComponent(
                        rich_component=RichTextComponent(
                            content=f"## 📝 Text Memories ({len(text_memories)})",
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                )

                for memory in text_memories:
                    # Create card with delete button
                    card_content = f"**Content:** {memory.content}\n\n"
                    if memory.timestamp:
                        card_content += f"**Timestamp:** {memory.timestamp}\n\n"
                    card_content += f"**ID:** `{memory.memory_id}`"

                    card = CardComponent(
                        title="Text Memory",
                        content=card_content,
                        icon="📝",
                        actions=[
                            {
                                "label": "🗑️ Delete",
                                "action": f"/delete {memory.memory_id}",
                                "variant": "error",
                            }
                        ],
                    )
                    components.append(
                        UiComponent(rich_component=card, simple_component=None)
                    )

            # Display tool memories
            if tool_memories:
                components.append(
                    UiComponent(
                        rich_component=RichTextComponent(
                            content=f"## 🔧 Tool Memories ({len(tool_memories)})",
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                )

                for tool_memory in tool_memories:
                    # Create card with delete button
                    card_content = f"**Question:** {tool_memory.question}\n\n"
                    card_content += f"**Tool:** {tool_memory.tool_name}\n\n"
                    card_content += f"**Arguments:** `{tool_memory.args}`\n\n"
                    card_content += f"**Success:** {'✅ Yes' if tool_memory.success else '❌ No'}\n\n"
                    if tool_memory.timestamp:
                        card_content += f"**Timestamp:** {tool_memory.timestamp}\n\n"
                    card_content += f"**ID:** `{tool_memory.memory_id}`"

                    card = CardComponent(
                        title=f"Tool: {tool_memory.tool_name}",
                        content=card_content,
                        markdown=True,
                        icon="🔧",
                        status="success" if tool_memory.success else "error",
                        actions=[
                            {
                                "label": "🗑️ Delete",
                                "action": f"/delete {tool_memory.memory_id}",
                                "variant": "error",
                            }
                        ],
                    )
                    components.append(
                        UiComponent(rich_component=card, simple_component=None)
                    )

            return WorkflowResult(should_skip_llm=True, components=components)

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

    async def _delete_memory(
        self, agent: "Agent", user: "User", conversation: "Conversation", memory_id: str
    ) -> WorkflowResult:
        """Delete a memory by its ID."""
        try:
            # Check if agent has memory capability
            if not hasattr(agent, "agent_memory") or agent.agent_memory is None:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# ⚠️ No Memory System\n\n"
                                "Agent memory is not configured. Cannot delete memories.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )

            if not memory_id:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content="# ⚠️ Invalid Command\n\n"
                                "Please provide a memory ID to delete.\n\n"
                                "Usage: `/delete [memory_id]`",
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

            # Try to delete as a tool memory first
            deleted = await agent.agent_memory.delete_by_id(context, memory_id)

            # If not found as tool memory, try as text memory
            if not deleted:
                try:
                    deleted = await agent.agent_memory.delete_text_memory(
                        context, memory_id
                    )
                except (AttributeError, NotImplementedError):
                    # Text memory deletion not supported by this implementation
                    pass

            if deleted:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content=f"# ✅ Memory Deleted\n\n"
                                f"Successfully deleted memory with ID: `{memory_id}`\n\n"
                                f"You can view remaining memories using `/memories`.",
                                markdown=True,
                            ),
                            simple_component=None,
                        )
                    ],
                )
            else:
                return WorkflowResult(
                    should_skip_llm=True,
                    components=[
                        UiComponent(
                            rich_component=RichTextComponent(
                                content=f"# ❌ Memory Not Found\n\n"
                                f"Could not find memory with ID: `{memory_id}`\n\n"
                                f"Use `/memories` to see available memory IDs.",
                                markdown=True,
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
                            content=f"# ❌ Error Deleting Memory\n\n"
                            f"Failed to delete memory: {str(e)}\n\n"
                            f"This may indicate an issue with the agent memory configuration.",
                            markdown=True,
                        ),
                        simple_component=None,
                    )
                ],
            )
