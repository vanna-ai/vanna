"""
Regression tests for fixes applied in PR #1 (2026-02-21).

Covers:
  #1069 — FastAPI duplicate keyword arg (title/description/version)
  #1078 — Legacy SQL injection guard (is_sql_valid before run_sql)
  #190  — Graceful handling when LLM returns plain text instead of SQL
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


class MockVanna:
    """Minimal concrete VannaBase subclass for unit tests.

    Uses MockLLM + MockVectorDB so all abstract methods are satisfied
    without requiring real databases or LLM credentials.
    """

    pass


@pytest.fixture
def vanna_instance():
    """Return a fully-constructed mock VannaBase instance."""
    from vanna.legacy.mock.embedding import MockEmbedding
    from vanna.legacy.mock.llm import MockLLM
    from vanna.legacy.mock.vectordb import MockVectorDB

    class MinimalVanna(MockVectorDB, MockLLM, MockEmbedding):
        def __init__(self, config=None):
            MockVectorDB.__init__(self, config=config)
            MockLLM.__init__(self, config=config)
            MockEmbedding.__init__(self, config=config)

    return MinimalVanna()


# ---------------------------------------------------------------------------
# #1069 — FastAPI duplicate keyword arg
# ---------------------------------------------------------------------------


def test_fastapi_create_app_with_custom_title():
    """#1069 — create_app() must not raise TypeError when title is in config."""
    from unittest.mock import MagicMock

    from vanna.servers.fastapi.app import VannaFastAPIServer

    agent = MagicMock()
    server = VannaFastAPIServer(
        agent=agent,
        config={"fastapi": {"title": "My API"}},
    )
    app = server.create_app()
    assert app.title == "My API"


def test_fastapi_create_app_with_all_config_keys():
    """#1069 — create_app() must not raise when title, description, and version
    are all present in the fastapi config dict."""
    from vanna.servers.fastapi.app import VannaFastAPIServer

    agent = MagicMock()
    server = VannaFastAPIServer(
        agent=agent,
        config={
            "fastapi": {
                "title": "Custom Title",
                "description": "Custom Description",
                "version": "3.1.4",
            }
        },
    )
    # Before the fix this raised:
    # TypeError: FastAPI.__init__() got multiple values for keyword argument 'title'
    app = server.create_app()
    assert app.title == "Custom Title"
    assert app.description == "Custom Description"
    assert app.version == "3.1.4"


def test_fastapi_create_app_default_config():
    """#1069 — create_app() works with empty config (baseline)."""
    from vanna.servers.fastapi.app import VannaFastAPIServer

    agent = MagicMock()
    server = VannaFastAPIServer(agent=agent)
    app = server.create_app()
    assert app.title == "Vanna Agents API"
    assert app.version == "0.1.0"


# ---------------------------------------------------------------------------
# #1078 — is_sql_valid() gates
# ---------------------------------------------------------------------------


def test_is_sql_valid_accepts_select(vanna_instance):
    """#1078 — is_sql_valid must return True for a SELECT statement."""
    assert vanna_instance.is_sql_valid("SELECT * FROM users") is True


def test_is_sql_valid_accepts_select_with_leading_whitespace(vanna_instance):
    """#1078 — is_sql_valid handles leading whitespace before SELECT."""
    assert vanna_instance.is_sql_valid("  SELECT id FROM orders WHERE id = 1") is True


def test_is_sql_valid_rejects_drop(vanna_instance):
    """#1078 — is_sql_valid must return False for DROP TABLE."""
    assert vanna_instance.is_sql_valid("DROP TABLE users") is False


def test_is_sql_valid_rejects_delete(vanna_instance):
    """#1078 — is_sql_valid must return False for DELETE."""
    assert vanna_instance.is_sql_valid("DELETE FROM users WHERE id = 1") is False


def test_is_sql_valid_rejects_insert(vanna_instance):
    """#1078 — is_sql_valid must return False for INSERT."""
    assert vanna_instance.is_sql_valid("INSERT INTO users VALUES (1, 'alice')") is False


def test_is_sql_valid_rejects_plain_text(vanna_instance):
    """#1078/#190 — is_sql_valid must return False for plain-text LLM responses."""
    assert (
        vanna_instance.is_sql_valid(
            "I'm sorry, I cannot generate SQL for this request."
        )
        is False
    )


# ---------------------------------------------------------------------------
# #190 — ask() graceful handling of plain-text LLM responses
# ---------------------------------------------------------------------------


def test_ask_returns_text_when_llm_returns_plain_text(vanna_instance):
    """#190 — When the LLM returns plain text instead of SQL, ask() must
    return (text, None, None) without crashing."""
    plain_text = "I cannot generate SQL for this philosophical question."

    with patch.object(vanna_instance, "generate_sql", return_value=plain_text):
        result = vanna_instance.ask(
            "What is the meaning of life?", print_results=False
        )

    sql, df, fig = result
    assert sql == plain_text
    assert df is None
    assert fig is None


def test_ask_returns_early_for_drop_table(vanna_instance):
    """#1078 — ask() must return (sql, None, None) without executing a
    DROP TABLE statement returned by the LLM."""
    dangerous_sql = "DROP TABLE users"

    with patch.object(vanna_instance, "generate_sql", return_value=dangerous_sql):
        # run_sql must never be called for invalid SQL
        with patch.object(vanna_instance, "run_sql") as mock_run_sql:
            result = vanna_instance.ask("Delete all users", print_results=False)
            mock_run_sql.assert_not_called()

    sql, df, fig = result
    assert sql == dangerous_sql
    assert df is None
    assert fig is None


def test_ask_returns_early_for_delete_statement(vanna_instance):
    """#1078 — ask() must stop before run_sql for DELETE statements."""
    delete_sql = "DELETE FROM orders WHERE total < 0"

    with patch.object(vanna_instance, "generate_sql", return_value=delete_sql):
        with patch.object(vanna_instance, "run_sql") as mock_run_sql:
            result = vanna_instance.ask("Remove bad orders", print_results=False)
            mock_run_sql.assert_not_called()

    sql, df, fig = result
    assert sql == delete_sql
    assert df is None
    assert fig is None


def test_ask_proceeds_for_valid_select(vanna_instance):
    """#1078/#190 — ask() must call run_sql for a valid SELECT statement."""
    import pandas as pd

    # run_sql_is_set is normally set by connect_to_*() helpers; set it here
    # so ask() doesn't bail out at the "not connected" check.
    vanna_instance.run_sql_is_set = True

    valid_sql = "SELECT * FROM users LIMIT 10"
    mock_df = pd.DataFrame({"id": [1, 2], "name": ["alice", "bob"]})

    with patch.object(vanna_instance, "generate_sql", return_value=valid_sql):
        with patch.object(vanna_instance, "run_sql", return_value=mock_df) as mock_run:
            result = vanna_instance.ask(
                "Show all users", print_results=False, visualize=False
            )
            mock_run.assert_called_once_with(valid_sql)

    sql, df, fig = result
    assert sql == valid_sql
    assert df is not None
    assert list(df.columns) == ["id", "name"]


# ---------------------------------------------------------------------------
# Flask /run_sql is_sql_valid guard (#1078)
# ---------------------------------------------------------------------------


def test_flask_run_sql_guard_rejects_non_select(vanna_instance):
    """#1078 — The Flask /api/v0/run_sql endpoint must return an error JSON
    (not execute) when the cached SQL fails is_sql_valid()."""
    pytest.importorskip("flask", reason="flask not installed")
    from vanna.legacy.flask import VannaFlaskApp

    app_wrapper = VannaFlaskApp(vanna_instance)
    client = app_wrapper.flask_app.test_client()

    # Inject a dangerous SQL string into the cache and attempt to run it
    cache_id = app_wrapper.cache.generate_id(question="drop test")
    app_wrapper.cache.set(id=cache_id, field="question", value="drop test")
    app_wrapper.cache.set(
        id=cache_id, field="sql", value="DROP TABLE users"
    )

    resp = client.get(f"/api/v0/run_sql?id={cache_id}")
    data = resp.get_json()

    assert data is not None
    assert data.get("type") == "error"
    # run_sql must never have been called
    with patch.object(vanna_instance, "run_sql") as mock_run:
        mock_run.assert_not_called()
