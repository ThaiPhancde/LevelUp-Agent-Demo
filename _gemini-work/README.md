# Level Up AI Agent Demo — Docker VMM for Windows

This is a **standalone simulator** of 13 agent roles (10 Level Up Blueprint roles + 3 advisory supervisors). It is **not an ARIS runtime**, does not implement agent-to-agent messaging, and does not run 13 isolated containers. QA/Audit/Monitor engines use deterministic rules; supervisor LLM outputs are commentary only.

## Prerequisites

- Docker Desktop 4.86+ with **Settings → General → Virtual Machine Manager → Docker VMM** selected. Docker VMM on Windows is beta.
- Windows virtualization enabled; Linux containers active.
- At least 4 GB memory allocated to the Docker Linux VM (Docker requirement).
- Windows PowerShell; no WSL commands necessary.
- Optional DeepSeek API key from https://platform.deepseek.com/ for real LLM calls. DeepSeek API calls incur costs.

## Setup (PowerShell)

Unzip the archive under `D:\LevelUp-Agent-Demo\` and enter the folder containing `compose.yaml`:

```powershell
cd D:\LevelUp-Agent-Demo\levelup-agent-demo-vmm
docker version
docker compose version
docker context show
docker info --format '{{.OSType}}'
Copy-Item .env.example .env
notepad .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail 50 demo
Invoke-RestMethod http://localhost:8088/health
```

Set `DEEPSEEK_API_KEY` in `.env` (do not commit). Official DeepSeek model used here: `deepseek-v4-flash`.

### No-token functional demo

```powershell
$body = @{ objective = "Demo thi truong Philippines"; inject_error = $true; use_llm = $false } | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri http://localhost:8088/demo/run -ContentType 'application/json' -Body $body
$result.checks | Format-List
Invoke-RestMethod "http://localhost:8088/events/$($result.run_id)"
```

Expected: QA FAIL (synthetic supplier price mismatch), Audit PASS, Monitor PASS. QA rejection should be logged. This is intentional.

### DeepSeek demo (paid API)

```powershell
$body = @{ objective = "Phan tich ke hoach ban thu Philippines"; inject_error = $false; use_llm = $true } | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri http://localhost:8088/demo/run -ContentType 'application/json' -Body $body
$result.checks
```

By default 13 sequential DeepSeek calls per run. Avoid repeated clicks; check API account cost. `MAX_AGENT_CALLS` is reserved for future code, not currently an enforced billing cap.

Web UI for test API: http://localhost:8088/docs (Swagger, not ARIS).

## Persisting state: named volume (VMM-compatible)

The Compose file uses **Docker named volume `demo_data`**, not Windows folder bind mounts. This avoids VMM Windows file sharing complications. Persistence survives `docker compose down` but **not** `docker compose down -v`. To inspect:

```powershell
docker volume ls
docker compose exec demo ls -la /app/data
```

To stop:

```powershell
docker compose down
```

To completely erase test DB (destructive):

```powershell
docker compose down -v
```

## If Docker VMM reports a host path is not shared

Named volumes remove the need to share the DB path. If you later bind mount a host folder (`D:\...`), open Docker Desktop → Settings → Resources → File sharing (or Shared Folders, if UI uses that name), add only the exact project folder and Apply & Restart.

## Integrating real ARIS later

1. Clone `https://github.com/tauhb/aris-agent` into `D:\aris-agent`.
2. Validate `pnpm install --frozen-lockfile`, build and test using Node >=22.19 and pnpm 10.
3. ARIS's current `@aris/keychain` plugin calls macOS `/usr/bin/security` and must be adapted to the standard DeepSeek Harness credential provider for Linux before attempting a Docker VMM Linux deployment.
4. Add an ARIS adapter for a mock tool gateway and configure 10 business roles + 3 supervisory roles.
5. Build workflow-level policy enforcement and real cross-agent reviews; this starter does not implement them.

Never expose the demo publicly, connect live payment/Meta accounts, or mount Docker socket inside untrusted agent containers.
