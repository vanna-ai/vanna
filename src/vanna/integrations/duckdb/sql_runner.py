"""DuckDB implementation of SqlRunner interface."""
from typing import Optional
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class DuckDBRunner(SqlRunner):
    """DuckDB implementation of the SqlRunner interface."""

    def __init__(
        self,
        database_path: str = ":memory:",
        init_sql: Optional[str] = None,
        **kwargs
    ):
        """Initialize with DuckDB connection parameters.

        Args:
            database_path: Path to the DuckDB database file.
                          Use ":memory:" for in-memory database (default).
                          Use "md:" or "motherduck:" for MotherDuck database.
            init_sql: Optional SQL to run when connecting to the database
            **kwargs: Additional duckdb connection parameters
        """
        try:
            import duckdb
            self.duckdb = duckdb
        except ImportError as e:
            raise ImportError(
                "duckdb package is required. Install with: pip install 'vanna[duckdb]'"
            ) from e

        self.database_path = database_path
        self.init_sql = init_sql
        self.kwargs = kwargs
        self._conn = None

    def _get_connection(self):
        """Get or create DuckDB connection."""
        if self._conn is None:
            self._conn = self.duckdb.connect(self.database_path, **self.kwargs)
            if self.init_sql:
                self._conn.query(self.init_sql)
        return self._conn

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against DuckDB database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            duckdb.Error: If query execution fails
        """
        conn = self._get_connection()

        # Execute the query and convert to DataFrame
        df = conn.query(args.sql).to_df()

        return df
