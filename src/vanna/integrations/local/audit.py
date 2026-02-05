"""
Local audit logger implementation using Python logging.

This module provides a simple audit logger that writes events using
the standard Python logging module, useful for development and testing.
"""

import json
import logging
from typing import Optional

from vanna.core.audit import AuditEvent, AuditLogger

logger = logging.getLogger(__name__)


class LoggingAuditLogger(AuditLogger):
    """Audit logger that writes events to Python logger as structured JSON.

    This implementation uses logger.info() to emit audit events as JSON,
    making them easy to parse and route to log aggregation systems.

    Example:
        audit_logger = LoggingAuditLogger()
        agent = Agent(
            llm_service=...,
            audit_logger=audit_logger
        )
    """

    def __init__(self, log_level: int = logging.INFO):
        """Initialize the logging audit logger.

        Args:
            log_level: Log level to use for audit events (default: INFO)
        """
        self.log_level = log_level

    async def log_event(self, event: AuditEvent) -> None:
        """Log an audit event as structured JSON.

        Args:
            event: The audit event to log
        """
        try:
            # Convert event to dict for JSON serialization
            event_dict = event.model_dump(mode="json", exclude_none=True)

            # Format as single-line JSON for easy parsing
            event_json = json.dumps(event_dict, separators=(",", ":"))

            # Log with structured prefix for easy filtering
            logger.log(
                self.log_level,
                f"[AUDIT] {event.event_type.value} | {event_json}",
            )
        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to log audit event: {e}", exc_info=True)
