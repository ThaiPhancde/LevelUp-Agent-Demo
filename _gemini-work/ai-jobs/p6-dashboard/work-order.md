# 04 — Work order: Phase 6 dashboard UI (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner ruling: Claude 60 / Gemini 40; dashboard = 3D office (D-16).
> Executor: one headless `agy -p` run per job (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude in a real browser, never the executor's own report.

## 1. What you are producing

A local demo where 13 simulated AI sales agents cooperate on a **synthetic** scenario. The dashboard at
`/dashboard` shows them as an isometric **3D office** (Claude writes the 3D scene) with control panels
around it (you write them). Everything is offline: no CDN, no external URL, no framework, no build step.

Read before working, in this order (only these):
1. `docs/DEMO_DASHBOARD_3D.md` — the design spec (sections 1–4 for `panels-ui`, section 2 for `office-props`).
2. `app/web/main.js` — how your module is called (the contract in section 4 below is binding).
3. `app/web/office-layout.js` — zones, rooms, colours, status styles (reuse its colours and labels).
4. `ai-jobs/p6-dashboard/sample_runs.json` — real API payloads: `happy`, `timeout`, `publish_blocked`,
   `waiting_approval` (each is the body of `GET /runs/{id}`), `agents` (`GET /agents`), `runs_list` (`GET /runs`).
5. Your brief in section 4.

## 2. Hard rules

You MUST:
- Write only the files listed in your brief.
- Vietnamese UI text; keep technical status words in English (PENDING, RUNNING, COMPLETED, FAILED,
  SKIPPED, CANCELLED, PASS, FAIL, WARN, DRAFT, HOLD_DRAFT, NEEDS_REVIEW, DRAFT_READY).
- Put untrusted text (objective, narrative, errors, findings, artifact JSON) into the DOM with
  `textContent` / `createElement` only. `innerHTML` is allowed only to clear an element (`= ''`).
- Show only data present in the payloads. Never invent numbers or statuses.
- Run `python -I ai-jobs/p6-dashboard/checker.py <your-job-id> .` until it exits 0 (max three rounds).

You MUST NOT: edit other files (not `main.js`, not `office3d.js`, not `office-layout.js`); use git, pip,
npm, docker or network; load anything from the internet; use `eval`, `new Function`, frameworks or
inline event attributes (`onclick=`).

## 3. Style

Light, friendly, readable — like a pastel toy-town dashboard: cream background, rounded cards with
soft shadow, zone colours from `office-layout.js`, system font stack, 14px base. Panels float over the
full-screen 3D canvas and must not cover its centre. Visible focus rings; respect
`prefers-reduced-motion`; works at 1280×720 and up; on narrow screens panels stack and the 3D area shrinks.

## 4. Briefs

### 4.1 `panels-ui`

- Outputs: `app/web/dashboard.html`, `app/web/styles.css`, `app/web/panels.js`.
- `dashboard.html` `<head>` must contain exactly these two script tags (and the stylesheet link):
  ```html
  <script type="importmap">{"imports":{"three":"/static/vendor/three.module.min.js","three/addons/":"/static/vendor/"}}</script>
  <script type="module" src="/static/main.js"></script>
  <link rel="stylesheet" href="/static/styles.css">
  ```
  `<body>` must contain `<div id="office" aria-label="Văn phòng 3D"></div>` (Claude's canvas host,
  leave it empty, full-screen behind the panels) and `<div id="app"></div>` (your panels root).
  `main.js` sets `document.body.dataset.view` to `3d` or `2d`; in `2d` hide `#office` with CSS and show
  your 2D overview instead.
- `panels.js` must `export function createPanels(root, handlers)` and return an object with:
  `setAgents(agents)`, `render(run)`, `renderHistory(runs)`, `selectTask(taskKey)`, `setView(mode)`,
  `showError(message)`. `run` is a `GET /runs/{id}` body (see samples); `render` is called every second
  while a run is active, so it must update in place without losing the open drawer or tab, and be cheap.
- Call the handlers (never `fetch` for actions): `handlers.onStart({objective, mode, inject})`,
  `onRetry(taskKey)`, `onCancel()`, `onApprove(approvalId, 'APPROVED'|'REJECTED')`, `onOpenRun(runId)`,
  `onToggle(option, value)` with option `rotate` | `labels` | `bubbles`, `onResetCamera()`,
  `onView('3d'|'2d')`, `onRefreshHistory()`. The only `fetch` allowed in your code is a read-only
  `GET /runs/{id}/decision-log` when the "Nhật ký" tab is opened.
- Must contain (spec sections 3–4):
  1. **Top bar**: product name "Văn phòng Level Up", a permanent badge "MOCK ONLY — dữ liệu giả lập",
     run status badge, "13 agent", "Bước n/14" (n = tasks in COMPLETED/FAILED/SKIPPED/CANCELLED),
     toolbar buttons: Tự xoay/Dừng xoay (toggle), Tên (toggle), Bong bóng (toggle), Toàn cảnh,
     Tổng quan (switch 3D↔2D), and the **Start Demo ▶** button.
  2. **Start form** (collapsible card): objective textarea (default text = the objective in the samples),
     mode radio **Mock (mặc định)** / **DeepSeek** — choosing DeepSeek shows a warning that it costs money
     and the demo allows at most 2 real calls; error-injection controls for `bad_cost`,
     `publish_attempt`, and `timeout:` / `missing_field:` / `empty_response:` each with a task select of
     the 14 task keys (labels from agents). Build the `inject` array exactly in those string formats.
  3. **Drawer** (right side, opened by `selectTask` or by clicking a row/node): agent name and role,
     status with icon, attempt, start/finish time, error, **Retry** button only when status is FAILED and
     run status is FAILED, **Đầu vào** (artifacts of the task's `depends_on` tasks from the same run,
     collapsible JSON), **Đầu ra** (its own artifact as collapsible pretty JSON + its `narrative`).
  4. **Bottom tabs**: **Kết quả cuối** (summary artifact: decision, key_numbers table, next_steps,
     narrative); **QA / Audit / Monitor** (from `run.engines`: status badge + findings table rule,
     severity, task_key, detail); **Token & chi phí** (`run.llm` calls/tokens/cost_est and each task's
     `artifact.narrative_source`); **Nhật ký** (decision log table: ts, task_key, agent_id, action, tool,
     allowed); **Lịch sử** (`renderHistory` list; clicking calls `onOpenRun`; a refresh button calls
     `onRefreshHistory`). A **Cancel** button shows while the run is PENDING/RUNNING/WAITING_APPROVAL.
  5. **Approvals**: when `run.approvals` has a PENDING item, show a highlighted card with reason, amount
     and **Duyệt** / **Từ chối** buttons.
  6. **2D overview** (`setView('2d')`): an inline SVG graph of the 14 tasks laid out in dependency
     layers (`depends_on`), edges as arrows, nodes coloured by status with the status icon; clicking a
     node opens the drawer; plus a compact status table. This view alone must give all 10 DEMO_ONLY
     Phase 6 capabilities (spec section 4).
  7. `showError` shows a dismissible toast.

### 4.2 `office-props`

- Output: `app/web/office-props.js` exporting `export const PROPS = { '01': [...], ..., '13': [...], gateway: [...] }`.
- Each item: `{ shape, size, pos, color, label? }` where `shape` is `box` (size `[w, h, d]`), `cylinder`
  or `cone` (size `[radius, height]`) or `sphere` (size `[radius]`); `pos` = `[x, y, z]` relative to the
  room centre with `y` the bottom of the shape (0 = floor); `color` = `#rrggbb`; optional `label` (short
  Vietnamese, shown only on hover — keep ≤ 24 chars).
- 4–10 items per room, at most 12 for `gateway`. Everything must stay inside the room footprint
  (`|x| + half width <= w/2 - 0.3`, same for z) and below height 3. Keep the centre `|x|,|z| < 0.9`
  free (the agent's desk and character go there). Use the zone colour from `office-layout.js` as accent.
- Ideas per room from spec section 2: map of Philippines (flat box), shelf with 3 product boxes,
  price board, easel, camera, campaign screen with a DRAFT colour, phone, parcel boxes, delivery
  scooter (simple shapes), bar chart (3–4 boxes of different heights), safe, 3 control consoles with
  lamps in the supervision rooms, plants and lamps everywhere; for `gateway` (centre = `GATEWAY`): two
  pillars and a horizontal barrier bar, a small booth.

## 5. Report back

Job id, output paths, checker last line, anything not done, "SUSPECTED BUGS" in Claude's files (or "none").

## 6. Acceptance (Claude)

Runner clean; checker rerun; Claude opens `/dashboard` in a real browser, runs Mock happy path,
`timeout:market` + Retry, `publish_attempt`, approval flow, 2D view; reads all UI text; one row in
`ai-jobs/LEDGER.md`.

## 7. Result

2026-11-05: 2/2 jobs exit 0 (605 s / 248 s), no stray write, no suspected bugs. Checker OK x2; suite 435 passed.
Browser acceptance by Claude (Playwright, 1440x900): happy path, timeout:market + Retry from the drawer,
publish_attempt (gateway turns red), approval card -> Duyệt -> COMPLETED, ?mode=2d. Claude fixes in Gemini files:
`[hidden]{display:none!important}` (Cancel showed on a FAILED run), null shown as a dash, `.dag-svg-wrapper` flex-shrink 0.
