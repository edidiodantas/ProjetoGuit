"""Tests for the FastAPI application layer."""

from __future__ import annotations

from unittest.mock import patch

from services.kimi_service import (
    KimiAuthError,
    KimiRateLimitError,
    KimiServiceError,
)
from main import app


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["kimi_configured"], bool)


def test_api_route_takes_precedence_over_static(client):
    # /api/health is handled by the API router, not by the static mount.
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_static_index_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "IPEIA" in response.text
    assert "VIBE CODING" in response.text
    assert 'class="title-ipeia"' in response.text
    assert 'class="title-vibe"' in response.text
    assert 'href="/manual"' in response.text
    assert ">Manual<" in response.text
    assert "/style.css?v=8" in response.text
    assert "Passo a passo" not in response.text
    marker = 'class="editor-section diff-section"'
    marker_at = response.text.index(marker)
    tag_start = response.text.rfind("<section", 0, marker_at)
    tag_end = response.text.index(">", marker_at)
    diff_tag = response.text[tag_start:tag_end]
    assert "hidden" not in diff_tag
    assert "diff-hidden" not in response.text


def test_manual_page(client):
    response = client.get("/manual")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    text = response.text
    assert "IPEIA VIBE CODING" in text
    assert "Passo a passo" in text
    assert "Construir" in text
    assert "Diferença" in text
    assert "kimi-k2.5-lite" in text
    assert "401" in text
    assert "429" in text
    assert ">Voltar<" in text
    assert 'href="/"' in text
    assert "originalEditor" not in text


def test_static_js_module_served(client):
    response = client.get("/js/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_composer_without_api_key_returns_401(client):
    response = client.post(
        "/api/composer",
        json={
            "code": "print('hello')",
            "prompt": "Add type hints",
            "language": "python",
        },
    )
    assert response.status_code == 401
    body = response.json()
    assert body["error_type"] == "auth_error"
    assert "chave" in body["message"].lower()


def test_composer_rate_limit_returns_429(client):
    with patch.object(
        app.state.kimi, "compose", side_effect=KimiRateLimitError()
    ):
        response = client.post(
            "/api/composer",
            json={
                "code": "print('hello')",
                "prompt": "Add type hints",
                "language": "python",
            },
        )
    assert response.status_code == 429
    body = response.json()
    assert body["error_type"] == "rate_limit"
    assert "limite" in body["message"].lower()


def test_composer_generic_api_error_returns_502(client):
    with patch.object(
        app.state.kimi,
        "compose",
        side_effect=KimiServiceError("erro genérico da API"),
    ):
        response = client.post(
            "/api/composer",
            json={
                "code": "print('hello')",
                "prompt": "Add type hints",
                "language": "python",
            },
        )
    assert response.status_code == 502
    body = response.json()
    assert body["error_type"] == "generic_api_error"


def test_composer_missing_prompt_returns_422(client):
    response = client.post(
        "/api/composer",
        json={
            "code": "print('hello')",
            "language": "python",
        },
    )
    assert response.status_code == 422


def test_composer_missing_code_returns_422(client):
    response = client.post(
        "/api/composer",
        json={
            "prompt": "Add type hints",
            "language": "python",
        },
    )
    assert response.status_code == 422
