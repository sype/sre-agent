"""Schemas for the client."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
from mcp import ClientSession
from mcp.types import Tool
from shared.logger import logger

DEFAULT_QUERY_TIMEOUT = 300

load_dotenv()


def _validate_fields(self: DataclassInstance) -> None:
    for config in fields(self):
        attr = getattr(self, config.name)

        # Only enforce non-empty for string fields. Lists (e.g. TOOLS/SERVICES)
        # may legitimately be empty and should not fail validation.
        if isinstance(attr, str) and not attr:
            msg = f"Environment variable {config.name.upper()} is not set."
            logger.error(msg)
            raise ValueError(msg)


def _load_json_list_env(var_name: str) -> list[str]:
    """Load a JSON list from env; accept CSV; treat empty as []."""
    raw_value = os.getenv(var_name)
    if raw_value is None or raw_value.strip() == "":
        return []

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return parsed
    except Exception as e:
        logger.debug("Failed to parse %s as JSON list: %s", var_name, e)

    return [item.strip() for item in raw_value.split(",") if item.strip()]


@dataclass
class ServerSession:
    """A dataclass to hold the session and tools for a server."""

    tools: list[Tool]
    session: ClientSession


class MCPServer(StrEnum):
    """The service names for the MCP servers."""

    SLACK = "slack"
    GITHUB = "github"
    KUBERNETES = "kubernetes"
    PROMPT = "prompt-server"


@dataclass(frozen=True)
class AuthConfig:
    """A config class containing authorisation environment variables."""

    slack_signing_secret: str = os.getenv("SLACK_SIGNING_SECRET", "")
    dev_bearer_token: str = os.getenv("DEV_BEARER_TOKEN", "")

    def __post_init__(self) -> None:
        """A post-constructor method for the dataclass."""
        _validate_fields(self)


@dataclass(frozen=True)
class ClientConfig:
    """A client config storing parsed env variables."""

    slack_channel_id: str = os.getenv("SLACK_CHANNEL_ID", "")
    tools: list[str] = field(default_factory=lambda: _load_json_list_env("TOOLS"))
    model: str = os.getenv("LLM_MODEL", "claude-3-7-sonnet-latest")
    max_tokens: int = 1000
    max_tool_retries: int = 3
    query_timeout: int = int(
        os.getenv("QUERY_TIMEOUT", DEFAULT_QUERY_TIMEOUT) or DEFAULT_QUERY_TIMEOUT
    )
    services: list[str] = field(default_factory=lambda: _load_json_list_env("SERVICES"))

    def __post_init__(self) -> None:
        """A post-constructor method for the dataclass."""
        _validate_fields(self)
