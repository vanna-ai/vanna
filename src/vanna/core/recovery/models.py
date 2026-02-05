"""
Recovery action models for error handling.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RecoveryActionType(str, Enum):
    """Types of recovery actions."""

    RETRY = "retry"
    FAIL = "fail"
    FALLBACK = "fallback"
    SKIP = "skip"


class RecoveryAction(BaseModel):
    """Action to take when recovering from an error."""

    action: RecoveryActionType = Field(description="Type of recovery action")
    retry_delay_ms: Optional[int] = Field(
        default=None, description="Delay before retry in milliseconds"
    )
    fallback_value: Optional[Any] = Field(
        default=None, description="Fallback value to use"
    )
    message: Optional[str] = Field(
        default=None, description="Message to include with action"
    )
