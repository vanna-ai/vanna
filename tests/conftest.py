"""
Pytest configuration and shared fixtures for Vanna v2 test suite.
"""

import os
import pytest
import sqlite3
from pathlib import Path

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "anthropic: marks tests requiring Anthropic API key"
    )
    config.addinivalue_line(
        "markers", "openai: marks tests requiring OpenAI API key"
    )
    config.addinivalue_line(
        "markers", "ollama: marks tests requiring Ollama"
    )
    config.addinivalue_line(
        "markers", "chromadb: marks tests requiring ChromaDB"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests if required API keys are missing."""
    for item in items:
        # Skip Anthropic tests if no API key
        if "anthropic" in item.keywords:
            if not os.getenv("ANTHROPIC_API_KEY"):
                item.add_marker(
                    pytest.mark.skip(reason="ANTHROPIC_API_KEY environment variable not set")
                )

        # Skip OpenAI tests if no API key
        if "openai" in item.keywords:
            if not os.getenv("OPENAI_API_KEY"):
                item.add_marker(
                    pytest.mark.skip(reason="OPENAI_API_KEY environment variable not set")
                )


@pytest.fixture(scope="session")
def chinook_db(tmp_path_factory):
    """
    Downloads the Chinook SQLite database and returns a SqliteRunner.

    Uses session scope so the database is only downloaded once per test session.
    """
    import httpx
    from vanna.integrations.sqlite import SqliteRunner

    tmp_path = tmp_path_factory.mktemp("data")
    db_path = tmp_path / "Chinook.sqlite"

    # Download the database
    response = httpx.get("https://vanna.ai/Chinook.sqlite")
    response.raise_for_status()

    db_path.write_bytes(response.content)

    return SqliteRunner(database_path=str(db_path))
