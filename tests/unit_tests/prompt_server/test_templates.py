"""Tests for Jinja2 template rendering in diagnose prompt."""

from __future__ import annotations

import pytest

from sre_agent.servers.prompt_server import server as prompt_server


def _clear_config_cache() -> None:
    # Ensure PromptServerConfig is reloaded with current env vars
    prompt_server._get_prompt_server_config.cache_clear()


def test_default_template_renders_expected_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no env override, default template should render expected output."""
    monkeypatch.delenv("DIAGNOSE_PROMPT_TEMPLATE", raising=False)
    _clear_config_cache()

    text = prompt_server.diagnose(
        service="svc",
        slack_channel_id="C123",
    )

    expected_parts = [
        "You are SRE Agent. Perform a focused diagnosis and return clear findings.",
        (
            "1) Logs: List pods. Then get the last 1000 lines of logs for the pod "
            "of service 'svc'."
        ),
        (
            "   If a pod name is required, list pods first and choose the one "
            "matching the service label."
        ),
        (
            "2) Code: Using GitHub org '"
            + prompt_server._get_prompt_server_config().organisation
            + "', repo '"
            + prompt_server._get_prompt_server_config().repo_name
            + "', inspect the root directory of the repository. If the path "
            + "does not exist, list directories and fetch the referenced file."
        ),
        (
            "3) Diagnose: Identify the most likely root cause; include file paths "
            "and short code excerpts."
        ),
        "4) Report: Create one GitHub issue (skip if issues disabled).",
        "5) Notify: Post a concise summary to Slack channel C123.",
        "Output requirements:",
        ("- Summarise key errors with timestamps and pod/container."),
        (
            "- Reference code locations (file:line) and include short snippets "
            "when relevant."
        ),
        "- Provide next actions.",
        "- Create at most one issue and one Slack message.",
    ]
    expected = "\n".join(expected_parts)

    assert text == expected


def test_custom_template_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """When env var points to a file path, render that file."""
    tmpl = tmp_path / "diagnose_custom.j2"
    tmpl.write_text("Hello {{ service }}", encoding="utf-8")
    monkeypatch.setenv("DIAGNOSE_PROMPT_TEMPLATE", str(tmpl))
    _clear_config_cache()

    out = prompt_server.diagnose(service="svc", slack_channel_id="C1")
    assert out == "Hello svc"


def test_inline_template_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """When env var is not a file, treat it as inline template string."""
    monkeypatch.setenv("DIAGNOSE_PROMPT_TEMPLATE", "INLINE: {{ org }}/{{ repo }}")
    _clear_config_cache()

    cfg = prompt_server._get_prompt_server_config()
    out = prompt_server.diagnose(service="svc", slack_channel_id="C1")
    assert out == f"INLINE: {cfg.organisation}/{cfg.repo_name}"


def test_at_template_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    """When env var is @diagnose.j2, load from templates directory."""
    monkeypatch.setenv("DIAGNOSE_PROMPT_TEMPLATE", "@diagnose.j2")
    _clear_config_cache()

    text = prompt_server.diagnose(service="svc", slack_channel_id="C123")
    assert "You are SRE Agent. Perform a focused diagnosis" in text
    assert "service 'svc'" in text
