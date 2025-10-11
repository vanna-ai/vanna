"""
SQL runner capability interface.

This module contains the abstract base class for SQL execution.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

from .models import RunSqlToolArgs

if TYPE_CHECKING:
    from vanna.core.tool import ToolContext


class SqlRunner(ABC):
    """Interface for SQL execution with different implementations."""

    @abstractmethod
    async def run_sql(self, args: RunSqlToolArgs, context: "ToolContext") -> pd.DataFrame:
        """Execute SQL query and return results as a DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            Exception: If query execution fails
        """
        pass
