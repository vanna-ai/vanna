"""
Unit tests for Azure OpenAI LLM service integration.

These tests validate the Azure OpenAI integration without making actual API calls.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from vanna.integrations.azureopenai import AzureOpenAILlmService
from vanna.integrations.azureopenai.llm import _is_reasoning_model


class TestReasoningModelDetection:
    """Test reasoning model detection logic."""

    def test_is_reasoning_model_o1(self):
        """Test that o1 models are detected as reasoning models."""
        assert _is_reasoning_model("o1")
        assert _is_reasoning_model("o1-mini")
        assert _is_reasoning_model("o1-preview")

    def test_is_reasoning_model_o3(self):
        """Test that o3 models are detected as reasoning models."""
        assert _is_reasoning_model("o3-mini")

    def test_is_reasoning_model_gpt5(self):
        """Test that GPT-5 series models are detected as reasoning models."""
        assert _is_reasoning_model("gpt-5")
        assert _is_reasoning_model("gpt-5-mini")
        assert _is_reasoning_model("gpt-5-nano")
        assert _is_reasoning_model("gpt-5-pro")
        assert _is_reasoning_model("gpt-5-codex")

    def test_is_not_reasoning_model(self):
        """Test that standard models are not detected as reasoning models."""
        assert not _is_reasoning_model("gpt-4")
        assert not _is_reasoning_model("gpt-4o")
        assert not _is_reasoning_model("gpt-4-turbo")
        assert not _is_reasoning_model("gpt-3.5-turbo")

    def test_case_insensitive_detection(self):
        """Test that model detection is case insensitive."""
        assert _is_reasoning_model("GPT-5")
        assert _is_reasoning_model("O1-MINI")
        assert not _is_reasoning_model("GPT-4O")


class TestAzureOpenAILlmServiceInitialization:
    """Test Azure OpenAI service initialization."""

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_with_all_params(self, mock_azure_openai):
        """Test initialization with all parameters provided."""
        service = AzureOpenAILlmService(
            model="gpt-4o",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
            api_version="2024-10-21",
        )

        assert service.model == "gpt-4o"
        assert not service._is_reasoning_model

        # Verify AzureOpenAI was called with correct params
        mock_azure_openai.assert_called_once()
        call_kwargs = mock_azure_openai.call_args[1]
        assert call_kwargs["azure_endpoint"] == "https://test.openai.azure.com"
        assert call_kwargs["api_version"] == "2024-10-21"
        assert call_kwargs["api_key"] == "test-key"

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_with_reasoning_model(self, mock_azure_openai):
        """Test initialization with a reasoning model."""
        service = AzureOpenAILlmService(
            model="gpt-5",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

        assert service.model == "gpt-5"
        assert service._is_reasoning_model

    @patch.dict(
        "os.environ",
        {
            "AZURE_OPENAI_MODEL": "gpt-4o-deployment",
            "AZURE_OPENAI_API_KEY": "env-key",
            "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com",
            "AZURE_OPENAI_API_VERSION": "2024-06-01",
        },
    )
    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_from_environment(self, mock_azure_openai):
        """Test initialization from environment variables."""
        service = AzureOpenAILlmService()

        assert service.model == "gpt-4o-deployment"

        # Verify AzureOpenAI was called with env values
        call_kwargs = mock_azure_openai.call_args[1]
        assert call_kwargs["azure_endpoint"] == "https://env.openai.azure.com"
        assert call_kwargs["api_version"] == "2024-06-01"
        assert call_kwargs["api_key"] == "env-key"

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_missing_model_raises(self, mock_azure_openai):
        """Test that missing model parameter raises ValueError."""
        with pytest.raises(ValueError, match="model parameter.*is required"):
            AzureOpenAILlmService(
                api_key="test-key",
                azure_endpoint="https://test.openai.azure.com",
            )

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_missing_endpoint_raises(self, mock_azure_openai):
        """Test that missing azure_endpoint raises ValueError."""
        with pytest.raises(ValueError, match="azure_endpoint is required"):
            AzureOpenAILlmService(
                model="gpt-4o",
                api_key="test-key",
            )

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_missing_auth_raises(self, mock_azure_openai):
        """Test that missing authentication raises ValueError."""
        with pytest.raises(ValueError, match="Authentication required"):
            AzureOpenAILlmService(
                model="gpt-4o",
                azure_endpoint="https://test.openai.azure.com",
            )

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_with_azure_ad_token_provider(self, mock_azure_openai):
        """Test initialization with Azure AD token provider."""
        mock_token_provider = Mock()
        service = AzureOpenAILlmService(
            model="gpt-4o",
            azure_endpoint="https://test.openai.azure.com",
            azure_ad_token_provider=mock_token_provider,
        )

        # Verify token provider was used instead of API key
        call_kwargs = mock_azure_openai.call_args[1]
        assert call_kwargs["azure_ad_token_provider"] == mock_token_provider
        assert "api_key" not in call_kwargs

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_init_default_api_version(self, mock_azure_openai):
        """Test that default API version is used when not specified."""
        service = AzureOpenAILlmService(
            model="gpt-4o",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

        # Verify default API version (2024-10-21)
        call_kwargs = mock_azure_openai.call_args[1]
        assert call_kwargs["api_version"] == "2024-10-21"


class TestAzureOpenAILlmServicePayloadBuilding:
    """Test payload building for API requests."""

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_build_payload_includes_temperature_for_standard_model(
        self, mock_azure_openai
    ):
        """Test that temperature is included for standard models."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User

        service = AzureOpenAILlmService(
            model="gpt-4o",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            temperature=0.8,
        )

        payload = service._build_payload(request)

        assert "temperature" in payload
        assert payload["temperature"] == 0.8
        assert payload["model"] == "gpt-4o"

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_build_payload_excludes_temperature_for_reasoning_model(
        self, mock_azure_openai
    ):
        """Test that temperature is excluded for reasoning models."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User

        service = AzureOpenAILlmService(
            model="gpt-5",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            temperature=0.8,
        )

        payload = service._build_payload(request)

        assert "temperature" not in payload
        assert payload["model"] == "gpt-5"

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_build_payload_with_system_prompt(self, mock_azure_openai):
        """Test that system prompt is added to messages."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User

        service = AzureOpenAILlmService(
            model="gpt-4o",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="test")],
            user=User(id="test", email="test@example.com", group_memberships=[]),
            system_prompt="You are a helpful assistant.",
        )

        payload = service._build_payload(request)

        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are a helpful assistant."

    @patch("vanna.integrations.azureopenai.llm.AzureOpenAI")
    def test_build_payload_with_tools(self, mock_azure_openai):
        """Test that tools are properly formatted in payload."""
        from vanna.core.llm import LlmRequest, LlmMessage
        from vanna.core.user import User
        from vanna.core.tool import ToolSchema

        service = AzureOpenAILlmService(
            model="gpt-4o",
            api_key="test-key",
            azure_endpoint="https://test.openai.azure.com",
        )

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


class TestImportError:
    """Test import error handling."""

    def test_import_error_message(self):
        """Test that helpful error message is shown when openai is not installed."""
        with patch.dict("sys.modules", {"openai": None}):
            # Force module reload to trigger import error
            import sys

            if "vanna.integrations.azureopenai.llm" in sys.modules:
                del sys.modules["vanna.integrations.azureopenai.llm"]

            with pytest.raises(
                ImportError, match="pip install 'vanna\\[azureopenai\\]'"
            ):
                from vanna.integrations.azureopenai import AzureOpenAILlmService

                AzureOpenAILlmService(
                    model="gpt-4o",
                    api_key="test",
                    azure_endpoint="https://test.openai.azure.com",
                )
