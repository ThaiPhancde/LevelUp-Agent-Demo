# 06 — Work order: dashboard UX pass, business wording and "Tổng quan" left rail (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner feedback (2026-11-05): "use business wording instead of codes like
> bad_cost or run UUIDs"; "the left part is not similar enough to the reference". Claude 60 / Gemini 40.
> Executor: one headless `agy -p` run (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude in a real browser, never the executor's own report.

## 1. What you are producing

A rework of `app/web/panels.js` and `app/web/styles.css` (both exist; you wrote the first version). Two goals:

**A. Business wording.** People read business words, not codes. Every user-visible text that is a technical code
(status codes, task keys, rule codes, injection ids, run UUIDs, English field names) must go through the
dictionary in `app/web/labels.js` (read it fully; do NOT edit it). Technical values stay available as `title`
tooltips, as `data-*` attributes, and inside a collapsed "Chi tiết kỹ thuật" element — never as the main text.

**B. Left rail = "Tổng quan".** Replace the current left column (start form always open) with an overview card in
the spirit of a kanban-style control panel: a title "Tổng quan", a subtitle line, a row of 4 counter tiles, and a
scrollable work list. The start form moves behind a button. Design it yourself with the same pastel style as the
rest; this is an original layout, do not imitate any real product's branding.

Read before working, in this order (only these):
1. `app/web/labels.js` — all wording (STATUS/TASK/AGENT/SCENARIOS/RULE/DECISION/ACTION/TOOL labels, `errorText`,
   `scenarioText`, `runTitle`, `formatTime`, `overviewCounts`).
2. `app/web/panels.js` and `app/web/styles.css` — current code. Keep everything that works; keep the bottom-dock
   resize code (`dock-grip`, `toggle-dock`, `DOCK_KEY`, `setDock`) exactly as is.
3. `app/web/main.js` — handler contract (unchanged; do not edit).
4. `ai-jobs/p6b-ux/sample_runs.json` — real API payloads (`run.seq` is the friendly run number, `runs_list[].inject`
   lists simulated situations).

## 2. Hard rules

You MUST:
- Edit only `app/web/panels.js` and `app/web/styles.css`.
- Keep the public contract: `createPanels(root, handlers)` returning `setAgents, render, renderHistory, selectTask,
  setView, showError`; the same handler calls as today (`onStart({objective, mode, inject})`, `onRetry`, `onCancel`,
  `onApprove`, `onOpenRun`, `onToggle`, `onResetCamera`, `onView`, `onRefreshHistory`). The `inject` array must still
  contain the API strings (`bad_cost`, `publish_attempt`, `timeout:<task>`, `missing_field:<task>`,
  `empty_response:<task>`).
- Keep `textContent` / `createElement` only for untrusted text; no `innerHTML` except `= ''`; no external URLs, no
  `eval`, no inline event attributes, `import` allowed only for `./labels.js`.
- Keep these stable hooks (tests use them): `[data-action="start-demo"]` on the top-bar button, `[data-action="retry-task"]`,
  `[data-action="approve"]`, `[data-action="reject"]`, `[data-action="cancel-run"]`, `[data-action="refresh-history"]`,
  tabs with `role="tab"`, `.drawer-panel`, `.office-label` untouched, SVG nodes with `aria-label^="Bước "`.
- Add these new hooks: run status badge in the top bar gets `data-run-status="<API code>"`; decision badge
  `data-decision="<code>"`; every PASS/WARN/FAIL badge `data-check-status="<code>"`; every task chip
  `data-task-status="<code>"`; engine finding rows `data-rule="<rule code>"`.
- Run `python -I ai-jobs/p6b-ux/checker.py left-rail-wording .` until it exits 0 (max three rounds).

You MUST NOT: edit any other file; call the API from panels (the only `fetch` allowed is the read-only decision log);
touch `window.__officeFps`, 3D code or the dock resize code; leave any text from the forbidden list in section 5.

## 3. Style

Same pastel cards as now. The overview card: rounded, soft shadow, 330 px wide, no taller than the rail (the rail
scrolls). Tiles are 2×2 or 4×1 depending on width, big number + small label, number turns red when "Lỗi" > 0 and
amber for "Chờ duyệt" > 0. Status chips use the status colours already in `:root`. Everything keyboard reachable,
visible focus rings, works at 960×520 and 1920×1080, respects `prefers-reduced-motion`.

## 4. Brief

### 4.1 Left rail (card "Tổng quan")

- Header: title `Tổng quan`; subtitle `Lượt #<seq> · <scenarioText(run.inject)>` (or `Chưa có lượt nào` when no run);
  a primary button `▶ Chạy kịch bản mới` that opens/closes the start form (aria-expanded).
- 4 tiles from `overviewCounts(run)`: `Đang làm` (running), `Chờ làm` (todo), `Chờ duyệt` (awaiting), `Lỗi` (failed).
- If there is a pending approval, show it on top of the list as a highlighted item titled `Chờ người duyệt` with the
  reason, amount, and the existing Duyệt / Từ chối buttons (keep the current approval logic and hooks).
- Work list titled `Việc của lượt này`: one row per task in graph order — small number `#<n>`, title `TASK_TITLE`, role
  `AGENT_ROLE`, status chip `TASK_STATUS_LABEL` (+ short `errorText` under failed/skipped rows). Click or Enter opens the
  drawer for that task (existing `selectTask`). Rows of the task currently open in the drawer are highlighted.
- Start form (collapsed by default, remembered open state not required): `Mục tiêu kinh doanh` textarea (keep the
  default text), mode radios `Mô phỏng (mặc định, miễn phí)` / `Dùng DeepSeek (có tính phí)` — keep the existing warning
  about cost and the 2-call limit when DeepSeek is chosen — then `Tình huống thử` with one checkbox per `SCENARIOS`
  entry (label from the dictionary, `hint` as small helper text, a task select for `needsTask` ones listing
  `TASK_TITLE`), buttons `Chạy` (calls the same handler as the top bar) and `Bỏ chọn tất cả`. Remove the
  `inject: [...]` debug line. Show a one-line summary of the chosen situations using `scenarioText`.

### 4.2 Business wording everywhere else

- Top bar: brand `Văn phòng Level Up` with subtitle `đội 13 AI agent bán hàng`; keep the `MOCK ONLY — dữ liệu giả lập`
  badge; run badge text from `RUN_STATUS_LABEL`; progress `Bước n/14` stays.
- Drawer: heading `<AGENT_ROLE> · <TASK_TITLE>`; fields `Trạng thái`, `Số lần thử`, `Bắt đầu`, `Kết thúc` (use
  `formatTime`), error via `errorText`; sections `Đầu vào` (kết quả của các bước trước, by `TASK_TITLE`) and
  `Đầu ra` (diễn giải + collapsed `Chi tiết kỹ thuật (JSON)`); Retry button text `Thử lại bước này` (keep the hook).
- Bottom tabs: `Kết quả cuối` (decision `DECISION_LABEL` + `DECISION_HINT`, key numbers table with only the meaning
  and value columns; the raw key goes into `title`), `Kiểm tra` (rename of the engines tab: three departments from
  `ENGINE_LABEL` with `CHECK_STATUS_LABEL` badges; findings table columns `Bộ phận`, `Vấn đề` (`RULE_LABEL`), `Mức độ`
  (`SEVERITY_LABEL`), `Bước` (`TASK_TITLE`), `Chi tiết kỹ thuật` (raw detail, small muted text)), `Token & chi phí`
  (rows by task title, source via `LLM_SOURCE_LABEL`), `Nhật ký` (action via `ACTION_LABEL`, tool via `TOOL_LABEL`,
  `allowed` as `Cho phép` / `Chặn`, step as `TASK_TITLE`; raw codes in `title`), `Lịch sử`.
- History table: columns `Lượt` (`#<seq>`), `Tình huống` (`scenarioText`), `Kết quả` (`RUN_STATUS_LABEL` chip), `Thời gian`
  (`formatTime`); no UUID anywhere; the row keeps `data-run-id`; current row highlighted. Header text:
  `Các lượt chạy — bấm một dòng để xem lại (không chạy lại agent, không tốn lời gọi AI)`.
- 2D overview: node labels and table columns use `TASK_TITLE` / `AGENT_ROLE` / `TASK_STATUS_LABEL`; column
  `Phụ thuộc` lists titles; keep the SVG `aria-label^="Bước "` on nodes.
- Toasts and empty states in plain Vietnamese.

## 5. Forbidden visible text (checker greps string literals)

`(Objective)`, `(Mode)`, `Error Injection`, `inject:`, `(attempt)`, `(decision)`, `(key)`, `(task_key)`, `(detail)`,
`(depends_on)`, `HITL`, `Artifact`, `Phase 5`, `engine`, `run_id` as displayed text, and any literal English status word
(`COMPLETED`, `FAILED`, `PENDING`, `RUNNING`, `SKIPPED`, `CANCELLED`, `WAITING_APPROVAL`, `PASS`, `FAIL`, `WARN`) used
as visible `textContent`. Codes are fine as `data-*`, `title`, object keys, comparisons and CSS class names.

## 6. Report back

Output paths, checker last line, anything not done, "SUSPECTED BUGS" in Claude's files (or "none").

## 7. Acceptance (Claude)

Real browser (1440×900 and 960×520): overview tiles update live during a run, work list rows and drawer open, start
form opens and runs a scenario, no code-like text on screen, approval flow, history without UUIDs, 2D overview,
bottom dock still resizes. Claude updates the E2E script to the new wording. One row in `ai-jobs/LEDGER.md`.

## 8. Result

<Filled in by Claude after acceptance.>
