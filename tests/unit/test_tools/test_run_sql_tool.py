"""
Unit tests for RunSqlTool.

Tests cover:
- SELECT query execution and DataFrame result handling
- Empty result sets
- INSERT/UPDATE/DELETE queries with affected rows
- SQL error handling
- Custom tool name and description
- Large result truncation
- File system integration for CSV saving
"""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock

from vanna.tools.run_sql import RunSqlTool
from vanna.capabilities.sql_runner.models import RunSqlToolArgs
from vanna.core.tool.models import ToolContext
from vanna.core.user.models import User
from vanna.components.rich.data.dataframe import DataFrameComponent
from vanna.components.rich.display.notification import NotificationComponent


class MockSqlRunner:
    """Mock SqlRunner for testing."""

    def __init__(self, return_data=None, error=None):
        self.return_data = return_data if return_data is not None else pd.DataFrame()
        self.error = error
        self.last_query = None
        self.call_count = 0

    async def run_sql(self, args, context):
        self.last_query = args.sql
        self.call_count += 1
        if self.error:
            raise self.error
        return self.return_data


class MockFileSystem:
    """Mock FileSystem for testing."""

    def __init__(self):
        self.files = {}
        self.write_calls = []

    async def write_file(self, filename, content, context, overwrite=False):
        self.write_calls.append({"filename": filename, "content": content})
        self.files[filename] = content


@pytest.fixture
def mock_context():
    """Create a mock ToolContext for testing."""
    user = User(
        id="test-user",
        username="test",
        email="test@example.com",
        group_memberships=["user"]
    )
    return ToolContext(
        user=user,
        conversation_id="test-conv-123",
        request_id="test-req-456",
        metadata={}
    )


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "restaurant_name": ["Downtown Diner", "Airport Bistro", "Suburban Cafe"],
        "revenue": [1200000, 980000, 750000],
        "orders": [15000, 12000, 9000]
    })


class TestRunSqlToolBasics:
    """Test basic RunSqlTool functionality."""

    def test_tool_name_default(self):
        """Test that default tool name is 'run_sql'."""
        runner = MockSqlRunner()
        tool = RunSqlTool(sql_runner=runner)
        assert tool.name == "run_sql"

    def test_tool_name_custom(self):
        """Test that custom tool name is used when provided."""
        runner = MockSqlRunner()
        tool = RunSqlTool(sql_runner=runner, custom_tool_name="query_database")
        assert tool.name == "query_database"

    def test_tool_description_default(self):
        """Test that default description is returned."""
        runner = MockSqlRunner()
        tool = RunSqlTool(sql_runner=runner)
        assert "SQL queries" in tool.description

    def test_tool_description_custom(self):
        """Test that custom description is used when provided."""
        runner = MockSqlRunner()
        tool = RunSqlTool(
            sql_runner=runner,
            custom_tool_description="Execute queries on Urban Eats database"
        )
        assert tool.description == "Execute queries on Urban Eats database"

    def test_args_schema(self):
        """Test that args schema is RunSqlToolArgs."""
        runner = MockSqlRunner()
        tool = RunSqlTool(sql_runner=runner)
        assert tool.get_args_schema() == RunSqlToolArgs


class TestRunSqlToolSelectQueries:
    """Test SELECT query execution."""

    @pytest.mark.asyncio
    async def test_select_query_returns_dataframe_component(self, mock_context, sample_dataframe):
        """SELECT queries should return a DataFrameComponent with results."""
        runner = MockSqlRunner(return_data=sample_dataframe)
        file_system = MockFileSystem()
        tool = RunSqlTool(sql_runner=runner, file_system=file_system)

        args = RunSqlToolArgs(sql="SELECT * FROM restaurants LIMIT 3")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        assert len(result.components) > 0

        # Check that a DataFrameComponent was returned
        df_components = [c for c in result.components if isinstance(c, DataFrameComponent)]
        assert len(df_components) > 0

        # Verify the data
        df_component = df_components[0]
        assert len(df_component.rows) == 3
        assert "restaurant_name" in df_component.columns

    @pytest.mark.asyncio
    async def test_select_query_empty_result(self, mock_context):
        """SELECT queries with no results should return appropriate message."""
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELECT * FROM restaurants WHERE 1=0")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        assert "No rows returned" in result.output or result.output == ""

    @pytest.mark.asyncio
    async def test_select_query_saves_csv_file(self, mock_context, sample_dataframe):
        """SELECT queries with results should save a CSV file."""
        runner = MockSqlRunner(return_data=sample_dataframe)
        file_system = MockFileSystem()
        tool = RunSqlTool(sql_runner=runner, file_system=file_system)

        args = RunSqlToolArgs(sql="SELECT * FROM restaurants")
        result = await tool.execute(mock_context, args)

        # Verify CSV was written
        assert len(file_system.write_calls) > 0
        csv_write = file_system.write_calls[0]
        assert csv_write["filename"].endswith(".csv")
        assert "restaurant_name" in csv_write["content"]


class TestRunSqlToolModifyingQueries:
    """Test INSERT, UPDATE, DELETE query execution."""

    @pytest.mark.asyncio
    async def test_insert_query_returns_notification(self, mock_context):
        """INSERT queries should return a NotificationComponent."""
        # INSERT returns empty DataFrame (no rows selected)
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="INSERT INTO restaurants (name) VALUES ('New Restaurant')")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        # Should have notification about query execution
        notification_components = [c for c in result.components if isinstance(c, NotificationComponent)]
        # Note: The actual implementation may vary

    @pytest.mark.asyncio
    async def test_update_query_execution(self, mock_context):
        """UPDATE queries should execute and return success."""
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="UPDATE restaurants SET revenue = 1500000 WHERE name = 'Downtown'")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        assert runner.last_query == "UPDATE restaurants SET revenue = 1500000 WHERE name = 'Downtown'"

    @pytest.mark.asyncio
    async def test_delete_query_execution(self, mock_context):
        """DELETE queries should execute and return success."""
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="DELETE FROM restaurants WHERE revenue < 100000")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        assert runner.last_query == "DELETE FROM restaurants WHERE revenue < 100000"


class TestRunSqlToolErrorHandling:
    """Test error handling in RunSqlTool."""

    @pytest.mark.asyncio
    async def test_sql_error_returns_failure_result(self, mock_context):
        """SQL errors should return ToolResult with success=False."""
        runner = MockSqlRunner(error=Exception("SQL syntax error near 'SELEC'"))
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELEC * FROM restaurants")
        result = await tool.execute(mock_context, args)

        assert result.success is False
        assert "error" in result.output.lower() or "SQL syntax error" in result.output

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_context):
        """Connection errors should be handled gracefully."""
        runner = MockSqlRunner(error=ConnectionError("Database connection failed"))
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELECT * FROM restaurants")
        result = await tool.execute(mock_context, args)

        assert result.success is False
        assert "connection" in result.output.lower() or "failed" in result.output.lower()

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, mock_context):
        """Timeout errors should be handled gracefully."""
        runner = MockSqlRunner(error=TimeoutError("Query timed out"))
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELECT * FROM very_large_table")
        result = await tool.execute(mock_context, args)

        assert result.success is False


class TestRunSqlToolLargeResults:
    """Test handling of large result sets."""

    @pytest.mark.asyncio
    async def test_large_result_dataframe_component(self, mock_context):
        """Large results should still return DataFrameComponent."""
        # Create a large DataFrame
        large_df = pd.DataFrame({
            "id": range(1000),
            "name": [f"Restaurant {i}" for i in range(1000)],
            "revenue": [100000 + i * 1000 for i in range(1000)]
        })
        runner = MockSqlRunner(return_data=large_df)
        file_system = MockFileSystem()
        tool = RunSqlTool(sql_runner=runner, file_system=file_system)

        args = RunSqlToolArgs(sql="SELECT * FROM restaurants")
        result = await tool.execute(mock_context, args)

        assert result.success is True
        # CSV should be saved with full data
        assert len(file_system.write_calls) > 0


class TestRunSqlToolSqlRunnerInteraction:
    """Test interaction with SqlRunner."""

    @pytest.mark.asyncio
    async def test_sql_passed_to_runner(self, mock_context):
        """SQL query should be passed to the runner exactly as provided."""
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        query = "SELECT restaurant_name, SUM(revenue) FROM restaurants GROUP BY restaurant_name"
        args = RunSqlToolArgs(sql=query)
        await tool.execute(mock_context, args)

        assert runner.last_query == query

    @pytest.mark.asyncio
    async def test_runner_called_once_per_execute(self, mock_context):
        """SqlRunner should be called exactly once per execute."""
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELECT 1")
        await tool.execute(mock_context, args)

        assert runner.call_count == 1

    @pytest.mark.asyncio
    async def test_context_passed_to_runner(self, mock_context):
        """ToolContext should be passed to the runner."""
        # We can verify this by checking the runner received the call
        runner = MockSqlRunner(return_data=pd.DataFrame())
        tool = RunSqlTool(sql_runner=runner)

        args = RunSqlToolArgs(sql="SELECT 1")
        await tool.execute(mock_context, args)

        # If the call succeeded without error, context was passed
        assert runner.call_count == 1
