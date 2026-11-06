import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_phase0_smoke_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        assert len((await client.get("/agents")).json()) == 13
        assert (await client.get("/sample")).json()["market"] == "Philippines"
        response = await client.post("/demo/run", json={"use_llm": False})
        assert response.status_code == 200
        body = response.json()
        assert len(body["outputs"]) == 14
        assert (await client.get(f"/events/{body['run_id']}")).status_code == 200
