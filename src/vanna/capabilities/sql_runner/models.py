"""
SQL runner capability models.

This module contains data models for SQL execution.
"""

from pydantic import BaseModel, Field


class RunSqlToolArgs(BaseModel):
    """Arguments for run_sql tool."""

    sql: str = Field(description="SQL query to execute")
