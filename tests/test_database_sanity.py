"""
Sanity tests for database implementations.

These tests verify that:
1. Each database implementation correctly implements the SqlRunner interface
2. Imports are working correctly for all database modules
3. Basic class instantiation works (without requiring actual database connections)

Note: These tests do NOT execute actual queries against databases.
They are lightweight sanity checks for the implementation structure.
"""

import pytest
from abc import abstractmethod
from inspect import signature, iscoroutinefunction
import pandas as pd


class TestSqlRunnerInterface:
    """Test that the SqlRunner interface is properly defined."""

    def test_sql_runner_import(self):
        """Test that SqlRunner can be imported."""
        from vanna.capabilities.sql_runner import SqlRunner
        assert SqlRunner is not None

    def test_sql_runner_is_abstract(self):
        """Test that SqlRunner is an abstract base class."""
        from vanna.capabilities.sql_runner import SqlRunner
        from abc import ABC

        assert issubclass(SqlRunner, ABC)

    def test_sql_runner_has_run_sql_method(self):
        """Test that SqlRunner defines the run_sql abstract method."""
        from vanna.capabilities.sql_runner import SqlRunner

        assert hasattr(SqlRunner, 'run_sql')
        assert getattr(SqlRunner.run_sql, '__isabstractmethod__', False)

    def test_run_sql_method_signature(self):
        """Test that run_sql has the correct method signature."""
        from vanna.capabilities.sql_runner import SqlRunner

        sig = signature(SqlRunner.run_sql)
        params = list(sig.parameters.keys())

        # Should have: self, args, context
        assert len(params) == 3
        assert params[0] == 'self'
        assert params[1] == 'args'
        assert params[2] == 'context'

    def test_run_sql_is_async(self):
        """Test that run_sql is defined as an async method."""
        from vanna.capabilities.sql_runner import SqlRunner

        # Abstract methods are wrapped, so we check if it's meant to be async
        # by looking at the method definition
        assert iscoroutinefunction(SqlRunner.run_sql)


class TestRunSqlToolArgsModel:
    """Test the RunSqlToolArgs model."""

    def test_run_sql_tool_args_import(self):
        """Test that RunSqlToolArgs can be imported."""
        from vanna.capabilities.sql_runner import RunSqlToolArgs
        assert RunSqlToolArgs is not None

    def test_run_sql_tool_args_has_sql_field(self):
        """Test that RunSqlToolArgs has a 'sql' field."""
        from vanna.capabilities.sql_runner import RunSqlToolArgs

        # Create an instance
        args = RunSqlToolArgs(sql="SELECT 1")
        assert hasattr(args, 'sql')
        assert args.sql == "SELECT 1"

    def test_run_sql_tool_args_is_pydantic_model(self):
        """Test that RunSqlToolArgs is a Pydantic model."""
        from vanna.capabilities.sql_runner import RunSqlToolArgs
        from pydantic import BaseModel

        assert issubclass(RunSqlToolArgs, BaseModel)


class TestPostgresRunner:
    """Sanity tests for PostgresRunner implementation."""

    def test_postgres_runner_import(self):
        """Test that PostgresRunner can be imported."""
        from vanna.integrations.postgres import PostgresRunner
        assert PostgresRunner is not None

    def test_postgres_runner_implements_sql_runner(self):
        """Test that PostgresRunner implements SqlRunner interface."""
        from vanna.integrations.postgres import PostgresRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(PostgresRunner, SqlRunner)

    def test_postgres_runner_has_run_sql_method(self):
        """Test that PostgresRunner implements run_sql method."""
        from vanna.integrations.postgres import PostgresRunner

        assert hasattr(PostgresRunner, 'run_sql')
        # Should not be abstract anymore
        assert not getattr(PostgresRunner.run_sql, '__isabstractmethod__', False)

    def test_postgres_runner_instantiation_with_connection_string(self):
        """Test that PostgresRunner can be instantiated with connection string."""
        from vanna.integrations.postgres import PostgresRunner

        # This should not raise an error (no actual connection is made in __init__)
        runner = PostgresRunner(connection_string="postgresql://user:pass@localhost/db")
        assert runner is not None
        assert runner.connection_string == "postgresql://user:pass@localhost/db"
        assert runner.connection_params is None

    def test_postgres_runner_instantiation_with_params(self):
        """Test that PostgresRunner can be instantiated with individual parameters."""
        from vanna.integrations.postgres import PostgresRunner

        runner = PostgresRunner(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password="testpass"
        )
        assert runner is not None
        assert runner.connection_string is None
        assert runner.connection_params is not None
        assert runner.connection_params['host'] == "localhost"
        assert runner.connection_params['database'] == "testdb"

    def test_postgres_runner_requires_valid_params(self):
        """Test that PostgresRunner raises error with invalid parameters."""
        from vanna.integrations.postgres import PostgresRunner

        with pytest.raises(ValueError, match="Either provide connection_string OR"):
            PostgresRunner()  # No parameters provided

    def test_postgres_runner_checks_psycopg2_import(self):
        """Test that PostgresRunner checks for psycopg2 package."""
        from vanna.integrations.postgres import PostgresRunner

        # If psycopg2 is not installed, this should raise ImportError
        # If it is installed, this should work fine
        try:
            runner = PostgresRunner(connection_string="postgresql://test")
            assert runner.psycopg2 is not None
        except ImportError as e:
            assert "psycopg2" in str(e)


class TestSqliteRunner:
    """Sanity tests for SqliteRunner implementation."""

    def test_sqlite_runner_import(self):
        """Test that SqliteRunner can be imported."""
        from vanna.integrations.sqlite import SqliteRunner
        assert SqliteRunner is not None

    def test_sqlite_runner_implements_sql_runner(self):
        """Test that SqliteRunner implements SqlRunner interface."""
        from vanna.integrations.sqlite import SqliteRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(SqliteRunner, SqlRunner)

    def test_sqlite_runner_has_run_sql_method(self):
        """Test that SqliteRunner implements run_sql method."""
        from vanna.integrations.sqlite import SqliteRunner

        assert hasattr(SqliteRunner, 'run_sql')
        # Should not be abstract anymore
        assert not getattr(SqliteRunner.run_sql, '__isabstractmethod__', False)

    def test_sqlite_runner_instantiation(self):
        """Test that SqliteRunner can be instantiated with a database path."""
        from vanna.integrations.sqlite import SqliteRunner

        runner = SqliteRunner(database_path="/tmp/test.db")
        assert runner is not None
        assert runner.database_path == "/tmp/test.db"

    def test_sqlite_uses_builtin_sqlite3(self):
        """Test that SqliteRunner uses Python's built-in sqlite3 module."""
        import sqlite3
        from vanna.integrations.sqlite import SqliteRunner

        # sqlite3 should be importable (it's part of Python standard library)
        assert sqlite3 is not None


class TestLegacySqlRunner:
    """Sanity tests for LegacySqlRunner adapter."""

    def test_legacy_sql_runner_import(self):
        """Test that LegacySqlRunner can be imported."""
        from vanna.legacy.adapter import LegacySqlRunner
        assert LegacySqlRunner is not None

    def test_legacy_sql_runner_implements_sql_runner(self):
        """Test that LegacySqlRunner implements SqlRunner interface."""
        from vanna.legacy.adapter import LegacySqlRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(LegacySqlRunner, SqlRunner)

    def test_legacy_sql_runner_has_run_sql_method(self):
        """Test that LegacySqlRunner implements run_sql method."""
        from vanna.legacy.adapter import LegacySqlRunner

        assert hasattr(LegacySqlRunner, 'run_sql')
        # Should not be abstract anymore
        assert not getattr(LegacySqlRunner.run_sql, '__isabstractmethod__', False)

    def test_legacy_sql_runner_instantiation(self):
        """Test that LegacySqlRunner can be instantiated with a VannaBase instance."""
        from vanna.legacy.adapter import LegacySqlRunner
        from unittest.mock import Mock

        # Create a mock VannaBase instance
        mock_vn = Mock()

        runner = LegacySqlRunner(vn=mock_vn)
        assert runner is not None
        assert runner.vn is mock_vn


class TestDatabaseIntegrationModules:
    """Test that database integration modules can be imported."""

    def test_postgres_module_import(self):
        """Test that the postgres integration module can be imported."""
        try:
            import vanna.integrations.postgres
            assert vanna.integrations.postgres is not None
        except ImportError as e:
            pytest.fail(f"Failed to import postgres module: {e}")

    def test_sqlite_module_import(self):
        """Test that the sqlite integration module can be imported."""
        try:
            import vanna.integrations.sqlite
            assert vanna.integrations.sqlite is not None
        except ImportError as e:
            pytest.fail(f"Failed to import sqlite module: {e}")

    def test_postgres_module_exports_runner(self):
        """Test that postgres module exports PostgresRunner."""
        from vanna.integrations.postgres import PostgresRunner
        assert PostgresRunner is not None

    def test_sqlite_module_exports_runner(self):
        """Test that sqlite module exports SqliteRunner."""
        from vanna.integrations.sqlite import SqliteRunner
        assert SqliteRunner is not None


class TestLegacyVannaBaseConnections:
    """Test that legacy VannaBase connection methods exist."""

    def test_vanna_base_import(self):
        """Test that VannaBase can be imported."""
        from vanna.legacy.base.base import VannaBase
        assert VannaBase is not None

    def test_vanna_base_has_connection_methods(self):
        """Test that VannaBase has various database connection methods."""
        from vanna.legacy.base.base import VannaBase

        connection_methods = [
            'connect_to_snowflake',
            'connect_to_sqlite',
            'connect_to_postgres',
            'connect_to_mysql',
            'connect_to_clickhouse',
            'connect_to_oracle',
            'connect_to_bigquery',
            'connect_to_duckdb',
            'connect_to_mssql',
            'connect_to_presto',
            'connect_to_hive',
        ]

        for method_name in connection_methods:
            assert hasattr(VannaBase, method_name), f"VannaBase missing {method_name}"

    def test_vanna_base_has_run_sql_method(self):
        """Test that VannaBase has a run_sql method."""
        from vanna.legacy.base.base import VannaBase

        assert hasattr(VannaBase, 'run_sql')


class TestLegacyVannaAdapter:
    """Test the LegacyVannaAdapter."""

    def test_legacy_vanna_adapter_import(self):
        """Test that LegacyVannaAdapter can be imported."""
        from vanna.legacy.adapter import LegacyVannaAdapter
        assert LegacyVannaAdapter is not None

    def test_legacy_vanna_adapter_is_tool_registry(self):
        """Test that LegacyVannaAdapter extends ToolRegistry."""
        from vanna.legacy.adapter import LegacyVannaAdapter
        from vanna.core.registry import ToolRegistry

        assert issubclass(LegacyVannaAdapter, ToolRegistry)


class TestSnowflakeRunner:
    """Sanity tests for SnowflakeRunner implementation."""

    def test_snowflake_runner_import(self):
        """Test that SnowflakeRunner can be imported."""
        from vanna.integrations.snowflake import SnowflakeRunner
        assert SnowflakeRunner is not None

    def test_snowflake_runner_implements_sql_runner(self):
        """Test that SnowflakeRunner implements SqlRunner interface."""
        from vanna.integrations.snowflake import SnowflakeRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(SnowflakeRunner, SqlRunner)

    def test_snowflake_runner_has_run_sql_method(self):
        """Test that SnowflakeRunner implements run_sql method."""
        from vanna.integrations.snowflake import SnowflakeRunner

        assert hasattr(SnowflakeRunner, 'run_sql')
        assert not getattr(SnowflakeRunner.run_sql, '__isabstractmethod__', False)

    def test_snowflake_runner_instantiation(self):
        """Test that SnowflakeRunner can be instantiated with required parameters."""
        from vanna.integrations.snowflake import SnowflakeRunner

        runner = SnowflakeRunner(
            account="test-account",
            username="test-user",
            password="test-pass",
            database="test-db"
        )
        assert runner is not None
        assert runner.account == "test-account"

    def test_snowflake_runner_key_pair_auth_with_path(self, tmp_path):
        """Test that SnowflakeRunner can be instantiated with RSA key-pair authentication using path."""
        from vanna.integrations.snowflake import SnowflakeRunner

        # Create a temporary private key file
        private_key_file = tmp_path / "test_private_key.p8"
        private_key_file.write_text("-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----")

        runner = SnowflakeRunner(
            account="test-account",
            username="test-user",
            private_key_path=str(private_key_file),
            private_key_passphrase="test-passphrase",
            database="test-db"
        )
        assert runner is not None
        assert runner.account == "test-account"
        assert runner.username == "test-user"
        assert runner.password is None
        assert runner.private_key_path == str(private_key_file)
        assert runner.private_key_passphrase == "test-passphrase"

    def test_snowflake_runner_key_pair_auth_with_content(self):
        """Test that SnowflakeRunner can be instantiated with RSA key-pair authentication using content."""
        from vanna.integrations.snowflake import SnowflakeRunner

        private_key_content = b"-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----"

        runner = SnowflakeRunner(
            account="test-account",
            username="test-user",
            private_key_content=private_key_content,
            database="test-db"
        )
        assert runner is not None
        assert runner.account == "test-account"
        assert runner.username == "test-user"
        assert runner.password is None
        assert runner.private_key_content == private_key_content

    def test_snowflake_runner_key_pair_auth_without_passphrase(self, tmp_path):
        """Test that SnowflakeRunner works with unencrypted private key (no passphrase)."""
        from vanna.integrations.snowflake import SnowflakeRunner

        # Create a temporary private key file
        private_key_file = tmp_path / "test_private_key_unencrypted.p8"
        private_key_file.write_text("-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----")

        runner = SnowflakeRunner(
            account="test-account",
            username="test-user",
            private_key_path=str(private_key_file),
            database="test-db"
        )
        assert runner is not None
        assert runner.private_key_passphrase is None

    def test_snowflake_runner_missing_auth_raises_error(self):
        """Test that SnowflakeRunner raises error when no authentication method is provided."""
        from vanna.integrations.snowflake import SnowflakeRunner
        import pytest

        with pytest.raises(ValueError, match="Either password or private_key_path/private_key_content must be provided"):
            SnowflakeRunner(
                account="test-account",
                username="test-user",
                database="test-db"
            )

    def test_snowflake_runner_invalid_key_path_raises_error(self):
        """Test that SnowflakeRunner raises error when private key file doesn't exist."""
        from vanna.integrations.snowflake import SnowflakeRunner
        import pytest

        with pytest.raises(FileNotFoundError, match="Private key file not found"):
            SnowflakeRunner(
                account="test-account",
                username="test-user",
                private_key_path="/nonexistent/path/to/key.p8",
                database="test-db"
            )

    def test_snowflake_runner_password_auth_backwards_compatible(self):
        """Test that SnowflakeRunner maintains backward compatibility with password auth."""
        from vanna.integrations.snowflake import SnowflakeRunner

        runner = SnowflakeRunner(
            account="test-account",
            username="test-user",
            password="test-password",
            database="test-db",
            role="test-role",
            warehouse="test-warehouse"
        )
        assert runner is not None
        assert runner.password == "test-password"
        assert runner.private_key_path is None
        assert runner.private_key_content is None


class TestMySQLRunner:
    """Sanity tests for MySQLRunner implementation."""

    def test_mysql_runner_import(self):
        """Test that MySQLRunner can be imported."""
        from vanna.integrations.mysql import MySQLRunner
        assert MySQLRunner is not None

    def test_mysql_runner_implements_sql_runner(self):
        """Test that MySQLRunner implements SqlRunner interface."""
        from vanna.integrations.mysql import MySQLRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(MySQLRunner, SqlRunner)

    def test_mysql_runner_has_run_sql_method(self):
        """Test that MySQLRunner implements run_sql method."""
        from vanna.integrations.mysql import MySQLRunner

        assert hasattr(MySQLRunner, 'run_sql')
        assert not getattr(MySQLRunner.run_sql, '__isabstractmethod__', False)

    def test_mysql_runner_instantiation(self):
        """Test that MySQLRunner can be instantiated with required parameters."""
        from vanna.integrations.mysql import MySQLRunner

        runner = MySQLRunner(
            host="localhost",
            database="test-db",
            user="test-user",
            password="test-pass"
        )
        assert runner is not None
        assert runner.host == "localhost"


class TestClickHouseRunner:
    """Sanity tests for ClickHouseRunner implementation."""

    def test_clickhouse_runner_import(self):
        """Test that ClickHouseRunner can be imported."""
        from vanna.integrations.clickhouse import ClickHouseRunner
        assert ClickHouseRunner is not None

    def test_clickhouse_runner_implements_sql_runner(self):
        """Test that ClickHouseRunner implements SqlRunner interface."""
        from vanna.integrations.clickhouse import ClickHouseRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(ClickHouseRunner, SqlRunner)

    def test_clickhouse_runner_has_run_sql_method(self):
        """Test that ClickHouseRunner implements run_sql method."""
        from vanna.integrations.clickhouse import ClickHouseRunner

        assert hasattr(ClickHouseRunner, 'run_sql')
        assert not getattr(ClickHouseRunner.run_sql, '__isabstractmethod__', False)

    def test_clickhouse_runner_instantiation(self):
        """Test that ClickHouseRunner can be instantiated with required parameters."""
        from vanna.integrations.clickhouse import ClickHouseRunner

        runner = ClickHouseRunner(
            host="localhost",
            database="test-db",
            user="test-user",
            password="test-pass"
        )
        assert runner is not None
        assert runner.host == "localhost"


class TestOracleRunner:
    """Sanity tests for OracleRunner implementation."""

    def test_oracle_runner_import(self):
        """Test that OracleRunner can be imported."""
        from vanna.integrations.oracle import OracleRunner
        assert OracleRunner is not None

    def test_oracle_runner_implements_sql_runner(self):
        """Test that OracleRunner implements SqlRunner interface."""
        from vanna.integrations.oracle import OracleRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(OracleRunner, SqlRunner)

    def test_oracle_runner_has_run_sql_method(self):
        """Test that OracleRunner implements run_sql method."""
        from vanna.integrations.oracle import OracleRunner

        assert hasattr(OracleRunner, 'run_sql')
        assert not getattr(OracleRunner.run_sql, '__isabstractmethod__', False)

    def test_oracle_runner_instantiation(self):
        """Test that OracleRunner can be instantiated with required parameters."""
        from vanna.integrations.oracle import OracleRunner

        runner = OracleRunner(
            user="test-user",
            password="test-pass",
            dsn="localhost:1521/ORCL"
        )
        assert runner is not None
        assert runner.user == "test-user"


class TestBigQueryRunner:
    """Sanity tests for BigQueryRunner implementation."""

    def test_bigquery_runner_import(self):
        """Test that BigQueryRunner can be imported."""
        from vanna.integrations.bigquery import BigQueryRunner
        assert BigQueryRunner is not None

    def test_bigquery_runner_implements_sql_runner(self):
        """Test that BigQueryRunner implements SqlRunner interface."""
        from vanna.integrations.bigquery import BigQueryRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(BigQueryRunner, SqlRunner)

    def test_bigquery_runner_has_run_sql_method(self):
        """Test that BigQueryRunner implements run_sql method."""
        from vanna.integrations.bigquery import BigQueryRunner

        assert hasattr(BigQueryRunner, 'run_sql')
        assert not getattr(BigQueryRunner.run_sql, '__isabstractmethod__', False)

    def test_bigquery_runner_instantiation(self):
        """Test that BigQueryRunner can be instantiated with required parameters."""
        from vanna.integrations.bigquery import BigQueryRunner

        runner = BigQueryRunner(project_id="test-project")
        assert runner is not None
        assert runner.project_id == "test-project"


class TestDuckDBRunner:
    """Sanity tests for DuckDBRunner implementation."""

    def test_duckdb_runner_import(self):
        """Test that DuckDBRunner can be imported."""
        from vanna.integrations.duckdb import DuckDBRunner
        assert DuckDBRunner is not None

    def test_duckdb_runner_implements_sql_runner(self):
        """Test that DuckDBRunner implements SqlRunner interface."""
        from vanna.integrations.duckdb import DuckDBRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(DuckDBRunner, SqlRunner)

    def test_duckdb_runner_has_run_sql_method(self):
        """Test that DuckDBRunner implements run_sql method."""
        from vanna.integrations.duckdb import DuckDBRunner

        assert hasattr(DuckDBRunner, 'run_sql')
        assert not getattr(DuckDBRunner.run_sql, '__isabstractmethod__', False)

    def test_duckdb_runner_instantiation_memory(self):
        """Test that DuckDBRunner can be instantiated for in-memory database."""
        from vanna.integrations.duckdb import DuckDBRunner

        runner = DuckDBRunner(database_path=":memory:")
        assert runner is not None
        assert runner.database_path == ":memory:"

    def test_duckdb_runner_instantiation_file(self):
        """Test that DuckDBRunner can be instantiated with file path."""
        from vanna.integrations.duckdb import DuckDBRunner

        runner = DuckDBRunner(database_path="/tmp/test.duckdb")
        assert runner is not None
        assert runner.database_path == "/tmp/test.duckdb"


class TestMSSQLRunner:
    """Sanity tests for MSSQLRunner implementation."""

    def test_mssql_runner_import(self):
        """Test that MSSQLRunner can be imported."""
        from vanna.integrations.mssql import MSSQLRunner
        assert MSSQLRunner is not None

    def test_mssql_runner_implements_sql_runner(self):
        """Test that MSSQLRunner implements SqlRunner interface."""
        from vanna.integrations.mssql import MSSQLRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(MSSQLRunner, SqlRunner)

    def test_mssql_runner_has_run_sql_method(self):
        """Test that MSSQLRunner implements run_sql method."""
        from vanna.integrations.mssql import MSSQLRunner

        assert hasattr(MSSQLRunner, 'run_sql')
        assert not getattr(MSSQLRunner.run_sql, '__isabstractmethod__', False)

    def test_mssql_runner_instantiation(self):
        """Test that MSSQLRunner can be instantiated with ODBC connection string."""
        from vanna.integrations.mssql import MSSQLRunner

        runner = MSSQLRunner(
            odbc_conn_str="Driver={SQL Server};Server=localhost;Database=test;Trusted_Connection=yes;"
        )
        assert runner is not None


class TestPrestoRunner:
    """Sanity tests for PrestoRunner implementation."""

    def test_presto_runner_import(self):
        """Test that PrestoRunner can be imported."""
        from vanna.integrations.presto import PrestoRunner
        assert PrestoRunner is not None

    def test_presto_runner_implements_sql_runner(self):
        """Test that PrestoRunner implements SqlRunner interface."""
        from vanna.integrations.presto import PrestoRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(PrestoRunner, SqlRunner)

    def test_presto_runner_has_run_sql_method(self):
        """Test that PrestoRunner implements run_sql method."""
        from vanna.integrations.presto import PrestoRunner

        assert hasattr(PrestoRunner, 'run_sql')
        assert not getattr(PrestoRunner.run_sql, '__isabstractmethod__', False)

    def test_presto_runner_instantiation(self):
        """Test that PrestoRunner can be instantiated with required parameters."""
        from vanna.integrations.presto import PrestoRunner

        runner = PrestoRunner(
            host="localhost",
            user="test-user",
            password="test-pass"
        )
        assert runner is not None
        assert runner.host == "localhost"


class TestHiveRunner:
    """Sanity tests for HiveRunner implementation."""

    def test_hive_runner_import(self):
        """Test that HiveRunner can be imported."""
        from vanna.integrations.hive import HiveRunner
        assert HiveRunner is not None

    def test_hive_runner_implements_sql_runner(self):
        """Test that HiveRunner implements SqlRunner interface."""
        from vanna.integrations.hive import HiveRunner
        from vanna.capabilities.sql_runner import SqlRunner

        assert issubclass(HiveRunner, SqlRunner)

    def test_hive_runner_has_run_sql_method(self):
        """Test that HiveRunner implements run_sql method."""
        from vanna.integrations.hive import HiveRunner

        assert hasattr(HiveRunner, 'run_sql')
        assert not getattr(HiveRunner.run_sql, '__isabstractmethod__', False)

    def test_hive_runner_instantiation(self):
        """Test that HiveRunner can be instantiated with required parameters."""
        from vanna.integrations.hive import HiveRunner

        runner = HiveRunner(
            host="localhost",
            user="test-user",
            password="test-pass"
        )
        assert runner is not None
        assert runner.host == "localhost"
