"""DeepSeek-compatible chat client with bounded retries and usage logging."""

import asyncio
import json
import os
import time
from pathlib import Path

import httpx

from app import db


class LLMError(RuntimeError):
    pass


class LLMEmptyError(LLMError):
    pass


class LLMResponseError(LLMError):
    pass


def _ensure_dotenv():
    """Load .env fallback if DEEPSEEK_API_KEY was not inherited from process environment."""
    if os.getenv("DEEPSEEK_API_KEY"):
        return
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k and not os.getenv(k):
                os.environ[k] = v


def _log_call(run_id, task_id, data, latency_ms, status, finish_reason=None):
    usage = data.get("usage") or {}
    pin, pout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    cost = (pin * float(os.getenv("LLM_PRICE_IN_PER_M", "0")) + pout * float(os.getenv("LLM_PRICE_OUT_PER_M", "0"))) / 1_000_000
    with db.tx() as c:
        c.execute("""INSERT INTO llm_calls (run_id, task_id, model, prompt_tokens, completion_tokens,
                     finish_reason, latency_ms, status, cost_est) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (run_id, task_id, data.get("model"), pin, pout, finish_reason, latency_ms, status, cost))


async def complete(role, objective, facts, prior, *, run_id=None, task_id=None,
                   client=None, max_retries=3):
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key or key == "PUT_YOUR_KEY_HERE":
        raise LLMError("Missing DEEPSEEK_API_KEY")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    timeout = float(os.getenv("DEEPSEEK_TIMEOUT", "60"))
    backoff = float(os.getenv("DEEPSEEK_BACKOFF_BASE", "1"))
    messages = [
        {"role": "system", "content": (f"You are {role[1]}. {role[2]} Use only supplied facts; "
         "do not claim live data or actions. Reply concisely in Vietnamese; flag assumptions.")},
        {"role": "user", "content": json.dumps(
            {"objective": objective, "facts": facts, "previous_results": prior[-2:]}, ensure_ascii=False)},
    ]
    owns_client = client is None
    transport = client or httpx.AsyncClient(timeout=timeout)
    try:
        for attempt in range(max_retries):
            started = time.monotonic()
            try:
                req_json = {
                    "model": model,
                    "max_tokens": int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000")),
                    "temperature": 0.2,
                    "messages": messages,
                }
                if "flash" in model:
                    req_json["reasoning_effort"] = "low"
                response = await transport.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json=req_json)
                latency = int((time.monotonic() - started) * 1000)
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                content = (choice.get("message") or {}).get("content") or ""
                reason = choice.get("finish_reason")
                if not content.strip():
                    _log_call(run_id, task_id, {**data, "model": data.get("model", model)},
                              latency, "ERROR", reason)
                    raise LLMEmptyError(f"Empty model response (finish_reason={reason})")
                _log_call(run_id, task_id, {**data, "model": data.get("model", model)},
                          latency, "WARN" if reason == "length" else "COMPLETED", reason)
                return content
            except LLMEmptyError:
                raise
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                _log_call(run_id, task_id, {"model": model}, int((time.monotonic() - started) * 1000), f"HTTP_{status_code}")
                retryable = status_code == 429 or status_code >= 500
                if not retryable or attempt + 1 == max_retries:
                    raise LLMResponseError(f"DeepSeek request failed: HTTP {status_code}") from exc
                await asyncio.sleep(backoff * 2 ** attempt)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                _log_call(run_id, task_id, {"model": model}, int((time.monotonic() - started) * 1000), type(exc).__name__)
                if attempt + 1 == max_retries:
                    raise LLMResponseError(f"DeepSeek request failed: {type(exc).__name__}") from exc
                await asyncio.sleep(backoff * 2 ** attempt)
            except (KeyError, ValueError, IndexError, TypeError) as exc:
                _log_call(run_id, task_id, {"model": model}, int((time.monotonic() - started) * 1000), "MALFORMED")
                raise LLMResponseError(f"DeepSeek response malformed: {type(exc).__name__}") from exc
    finally:
        if owns_client:
            await transport.aclose()
