"""SQLite implementation of SqlRunner interface."""
import sqlite3
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class SqliteRunner(SqlRunner):
    """SQLite implementation of the SqlRunner interface."""

    def __init__(self, database_path: str):
        """Initialize with a SQLite database path.

        Args:
            database_path: Path to the SQLite database file
        """
        self.database_path = database_path

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against SQLite database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            sqlite3.Error: If query execution fails
        """
        # Connect to the database
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        try:
            # Execute the query
            cursor.execute(args.sql)

            # Determine if this is a SELECT query or modification query
            query_type = args.sql.strip().upper().split()[0]

            if query_type == "SELECT":
                # Fetch results for SELECT queries
                rows = cursor.fetchall()
                if not rows:
                    # Return empty DataFrame
                    return pd.DataFrame()

                # Convert rows to list of dictionaries
                results_data = [dict(row) for row in rows]
                return pd.DataFrame(results_data)
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                rows_affected = cursor.rowcount
                # Return a DataFrame indicating rows affected
                return pd.DataFrame({'rows_affected': [rows_affected]})

        finally:
            cursor.close()
            conn.close()
