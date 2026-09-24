"""Tests for the Kimi service parsing and guard logic."""

from __future__ import annotations

import pytest

from services.kimi_service import KimiService, KimiServiceError


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
        with pytest.raises(KimiServiceError, match="KIMI_API_KEY"):
            import asyncio

            asyncio.run(service.compose("code", "prompt"))

    def test_compose_with_empty_prompt_raises(self):
        service = KimiService(api_key="fake-key")
        with pytest.raises(KimiServiceError, match="não pode estar vazio"):
            import asyncio

            asyncio.run(service.compose("code", "   "))

    def test_compose_with_oversized_payload_raises(self):
        service = KimiService(api_key="fake-key", max_code_chars=5)
        with pytest.raises(KimiServiceError, match="excede o limite"):
            import asyncio

            asyncio.run(service.compose("print('too long')", "prompt"))
