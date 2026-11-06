import httpx
import pytest

from app.llm.deepseek import LLMEmptyError, LLMResponseError, complete


def payload(content="Xin chào", finish_reason="stop", usage=None):
    return {"model": "test-model", "choices": [{"message": {"content": content}, "finish_reason": finish_reason}],
            "usage": usage or {"prompt_tokens": 3, "completion_tokens": 4}}


async def test_success_and_length(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    responses = [httpx.Response(200, json=payload("Đã xong")), httpx.Response(200, json=payload("Cắt ngắn", "length"))]
    async def handler(request): return responses.pop(0)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await complete(("01", "Commander", "plan"), "mục tiêu", {"x": "á"}, [], client=client) == "Đã xong"
        assert await complete(("01", "Commander", "plan"), "mục tiêu", {}, [], client=client) == "Cắt ngắn"


@pytest.mark.parametrize("status", [429, 500])
async def test_retries_http_errors(monkeypatch, status):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    calls = 0
    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMResponseError): await complete(("01", "x", "y"), "o", {}, [], client=client, max_retries=3)
    assert calls == 3


async def test_timeout_retries(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    calls = 0
    async def handler(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timed out", request=request)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMResponseError):
            await complete(("01", "x", "y"), "o", {}, [], client=client, max_retries=3)
    assert calls == 3

async def test_empty_response_fails(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    async def handler(request): return httpx.Response(200, json=payload("", "stop"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMEmptyError): await complete(("01", "x", "y"), "o", {}, [], client=client)


async def test_failed_attempts_are_logged_for_monitoring(monkeypatch):
    from app import db
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    async def handler(request): return httpx.Response(503, json={})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMResponseError):
            await complete(("09", "x", "y"), "o", {}, [], run_id="log-run", task_id="09", client=client, max_retries=2)
    with db.tx() as c:
        rows = [r["status"] for r in c.execute("SELECT status FROM llm_calls WHERE run_id='log-run'")]
    assert rows == ["HTTP_503", "HTTP_503"]


async def test_vietnamese_text_survives_sqlite_and_api_utf8():
    """DEMO_DECISIONS M-04: bytes must be UTF-8 end to end; mojibake in PowerShell output is display only."""
    from httpx import ASGITransport, AsyncClient
    from app import db
    from app.main import app
    text = "Đề xuất kế hoạch bán thử — Phân tích thị trường"
    db.log_event("utf8-run", "Commander", "probe", {"text": text})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/events/utf8-run")
    assert resp.headers["content-type"].startswith("application/json")
    assert text.encode("utf-8") in resp.content
    assert resp.json()[0]["detail"]["text"] == text
