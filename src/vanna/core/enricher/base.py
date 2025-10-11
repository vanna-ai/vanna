"""
Base context enricher interface.

Context enrichers allow you to add additional data to the ToolContext
before tools are executed.
"""

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tool.models import ToolContext


class ContextEnricher(ABC):
    """Enricher for adding data to ToolContext.

    Subclass this to create custom enrichers that can:
    - Add user preferences from database
    - Inject session state
    - Add temporal context (timezone, current date)
    - Include user history or profile data
    - Add environment-specific configuration

    Example:
        class UserPreferencesEnricher(ContextEnricher):
            def __init__(self, db):
                self.db = db

            async def enrich_context(self, context: ToolContext) -> ToolContext:
                # Fetch user preferences
                prefs = await self.db.get_user_preferences(context.user.id)

                # Add to context metadata
                context.metadata["preferences"] = prefs
                context.metadata["timezone"] = prefs.get("timezone", "UTC")

                return context

        agent = AgentRunner(
            llm_service=...,
            context_enrichers=[UserPreferencesEnricher(db), SessionEnricher()]
        )
    """

    async def enrich_context(self, context: "ToolContext") -> "ToolContext":
        """Enrich the tool execution context with additional data.

        Args:
            context: The tool context to enrich

        Returns:
            Enriched context (typically modified in-place)

        Note:
            Enrichers typically modify the context.metadata dict to add
            additional data that tools can access.
        """
        return context
