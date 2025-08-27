"""Unit tests for parse_github_url utility parsing various formats."""

from sre_agent.servers.prompt_server.utils.url_parser import parse_github_url


def test_parse_https_minimal():
    """HTTPS minimal org/repo without branch or path."""
    p = parse_github_url("https://github.com/org/repo")
    assert p.host == "github.com"
    assert p.organisation == "org"
    assert p.repo_name == "repo"
    assert p.branch is None
    assert p.project_root is None


def test_parse_https_tree_with_path():
    """HTTPS /tree/<branch>/<path> is parsed correctly."""
    p = parse_github_url("https://github.com/org/repo/tree/main/services/web")
    assert p.organisation == "org"
    assert p.repo_name == "repo"
    assert p.branch == "main"
    assert p.project_root == "services/web"


def test_parse_https_blob_with_path():
    """HTTPS /blob/<branch>/<path> is parsed correctly."""
    p = parse_github_url("https://github.com/org/repo/blob/release/app/file.py")
    assert p.branch == "release"
    assert p.project_root == "app/file.py"


def test_parse_ssh():
    """SSH git@host:org/repo.git is parsed correctly."""
    p = parse_github_url("git@github.company.com:team/repo.git")
    assert p.host == "github.company.com"
    assert p.organisation == "team"
    assert p.repo_name == "repo"
