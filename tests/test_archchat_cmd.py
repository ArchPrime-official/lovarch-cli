"""Unit tests for archchat read-only helper."""
from __future__ import annotations

import httpx

from lovarch_cli.commands.archchat_cmd import _get


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows
        self.last = None

    async def request(self, method, path, *, params=None, **kw):
        self.last = {"path": path, "params": params}
        return httpx.Response(200, json=self._rows, request=httpx.Request(method, "http://x" + path))


async def test_get_returns_list():
    s = _FakeSession([{"id": "a", "title": "T"}])
    out = await _get(s, "/rest/v1/archchat_conversations", {"select": "id"})
    assert out == [{"id": "a", "title": "T"}]
    assert s.last["path"].endswith("archchat_conversations")


async def test_get_non_list_returns_empty():
    s = _FakeSession({"error": "x"})
    out = await _get(s, "/rest/v1/archchat_messages", {})
    assert out == []
