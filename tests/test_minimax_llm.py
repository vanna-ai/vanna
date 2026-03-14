"""
Unit tests for MiniMax LLM service integration.

These tests validate the MiniMax integration without making actual API calls.
"""

import pytest
from unittest.mock import patch


class TestMinimaxLlmServiceInitialization:
    """Test MiniMax service initialization."""

    @patch("openai.OpenAI")
    def test_init_with_all_params(self, mock_openai):
        """Test initialization with all parameters provided."""
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(
            model="MiniMax-M2.5",
            api_key="test-key",
            base_url="https://api.minimax.io/v1",
        )

        assert service.model == "MiniMax-M2.5"

        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["api_key"] == "test-key"
        assert call_kwargs["base_url"] == "https://api.minimax.io/v1"

    @patch("openai.OpenAI")
    def test_init_default_model(self, mock_openai):
        """Test that default model is MiniMax-M2.5."""
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        assert service.model == "MiniMax-M2.5"

    @patch("openai.OpenAI")
    def test_init_default_base_url(self, mock_openai):
        """Test that default base_url points to MiniMax API."""
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["base_url"] == "https://api.minimax.io/v1"

    @patch("openai.OpenAI")
    def test_init_custom_model(self, mock_openai):
        """Test initialization with a custom model name."""
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(
            model="MiniMax-M2.5-highspeed",
            api_key="test-key",
        )

        assert service.model == "MiniMax-M2.5-highspeed"

    @patch.dict(
        "os.environ",
        {
            "MINIMAX_MODEL": "MiniMax-M2.5-highspeed",
            "MINIMAX_API_KEY": "env-key",
            "MINIMAX_BASE_URL": "https://custom.minimax.io/v1",
        },
    )
    @patch("openai.OpenAI")
    def test_init_from_environment(self, mock_openai):
        """Test initialization from environment variables."""
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService()

        assert service.model == "MiniMax-M2.5-highspeed"

        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["api_key"] == "env-key"
        assert call_kwargs["base_url"] == "https://custom.minimax.io/v1"

    def test_init_missing_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        from vanna.integrations.minimax import MinimaxLlmService

        with patch.dict("os.environ", {}, clear=True):
            # Remove all MINIMAX env vars
            import os

            for key in list(os.environ.keys()):
                if key.startswith("MINIMAX"):
                    del os.environ[key]

            with pytest.raises(ValueError, match="API key is required"):
                MinimaxLlmService()


class TestMinimaxLlmServicePayloadBuilding:
    """Test payload building for API requests."""

    @patch("openai.OpenAI")
    def test_build_payload_clamps_zero_temperature(self, mock_openai):
        """Test that temperature=0.0 is clamped to 0.01 for MiniMax."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            temperature=0.0,
        )

        payload = service._build_payload(request)

        assert payload["temperature"] == 0.01

    @patch("openai.OpenAI")
    def test_build_payload_clamps_high_temperature(self, mock_openai):
        """Test that temperature > 1.0 is clamped to 1.0 for MiniMax."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            temperature=1.5,
        )

        payload = service._build_payload(request)

        assert payload["temperature"] == 1.0

    @patch("openai.OpenAI")
    def test_build_payload_valid_temperature(self, mock_openai):
        """Test that valid temperature passes through unchanged."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            temperature=0.7,
        )

        payload = service._build_payload(request)

        assert payload["temperature"] == 0.7

    @patch("openai.OpenAI")
    def test_build_payload_with_system_prompt(self, mock_openai):
        """Test that system prompt is added to messages."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            system_prompt="You are a helpful assistant.",
        )

        payload = service._build_payload(request)

        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are a helpful assistant."

    @patch("openai.OpenAI")
    def test_build_payload_with_tools(self, mock_openai):
        """Test that tools are properly formatted in payload."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.core.tool import ToolSchema
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        tool = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
            },
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            tools=[tool],
        )

        payload = service._build_payload(request)

        assert "tools" in payload
        assert len(payload["tools"]) == 1
        assert payload["tools"][0]["type"] == "function"
        assert payload["tools"][0]["function"]["name"] == "test_tool"
        assert payload["tool_choice"] == "auto"

    @patch("openai.OpenAI")
    def test_build_payload_model_name(self, mock_openai):
        """Test that model name is correctly set in payload."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(
            model="MiniMax-M2.5-highspeed", api_key="test-key"
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
        )

        payload = service._build_payload(request)

        assert payload["model"] == "MiniMax-M2.5-highspeed"


class TestMinimaxLlmServiceToolValidation:
    """Test tool validation."""

    @patch("openai.OpenAI")
    @pytest.mark.asyncio
    async def test_validate_tools_valid(self, mock_openai):
        """Test validation of valid tool schemas."""
        from vanna.core.tool import ToolSchema
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        tools = [
            ToolSchema(
                name="valid_tool",
                description="A valid tool",
                parameters={"type": "object", "properties": {}},
            )
        ]

        errors = await service.validate_tools(tools)
        assert errors == []

    @patch("openai.OpenAI")
    @pytest.mark.asyncio
    async def test_validate_tools_long_name(self, mock_openai):
        """Test validation rejects tool names longer than 64 characters."""
        from vanna.core.tool import ToolSchema
        from vanna.integrations.minimax import MinimaxLlmService

        service = MinimaxLlmService(api_key="test-key")

        tools = [
            ToolSchema(
                name="a" * 65,
                description="A tool with a very long name",
                parameters={"type": "object", "properties": {}},
            )
        ]

        errors = await service.validate_tools(tools)
        assert len(errors) == 1
        assert "Invalid tool name" in errors[0]


class TestImportError:
    """Test import error handling."""

    def test_import_error_message(self):
        """Test that helpful error message is shown when openai is not installed."""
        with patch.dict("sys.modules", {"openai": None}):
            import sys

            if "vanna.integrations.minimax.llm" in sys.modules:
                del sys.modules["vanna.integrations.minimax.llm"]

            with pytest.raises(
                ImportError, match="pip install 'vanna\\[minimax\\]'"
            ):
                from vanna.integrations.minimax import MinimaxLlmService

                MinimaxLlmService(api_key="test-key")
