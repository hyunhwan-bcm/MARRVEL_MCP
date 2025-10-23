import pytest
import httpx
import asyncio
from types import SimpleNamespace

from src.utils.api_client import fetch_marrvel_data


class DummyResponse:
    def __init__(self, text, status_code=200, headers=None):
        self._text = text
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        # Simulate synchronous raise_for_status
        if 400 <= self.status_code < 600:
            raise httpx.HTTPStatusError("HTTP error", request=None, response=None)
        return None

    def json(self):
        # Will not be called in this test (content is HTML)
        raise ValueError("Not JSON")

    @property
    def text(self):
        return self._text


class DummyClient:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        return self._response


@pytest.mark.asyncio
async def test_html_response_detected(monkeypatch):
    html = "<!doctype html><html><body>App shell</body></html>"
    dummy_resp = DummyResponse(html, status_code=200)

    async def dummy_client_factory(*args, **kwargs):
        return DummyClient(dummy_resp)

    # Patch httpx.AsyncClient to use our dummy client
    monkeypatch.setattr(
        "src.utils.api_client.httpx.AsyncClient", lambda **kwargs: DummyClient(dummy_resp)
    )

    result = await fetch_marrvel_data("/data/gtex/gene/entrezI/7157")

    assert isinstance(result, dict)
    assert result["error"] == "Unexpected HTML response from API"
    assert result["status_code"] == 400
    assert "content_preview" in result
