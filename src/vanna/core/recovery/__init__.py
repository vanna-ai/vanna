"""
Error recovery system for handling failures gracefully.

This module provides interfaces for custom error handling, retry logic,
and fallback strategies.
"""

from .base import ErrorRecoveryStrategy
from .models import RecoveryAction, RecoveryActionType

__all__ = ["ErrorRecoveryStrategy", "RecoveryAction", "RecoveryActionType"]
