"""Apache Doris implementation of SqlRunner interface."""

import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class DorisRunner(SqlRunner):
    """Apache Doris implementation of the SqlRunner interface.

    Apache Doris is MySQL-compatible, so this implementation uses PyMySQL
    as the database driver with Doris-specific defaults (port 9030).
    """

    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 9030,
        **kwargs,
    ):
        """Initialize with Apache Doris connection parameters.

        Args:
            host: Database host address
            database: Database name
            user: Database user
            password: Database password
            port: Database port (default: 9030, Doris FE query port)
            **kwargs: Additional PyMySQL connection parameters
        """
        try:
            import pymysql.cursors

            self.pymysql = pymysql
        except ImportError as e:
            raise ImportError(
                "PyMySQL package is required. Install with: pip install 'vanna[doris]'"
            ) from e

        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.kwargs = kwargs

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against Apache Doris database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            pymysql.Error: If query execution fails
        """
        # Connect to the database
        conn = self.pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            cursorclass=self.pymysql.cursors.DictCursor,
            **self.kwargs,
        )

        try:
            # Ping to ensure connection is alive
            conn.ping(reconnect=True)

            cursor = conn.cursor()
            cursor.execute(args.sql)
            results = cursor.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(
                results,
                columns=[desc[0] for desc in cursor.description]
                if cursor.description
                else [],
            )

            cursor.close()
            return df

        finally:
            conn.close()
