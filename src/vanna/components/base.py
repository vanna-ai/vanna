"""
UI components base - re-exports UiComponent from core.

UiComponent lives in core/ because it's a fundamental return type for tools.
This module provides backward compatibility by re-exporting it here.
"""

# Re-export UiComponent from core for backward compatibility
from ..core.components import UiComponent

__all__ = ["UiComponent"]
