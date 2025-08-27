"""Smoke test for lazy LLM provider selection in /health endpoint."""

import os

from fastapi.testclient import TestClient

from sre_agent.llm.main import app

HTTP_OK = 200


def test_health_does_not_require_gemini_key_when_anthropic_selected():
    """Health endpoint should work without GEMINI_API_KEY when provider=anthropic."""
    os.environ["PROVIDER"] = "anthropic"
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == HTTP_OK
        assert r.json()["status"] == "healthy"
