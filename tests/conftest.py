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
    config.addinivalue_line("markers", "openai: marks tests requiring OpenAI API key")
    config.addinivalue_line(
        "markers", "azureopenai: marks tests requiring Azure OpenAI API key"
    )
    config.addinivalue_line("markers", "gemini: marks tests requiring Google API key")
    config.addinivalue_line("markers", "ollama: marks tests requiring Ollama")
    config.addinivalue_line("markers", "chromadb: marks tests requiring ChromaDB")
    config.addinivalue_line("markers", "legacy: marks tests for LegacyVannaAdapter")


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests if required API keys are missing."""
    for item in items:
        # Skip Anthropic tests if no API key
        if "anthropic" in item.keywords:
            if not os.getenv("ANTHROPIC_API_KEY"):
                item.add_marker(
                    pytest.mark.skip(
                        reason="ANTHROPIC_API_KEY environment variable not set"
                    )
                )

        # Skip OpenAI tests if no API key
        if "openai" in item.keywords:
            if not os.getenv("OPENAI_API_KEY"):
                item.add_marker(
                    pytest.mark.skip(
                        reason="OPENAI_API_KEY environment variable not set"
                    )
                )

        # Skip Azure OpenAI tests if no API key
        if "azureopenai" in item.keywords:
            if not os.getenv("AZURE_OPENAI_API_KEY"):
                item.add_marker(
                    pytest.mark.skip(
                        reason="AZURE_OPENAI_API_KEY environment variable not set"
                    )
                )

        # Skip Gemini tests if no API key
        if "gemini" in item.keywords:
            if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
                item.add_marker(
                    pytest.mark.skip(
                        reason="GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set"
                    )
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


# =============================================================================
# Urban Eats Database Fixture
# =============================================================================

@pytest.fixture(scope="session")
def urban_eats_db():
    """
    Returns a SqliteRunner connected to the Urban Eats demo database.
    Falls back to creating a minimal test database if the demo database doesn't exist.
    """
    from vanna.integrations.sqlite import SqliteRunner

    db_path = Path(__file__).parent.parent / "demo-data" / "urban_eats.sqlite"

    if db_path.exists():
        return SqliteRunner(database_path=str(db_path))

    # Fall back to in-memory database with test data
    return SqliteRunner(database_path=":memory:")


# =============================================================================
# Mock LLM Service
# =============================================================================

class MockLlmService:
    """
    Mock LLM service for testing that returns predictable responses.

    Usage:
        mock_llm = MockLlmService(responses=[
            LlmResponse(content="Hello!", tool_calls=None),
        ])
    """

    def __init__(
        self,
        responses: list = None,
        stream_chunks: list = None,
        error: Exception = None,
    ):
        self.responses = responses or []
        self.stream_chunks = stream_chunks or []
        self.error = error
        self.call_count = 0
        self.last_request = None
        self.all_requests = []

    async def send_request(self, request):
        """Mock send_request that returns configured responses."""
        self.last_request = request
        self.all_requests.append(request)
        self.call_count += 1

        if self.error:
            raise self.error

        if self.responses:
            idx = min(self.call_count - 1, len(self.responses) - 1)
            return self.responses[idx]

        # Default response
        from vanna.core.llm.models import LlmResponse
        return LlmResponse(content="Mock response", tool_calls=None, finish_reason="stop")

    async def stream_request(self, request):
        """Mock stream_request that yields configured chunks."""
        self.last_request = request
        self.all_requests.append(request)

        if self.error:
            raise self.error

        for chunk in self.stream_chunks:
            yield chunk

    async def validate_tools(self, tools):
        """Mock validate_tools that returns empty list (no validation errors)."""
        return []


@pytest.fixture
def mock_llm_service():
    """Fixture that returns a MockLlmService factory."""
    def _create_mock(responses=None, stream_chunks=None, error=None):
        return MockLlmService(responses=responses, stream_chunks=stream_chunks, error=error)
    return _create_mock


# =============================================================================
# Mock SQL Runner
# =============================================================================

class MockSqlRunner:
    """
    Mock SQL runner for testing that returns configured DataFrames.

    Usage:
        mock_runner = MockSqlRunner(return_data=pd.DataFrame({"col": [1, 2, 3]}))
    """

    def __init__(self, return_data=None, error: Exception = None):
        import pandas as pd
        self.return_data = return_data if return_data is not None else pd.DataFrame()
        self.error = error
        self.last_query = None
        self.all_queries = []

    async def run_sql(self, args, context):
        """Mock run_sql that returns configured DataFrame."""
        self.last_query = args.sql
        self.all_queries.append(args.sql)

        if self.error:
            raise self.error

        return self.return_data


@pytest.fixture
def mock_sql_runner():
    """Fixture that returns a MockSqlRunner factory."""
    def _create_mock(return_data=None, error=None):
        return MockSqlRunner(return_data=return_data, error=error)
    return _create_mock


# =============================================================================
# Mock File System
# =============================================================================

class MockFileSystem:
    """
    In-memory file system for testing.

    Usage:
        mock_fs = MockFileSystem()
        mock_fs.files["test.csv"] = "col1,col2\n1,2"
    """

    def __init__(self):
        self.files: dict = {}
        self.write_calls: list = []
        self.read_calls: list = []

    async def write_file(self, filename: str, content: str, context, overwrite: bool = False):
        """Mock write_file that stores content in memory."""
        self.write_calls.append({"filename": filename, "content": content, "overwrite": overwrite})

        if filename in self.files and not overwrite:
            raise FileExistsError(f"File {filename} already exists")

        self.files[filename] = content

    async def read_file(self, filename: str, context) -> str:
        """Mock read_file that retrieves content from memory."""
        self.read_calls.append(filename)

        if filename not in self.files:
            raise FileNotFoundError(f"File {filename} not found")

        return self.files[filename]

    async def list_files(self, directory: str, context, pattern: str = "*") -> list:
        """Mock list_files that returns matching files from memory."""
        import fnmatch
        return [f for f in self.files.keys() if fnmatch.fnmatch(f, pattern)]


@pytest.fixture
def mock_file_system():
    """Fixture that returns a new MockFileSystem instance."""
    return MockFileSystem()


# =============================================================================
# Mock Agent Memory
# =============================================================================

class MockAgentMemory:
    """
    In-memory agent memory for testing.
    """

    def __init__(self):
        self.tool_memories: list = []
        self.text_memories: list = []
        self.save_calls: list = []
        self.search_calls: list = []

    async def save_tool_usage(self, question: str, tool_name: str, args: dict, context, success: bool = True):
        """Mock save_tool_usage that stores in memory."""
        import uuid
        from datetime import datetime

        memory = {
            "memory_id": str(uuid.uuid4()),
            "question": question,
            "tool_name": tool_name,
            "args": args,
            "timestamp": datetime.now(),
            "success": success,
        }
        self.tool_memories.append(memory)
        self.save_calls.append(memory)
        return memory

    async def search_similar_usage(
        self, question: str, context, limit: int = 10,
        similarity_threshold: float = 0.7, tool_name_filter: str = None
    ) -> list:
        """Mock search_similar_usage with simple keyword matching."""
        self.search_calls.append({"question": question, "limit": limit, "tool_name_filter": tool_name_filter})

        results = []
        question_words = set(question.lower().split())

        for memory in self.tool_memories:
            if tool_name_filter and memory["tool_name"] != tool_name_filter:
                continue

            memory_words = set(memory["question"].lower().split())
            overlap = len(question_words & memory_words)
            score = overlap / max(len(question_words), 1)

            if score >= similarity_threshold:
                results.append({"memory": memory, "similarity_score": score})

        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:limit]

    async def save_text_memory(self, text: str, context, metadata: dict = None):
        """Mock save_text_memory that stores in memory."""
        import uuid
        from datetime import datetime

        memory = {
            "memory_id": str(uuid.uuid4()),
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
        }
        self.text_memories.append(memory)
        return memory

    async def search_text_memories(self, query: str, context, limit: int = 10) -> list:
        """Mock search_text_memories with simple matching."""
        return self.text_memories[:limit]


@pytest.fixture
def mock_agent_memory():
    """Fixture that returns a new MockAgentMemory instance."""
    return MockAgentMemory()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def admin_user():
    """Fixture that returns an admin user with all permissions."""
    from vanna.core.user.models import User
    return User(
        id="admin-001",
        username="admin",
        email="admin@example.com",
        metadata={"role": "administrator"},
        group_memberships=["admin", "user"]
    )


@pytest.fixture
def regular_user():
    """Fixture that returns a regular user with basic permissions."""
    from vanna.core.user.models import User
    return User(
        id="user-001",
        username="regular_user",
        email="user@example.com",
        metadata={"role": "user"},
        group_memberships=["user"]
    )


@pytest.fixture
def guest_user():
    """Fixture that returns a guest user with minimal permissions."""
    from vanna.core.user.models import User
    return User(
        id="guest-001",
        username="guest",
        email="guest@example.com",
        metadata={"role": "guest"},
        group_memberships=["guest"]
    )


# =============================================================================
# Request Context Fixture
# =============================================================================

@pytest.fixture
def request_context():
    """Fixture that returns a basic RequestContext for testing."""
    from vanna.core.user.request_context import RequestContext
    return RequestContext(
        cookies={},
        headers={},
        remote_addr="127.0.0.1",
        query_params={},
        metadata={}
    )


# =============================================================================
# FastAPI Test Client Fixtures
# =============================================================================

@pytest.fixture
def test_app(mock_llm_service, mock_agent_memory, admin_user):
    """
    Fixture that returns a FastAPI app with mocked dependencies for testing.
    """
    from fastapi.testclient import TestClient
    from vanna.servers.fastapi.app import VannaFastAPIServer
    from vanna.core.agent.agent import Agent
    from vanna.core.registry import ToolRegistry
    from vanna.core.user.resolver import UserResolver
    from vanna.core.user.request_context import RequestContext

    # Create a simple user resolver that always returns admin
    class TestUserResolver(UserResolver):
        async def resolve_user(self, request_context: RequestContext):
            return admin_user

    # Create agent with mocked dependencies
    mock_llm = mock_llm_service()
    tool_registry = ToolRegistry()

    agent = Agent(
        llm_service=mock_llm,
        tool_registry=tool_registry,
        user_resolver=TestUserResolver(),
        agent_memory=mock_agent_memory,
    )

    # Create server
    server = VannaFastAPIServer(agent=agent)
    app = server.create_app()

    return app


@pytest.fixture
def test_client(test_app):
    """Fixture that returns a TestClient for the test app."""
    from fastapi.testclient import TestClient
    return TestClient(test_app)
