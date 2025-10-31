"""Presto implementation of SqlRunner interface."""
from typing import Optional
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class PrestoRunner(SqlRunner):
    """Presto implementation of the SqlRunner interface."""

    def __init__(
        self,
        host: str,
        catalog: str = 'hive',
        schema: str = 'default',
        user: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 443,
        combined_pem_path: Optional[str] = None,
        protocol: str = 'https',
        requests_kwargs: Optional[dict] = None,
        **kwargs
    ):
        """Initialize with Presto connection parameters.

        Args:
            host: The host address of the Presto database
            catalog: The catalog to use in the Presto environment (default: 'hive')
            schema: The schema to use in the Presto environment (default: 'default')
            user: The username for authentication
            password: The password for authentication
            port: The port number for the Presto connection (default: 443)
            combined_pem_path: The path to the combined pem file for SSL connection
            protocol: The protocol to use for the connection (default: 'https')
            requests_kwargs: Additional keyword arguments for requests
            **kwargs: Additional pyhive connection parameters
        """
        try:
            from pyhive import presto
            self.presto = presto
        except ImportError as e:
            raise ImportError(
                "pyhive package is required. Install with: pip install pyhive"
            ) from e

        self.host = host
        self.catalog = catalog
        self.schema = schema
        self.user = user
        self.password = password
        self.port = port
        self.protocol = protocol
        self.kwargs = kwargs

        # Set up requests_kwargs for SSL if combined_pem_path is provided
        if requests_kwargs is None and combined_pem_path is not None:
            self.requests_kwargs = {'verify': combined_pem_path}
        else:
            self.requests_kwargs = requests_kwargs

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against Presto database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            presto.Error: If query execution fails
        """
        # Connect to the database
        conn = self.presto.Connection(
            host=self.host,
            username=self.user,
            password=self.password,
            catalog=self.catalog,
            schema=self.schema,
            port=self.port,
            protocol=self.protocol,
            requests_kwargs=self.requests_kwargs,
            **self.kwargs
        )

        try:
            # Strip and remove trailing semicolons (Presto doesn't like them)
            sql = args.sql.rstrip()
            if sql.endswith(';'):
                sql = sql[:-1]

            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])

            cursor.close()
            return df

        finally:
            conn.close()
