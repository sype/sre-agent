"""A module containing schemas for the prompt server."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


load_dotenv()


def _validate_fields(self: DataclassInstance) -> None:
    # Allow some config fields to be optional/empty
    empty_allowed = {"prompt_template_path"}
    for config in fields(self):
        if config.name in empty_allowed:
            continue
        attr = getattr(self, config.name)

        if not attr:
            msg = f"Environment variable {config.name.upper()} is not set."
            raise ValueError(msg)


@dataclass(frozen=True)
class PromptServerConfig:
    """A config class containing Github org and repo name environment variables."""

    organisation: str = os.getenv("GITHUB_ORGANISATION", "")
    repo_name: str = os.getenv("GITHUB_REPO_NAME", "")
    project_root: str = os.getenv("PROJECT_ROOT", "")
    # Optional: template path or inline template for diagnose prompt
    prompt_template_path: str = os.getenv("DIAGNOSE_PROMPT_TEMPLATE", "")

    def __post_init__(self) -> None:
        """A post-constructor method for the dataclass."""
        _validate_fields(self)
