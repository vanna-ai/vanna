"""Snowflake implementation of SqlRunner interface."""
from typing import Optional, Union
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class SnowflakeRunner(SqlRunner):
    """Snowflake implementation of the SqlRunner interface."""

    def __init__(
        self,
        account: str,
        username: str,
        password: str,
        database: str,
        role: Optional[str] = None,
        warehouse: Optional[str] = None,
        **kwargs
    ):
        """Initialize with Snowflake connection parameters.

        Args:
            account: Snowflake account identifier
            username: Database user
            password: Database password
            database: Database name
            role: Snowflake role to use (optional)
            warehouse: Snowflake warehouse to use (optional)
            **kwargs: Additional snowflake.connector connection parameters
        """
        try:
            import snowflake.connector
            self.snowflake = snowflake.connector
        except ImportError as e:
            raise ImportError(
                "snowflake-connector-python package is required. "
                "Install with: pip install 'vanna[snowflake]'"
            ) from e

        self.account = account
        self.username = username
        self.password = password
        self.database = database
        self.role = role
        self.warehouse = warehouse
        self.kwargs = kwargs

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against Snowflake database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            snowflake.connector.Error: If query execution fails
        """
        # Connect to the database
        conn = self.snowflake.connect(
            user=self.username,
            password=self.password,
            account=self.account,
            database=self.database,
            client_session_keep_alive=True,
            **self.kwargs
        )

        cursor = conn.cursor()

        try:
            # Set role if specified
            if self.role:
                cursor.execute(f"USE ROLE {self.role}")

            # Set warehouse if specified
            if self.warehouse:
                cursor.execute(f"USE WAREHOUSE {self.warehouse}")

            # Use the specified database
            cursor.execute(f"USE DATABASE {self.database}")

            # Execute the query
            cursor.execute(args.sql)
            results = cursor.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
            return df

        finally:
            cursor.close()
            conn.close()
