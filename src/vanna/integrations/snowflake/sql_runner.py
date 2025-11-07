"""Snowflake implementation of SqlRunner interface."""

from typing import Optional, Union
import os
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class SnowflakeRunner(SqlRunner):
    """Snowflake implementation of the SqlRunner interface."""

    def __init__(
        self,
        account: str,
        username: str,
        password: Optional[str] = None,
        database: str = "",
        role: Optional[str] = None,
        warehouse: Optional[str] = None,
        private_key_path: Optional[str] = None,
        private_key_passphrase: Optional[str] = None,
        private_key_content: Optional[bytes] = None,
        **kwargs,
    ):
        """Initialize with Snowflake connection parameters.

        Args:
            account: Snowflake account identifier
            username: Database user
            password: Database password (optional if using key-pair auth)
            database: Database name
            role: Snowflake role to use (optional)
            warehouse: Snowflake warehouse to use (optional)
            private_key_path: Path to private key file for RSA key-pair authentication (optional)
            private_key_passphrase: Passphrase for encrypted private key (optional)
            private_key_content: Private key content as bytes (optional, alternative to private_key_path)
            **kwargs: Additional snowflake.connector connection parameters

        Note:
            Either password OR private_key_path/private_key_content must be provided.
            RSA key-pair authentication is recommended for production systems as Snowflake
            is deprecating user/password authentication.
        """
        try:
            import snowflake.connector

            self.snowflake = snowflake.connector
        except ImportError as e:
            raise ImportError(
                "snowflake-connector-python package is required. "
                "Install with: pip install 'vanna[snowflake]'"
            ) from e

        # Validate that at least one authentication method is provided
        if not password and not private_key_path and not private_key_content:
            raise ValueError(
                "Either password or private_key_path/private_key_content must be provided for authentication"
            )

        # Validate private key path exists if provided
        if private_key_path and not os.path.isfile(private_key_path):
            raise FileNotFoundError(f"Private key file not found: {private_key_path}")

        self.account = account
        self.username = username
        self.password = password
        self.database = database
        self.role = role
        self.warehouse = warehouse
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.private_key_content = private_key_content
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
        # Build connection parameters
        conn_params = {
            "user": self.username,
            "account": self.account,
            "client_session_keep_alive": True,
        }

        # Add database if specified
        if self.database:
            conn_params["database"] = self.database

        # Configure authentication method
        if self.private_key_path or self.private_key_content:
            # Use RSA key-pair authentication
            if self.private_key_path:
                conn_params["private_key_path"] = self.private_key_path
            else:
                conn_params["private_key_content"] = self.private_key_content

            # Add passphrase if provided
            if self.private_key_passphrase:
                conn_params["private_key_passphrase"] = self.private_key_passphrase
        else:
            # Use password authentication (fallback)
            conn_params["password"] = self.password

        # Add any additional kwargs
        conn_params.update(self.kwargs)

        # Connect to the database
        conn = self.snowflake.connect(**conn_params)

        cursor = conn.cursor()

        try:
            # Set role if specified
            if self.role:
                cursor.execute(f"USE ROLE {self.role}")

            # Set warehouse if specified
            if self.warehouse:
                cursor.execute(f"USE WAREHOUSE {self.warehouse}")

            # Use the specified database if provided
            if self.database:
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
