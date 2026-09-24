"""Tests for the Kimi service parsing and guard logic."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import openai
import pytest

from services.kimi_service import (
    KimiAuthError,
    KimiConnectionError,
    KimiInvalidRequestError,
    KimiRateLimitError,
    KimiService,
    KimiServiceError,
    KimiServiceUnavailableError,
)


class TestParseResponse:
    def test_extracts_last_code_block(self):
        content = (
            "First, I'll add error handling.\n\n"
            "```python\nprint('old')\n```\n\n"
            "Here is the final version:\n\n"
            "```python\ndef greet(name: str) -> None:\n    print(f'Hello, {name}')\n```"
        )
        result = KimiService._parse_response(
            content, fallback_code="original", language="python"
        )
        assert "final version" in result["explanation"]
        assert "def greet" in result["code"]
        assert result["language"] == "python"

    def test_no_code_block_returns_fallback(self):
        content = "No changes needed."
        result = KimiService._parse_response(
            content, fallback_code="unchanged", language="python"
        )
        assert result["explanation"] == content
        assert result["code"] == "unchanged"

    def test_empty_response_returns_fallback(self):
        result = KimiService._parse_response(
            "", fallback_code="unchanged", language="python"
        )
        assert "vazia" in result["explanation"]
        assert result["code"] == "unchanged"

    def test_optional_language_tag(self):
        content = "```\nconst x = 1;\n```"
        result = KimiService._parse_response(
            content, fallback_code="original", language="javascript"
        )
        assert result["code"] == "const x = 1;"
        assert result["language"] == "javascript"


class TestComposeGuards:
    def test_compose_without_key_raises(self):
        service = KimiService(api_key=None)
        with pytest.raises(KimiAuthError, match="KIMI_API_KEY"):
            asyncio.run(service.compose("code", "prompt"))

    def test_compose_with_empty_prompt_raises(self):
        service = KimiService(api_key="fake-key")
        with pytest.raises(KimiInvalidRequestError, match="não pode estar vazio"):
            asyncio.run(service.compose("code", "   "))

    def test_compose_with_oversized_payload_raises(self):
        service = KimiService(api_key="fake-key", max_code_chars=5)
        with pytest.raises(KimiInvalidRequestError, match="excede o limite"):
            asyncio.run(service.compose("print('too long')", "prompt"))


class TestOpenAIErrorTranslation:
    """Verify that OpenAI SDK exceptions become Portuguese typed errors."""

    @pytest.fixture
    def service(self):
        return KimiService(api_key="fake-key")

    def _run(self, coro):
        return asyncio.run(coro)

    def test_authentication_error_becomes_auth_error(self, service):
        response = Mock(status_code=401)
        exc = openai.AuthenticationError(
            "Invalid API key", response=response, body=None
        )
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiAuthError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "auth_error"

    def test_rate_limit_error_becomes_rate_limit(self, service):
        response = Mock(status_code=429)
        exc = openai.RateLimitError(
            "Rate limit exceeded", response=response, body=None
        )
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiRateLimitError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "rate_limit"

    def test_bad_request_error_becomes_invalid_request(self, service):
        response = Mock(status_code=400)
        exc = openai.BadRequestError(
            "Invalid model", response=response, body=None
        )
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiInvalidRequestError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "invalid_request"

    def test_api_status_5xx_becomes_service_unavailable(self, service):
        response = Mock(status_code=503)
        exc = openai.APIStatusError(
            "Service unavailable", response=response, body=None
        )
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiServiceUnavailableError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "service_unavailable"

    def test_api_status_4xx_other_becomes_generic(self, service):
        response = Mock(status_code=418)
        exc = openai.APIStatusError("I'm a teapot", response=response, body=None)
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiServiceError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "generic_api_error"

    def test_connection_error_becomes_connection_error(self, service):
        request = Mock()
        exc = openai.APIConnectionError(
            message="Connection failed", request=request
        )
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiConnectionError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "connection_error"

    def test_generic_openai_error_becomes_generic(self, service):
        exc = openai.OpenAIError("Something went wrong")
        with patch.object(
            service._client.chat.completions, "create", side_effect=exc
        ):
            with pytest.raises(KimiServiceError) as ctx:
                self._run(service.compose("code", "prompt"))
        assert ctx.value.error_type == "generic_api_error"
