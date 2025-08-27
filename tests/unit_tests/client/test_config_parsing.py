"""Unit tests for ClientConfig env parsing of SERVICES and TOOLS."""

import os
from importlib import reload

from sre_agent.client.utils import schemas as client_schemas


def _set_env(**kwargs: str) -> None:
    """Replace selected env vars and reload module under test."""
    for k in list(os.environ):
        if k in ("SERVICES", "TOOLS", "QUERY_TIMEOUT"):
            os.environ.pop(k)
    for k, v in kwargs.items():
        os.environ[k] = v
    reload(client_schemas)


def test_services_tools_json_arrays():
    """SERVICES/TOOLS JSON arrays are parsed to lists of strings."""
    _set_env(SERVICES='["a","b"]', TOOLS='["x","y"]', QUERY_TIMEOUT="300")
    cfg = client_schemas.ClientConfig()
    assert cfg.services == ["a", "b"]
    assert cfg.tools == ["x", "y"]


def test_services_tools_csv_and_empty():
    """SERVICES as CSV parses, empty TOOLS yields empty list."""
    _set_env(SERVICES="a,b,c", TOOLS="", QUERY_TIMEOUT="300")
    cfg = client_schemas.ClientConfig()
    assert cfg.services == ["a", "b", "c"]
    assert cfg.tools == []
