"""Unit tests for diagnose prompt override logic in prompt server."""

from sre_agent.servers.prompt_server.server import diagnose


def test_prompt_overrides_with_repo_url_and_ns_container():
    """Overrides via repo_url, namespace and container appear in the prompt text."""
    text = diagnose(
        service="svc",
        slack_channel_id="C123",
        repo_url="https://github.com/acme/shop/tree/main/backend",
        namespace="prod",
        container="app",
    )
    assert "acme" in text
    assert "shop" in text
    assert "backend" in text
    assert "namespace" in text
    assert "container" in text


def test_prompt_defaults_to_repo_root_when_no_path():
    """When no path is provided in repo_url, prompt should reference repo root."""
    text = diagnose(
        service="svc",
        slack_channel_id="C123",
        repo_url="https://github.com/acme/shop",
    )
    # Should refer to root directory and not to a fixed env default path
    assert "root directory of the repository" in text
