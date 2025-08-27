"""Utilities for parsing GitHub-like repository URLs."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ParsedRepo:
    """Parsed components of a repository URL."""

    host: str
    organisation: str
    repo_name: str
    branch: str | None = None
    project_root: str | None = None


def parse_github_url(repo_url: str) -> ParsedRepo:
    """Parse GitHub-like URLs into organisation, repo, optional branch and path.

    Supports:
      - HTTPS: https://host/org/repo[.git][/tree/<branch>/<path...>] |
        [/blob/<branch>/<path...>]
      - SSH:   git@host:org/repo.git
    """
    repo_url = repo_url.strip()

    # SSH form: git@host:org/repo(.git)
    if repo_url.startswith("git@"):
        _, rest = repo_url.split("@", 1)
        host, path = rest.split(":", 1)
        parts = path.strip("/").split("/")
        org = parts[0]
        repo = parts[1].removesuffix(".git")
        return ParsedRepo(host=host, organisation=org, repo_name=repo)

    # HTTPS and others
    parsed = urlparse(repo_url)
    host = parsed.netloc or parsed.path.split(":")[0]  # handle host:path
    path_parts = parsed.path.strip("/").split("/") if parsed.path else []
    min_parts_for_repo = 2
    if len(path_parts) < min_parts_for_repo:
        raise ValueError("Invalid repository URL: expected /<org>/<repo>")

    org = path_parts[0]
    repo = path_parts[1].removesuffix(".git")

    # Optional branch + path
    branch = None
    project_root = None

    tree_blob_marker_index = 2
    branch_index = 3
    root_start_index = 4
    if len(path_parts) >= tree_blob_marker_index + 1 and path_parts[
        tree_blob_marker_index
    ] in ("tree", "blob"):
        if len(path_parts) >= branch_index + 1:
            branch = path_parts[branch_index]
        if len(path_parts) >= root_start_index + 1:
            project_root = "/".join(path_parts[root_start_index:])

    return ParsedRepo(
        host=host,
        organisation=org,
        repo_name=repo,
        branch=branch,
        project_root=project_root,
    )
