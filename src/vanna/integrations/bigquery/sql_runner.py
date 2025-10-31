"""BigQuery implementation of SqlRunner interface."""
from typing import Optional
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class BigQueryRunner(SqlRunner):
    """BigQuery implementation of the SqlRunner interface."""

    def __init__(
        self,
        project_id: str,
        cred_file_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize with BigQuery connection parameters.

        Args:
            project_id: Google Cloud Project ID
            cred_file_path: Path to Google Cloud credentials JSON file (optional)
            **kwargs: Additional google.cloud.bigquery.Client parameters
        """
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
            self.bigquery = bigquery
            self.service_account = service_account
        except ImportError as e:
            raise ImportError(
                "google-cloud-bigquery package is required. "
                "Install with: pip install 'vanna[bigquery]'"
            ) from e

        self.project_id = project_id
        self.cred_file_path = cred_file_path
        self.kwargs = kwargs
        self._client = None

    def _get_client(self):
        """Get or create BigQuery client."""
        if self._client is not None:
            return self._client

        if self.cred_file_path:
            import json
            with open(self.cred_file_path, "r") as f:
                credentials = self.service_account.Credentials.from_service_account_info(
                    json.loads(f.read()),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            self._client = self.bigquery.Client(
                project=self.project_id,
                credentials=credentials,
                **self.kwargs
            )
        else:
            # Use default credentials
            self._client = self.bigquery.Client(project=self.project_id, **self.kwargs)

        return self._client

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against BigQuery database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            google.api_core.exceptions.GoogleAPIError: If query execution fails
        """
        client = self._get_client()

        # Execute the query
        job = client.query(args.sql)
        df = job.result().to_dataframe()

        return df
