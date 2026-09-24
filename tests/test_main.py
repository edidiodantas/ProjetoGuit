"""Tests for the FastAPI application layer."""

from __future__ import annotations


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
    assert "Kimi Vibe Composer" in response.text


def test_static_js_module_served(client):
    response = client.get("/js/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_composer_without_api_key_returns_503(client):
    response = client.post(
        "/api/composer",
        json={
            "code": "print('hello')",
            "prompt": "Add type hints",
            "language": "python",
        },
    )
    assert response.status_code == 503
    assert "KIMI_API_KEY" in response.json()["detail"]


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
