# 05 — Work order: Phase 8 browser E2E script (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner ruling: Claude 60 / Gemini 40.
> Executor: one headless `agy -p` run (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude runs the script against a real container, never the executor's own report.

## 1. What you are producing

A local demo where 13 simulated AI agents cooperate on a **synthetic** sales scenario, shown in a
browser dashboard at `/dashboard` (3D office + panels, or a 2D overview with `?mode=2d`). You write one
**Node.js script that drives Chromium with the `playwright` library** and checks the dashboard end to
end. Claude runs it inside the official Playwright Docker image against a fresh demo container.

Read before working, in this order (only these):
1. `app/web/panels.js` and `app/web/dashboard.html` — the DOM you drive (use the `data-action`
   attributes, ARIA labels and visible Vietnamese texts you find there).
2. `app/web/office3d.js` — 3D labels are HTML elements with class `office-label` (text like
   `✓ 02 · Thị trường & Sản phẩm`); the gateway alert bubble has class `office-bubble--alert`.
3. `app/web/main.js` — how runs are started and polled (every 1 s).
4. `ai-jobs/p6-dashboard/sample_runs.json` — what the API returns.

## 2. Hard rules

You MUST:
- Write exactly one file: `tests/e2e/browser/dashboard.e2e.mjs` (ES module, Node 18+).
- Import only `playwright` (`import { chromium } from 'playwright'`) and Node built-ins (`node:fs`,
  `node:path`, `node:process`, `node:assert/strict`).
- Read the base URL from `process.env.E2E_BASE_URL` (default `http://127.0.0.1:8090`) and the screenshot
  folder from `process.env.E2E_SHOTS` (default `./shots`); create the folder.
- Launch Chromium headless with args `['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']`,
  viewport 1440×900.
- Run the scenarios in section 4 **sequentially**, each in its own `try/catch`, record
  `{name, ok, ms, error?}`, take one PNG screenshot per scenario (`<n>-<name>.png`), and keep going
  after a failure.
- Collect browser console messages of type `error` and page errors; ignore messages that contain
  `favicon`. Report them as a separate check `no-console-errors`.
- At the end print exactly one line `E2E_RESULT <json>` where json is
  `{"passed": <int>, "failed": <int>, "results": [...]}`, then exit with code 0 if all passed else 1.
- Wait with Playwright's auto-waiting (`locator.waitFor`, `expect`-style polling with `page.waitForFunction`)
  and explicit timeouts (≤ 30 s per wait). Never use fixed sleeps longer than 1 s.
- Run `python -I ai-jobs/p8-e2e/checker.py browser-e2e .` and fix until it exits 0 (max three rounds).
  The checker only checks syntax and required structure; it cannot run the browser.

You MUST NOT: edit any other file; use git, npm, docker or network beyond the base URL; call the REST API
directly to make a scenario pass (scenarios must be driven through the UI; reading text from the page is
how you assert). Exception: `GET /runs?limit=1` is allowed only to read the latest `run_id` for logging.

## 3. Style

Small helper functions (`startDemo(page, injections)`, `waitForRunStatus(page, statuses)`, `openTask(page, key)`),
clear scenario names, comments in English, no frameworks.

## 4. Scenarios (drive through the UI)

The container under test runs Mock Mode with no LLM key and no step delay, so a run finishes within a few
seconds. Start each scenario by loading `/dashboard` fresh.

1. `load` — page title contains `Văn phòng Level Up`; the badge `MOCK ONLY` is visible; text `13 agent` is visible;
   the start form's Mock radio is checked by default.
2. `happy-path` — clear all injection checkboxes, click the start button (`[data-action="start-demo"]` or the
   form's "Start Demo ▶"); wait until the run status badge shows `COMPLETED` and `Bước 14/14`;
   open tab "Kết quả cuối" and assert it shows `HOLD_DRAFT` and `LU-PH-001`.
3. `timeout-then-retry` — tick the `timeout:` injection (its task select defaults to `market`), start; wait for
   status `FAILED`; open the market task's drawer (click the `.office-label` containing `02 ·` if present,
   otherwise the 2D node / table row for `market`); assert the drawer shows `timeout`; click the Retry button
   (`[data-action="retry-task"]`); wait for status `COMPLETED`.
4. `publish-blocked` — tick `publish_attempt`, start; wait for `COMPLETED`; open tab "QA / Audit / Monitor" and assert
   it contains `blocked_action`; if `.office-bubble--alert` exists assert it contains `Chặn publish`.
5. `qa-bad-cost` — tick `bad_cost`, start; wait for `COMPLETED`; open "QA / Audit / Monitor" and assert it contains
   `reference` and `9999`; open "Kết quả cuối" and assert `NEEDS_REVIEW`.
6. `overview-2d` — load `/dashboard?mode=2d`; assert `#office` is hidden, the SVG graph has 14 task nodes
   (`[aria-label^="Bước "]` inside the SVG) and the status table has a row for `summary`;
   assert no toast saying `Không tải được chế độ 3D`.
7. `history-replay` — open tab "Lịch sử", click the second history entry, assert the status badge changes to that
   run's status without starting a new run (count history entries before/after: unchanged).
8. `no-console-errors` — the collected console/page errors list is empty.

## 5. Report back

Output path, checker last line, scenario list, anything you could not do, "SUSPECTED BUGS" in the UI (or "none").

## 6. Acceptance (Claude)

Claude runs the script in `mcr.microsoft.com/playwright:v1.48.2-jammy` against a fresh container and reads every
screenshot. One row in `ai-jobs/LEDGER.md`.

## 7. Result

2026-11-05: job exit 0, 502 s, no stray write, no suspected bugs. Run by Claude via tools/e2e/run_e2e.py:
8/8 scenarios passed, screenshots read (3D renders under SwiftShader). Assertions check real content, not just presence.
