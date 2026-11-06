# 03 — Work order: Phase 5 engine tests (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner ruling: Claude 60 / Gemini 40.
> Executor: one headless `agy -p` run per job (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude, never the executor's own report.

## 1. What you are producing

A local demo where 13 simulated AI agents cooperate on a **synthetic** Philippines sales scenario.
Three deterministic "engines" check the agents' work without any LLM. You write table-driven pytest
files for them, plus tests for the new "soft dependency" rules in the task graph.

Read before working, in this order (only these):
1. The module(s) under test named in your brief, completely (docstrings define the rules).
2. `app/core/artifacts.py` (artifact SPEC), `app/core/registry.py` (permissions), `app/mock/fixtures.json`.
3. `ai-jobs/p4-agents/sample_flat.json` only as an orientation of real values (it is flattened).
4. `tests/test_graph_table.py`: style to match.
5. Your brief in section 4.

## 2. Hard rules

You MUST:
- Write exactly the one file named in your brief, nothing else.
- Write expected values as literals derived by hand from the docstrings and fixtures. Never call the
  function under test to produce an expectation. If the code disagrees with the docstring, keep the
  docstring expectation, let the test fail, and report it under "SUSPECTED BUGS". Do not edit code.
- Build input artifacts by hand as plain dicts (a small helper returning a consistent valid set is fine);
  for QA they must satisfy `app/core/artifacts.py` SPEC so that only the rule you target fires.
- Run `python -I ai-jobs/p5-engines/checker.py <your-job-id> .` until it exits 0 (max three rounds).

You MUST NOT: edit other files; use git, pip, docker or network; import anything except `pytest`,
`copy`, `json`, `math`, `pathlib`, `os` and the modules under test; invent products or brands.

## 3. Style

`@pytest.mark.parametrize` with `ids=`, one idea per test, helper builders with `copy.deepcopy`.

## 4. Briefs

### 4.1 `qa-tests`

- Output: `tests/test_engine_qa_table.py`. Import `from app.engines import qa`.
- Build one fully consistent valid artifact set for the 9 BUSINESS tasks using the real scenario
  numbers (LU-PH-001: price 499, cost 180, shipping 75, fee 18, margin 226, break-even 18 with budget
  4000, 100 leads / 20 confirmed / 15 delivered / 2 returned, net units 13, net revenue 6487, ROAS 1.62,
  contribution 2938 before ads and -1062 after). Check it gives `qa.run(...)['status'] == 'PASS'` with
  no findings, using `ref_facts` loaded from `app/mock/fixtures.json`.
- At least **35 cases**: each rule `schema` (missing artifact; missing field; rejected artifact text
  appears in detail), `reference` (offer cost 9999; a candidate cost differs), `arithmetic` (wrong
  margin; wrong break-even; break-even 0 when margin <= 0; wrong net revenue; wrong roas; wrong
  contribution before/after; unconfirmed mismatch; values within 0.01 tolerance pass), `consistency`
  (sku mismatch per task; budget mismatch; spend mismatch; margin mismatch; campaign not DRAFT),
  `narrative` (number not in artifact → WARN only, status WARN; number present passes; comma decimal
  "45,29" matches 45.29), and `status()` (FAIL beats WARN; empty → PASS).

### 4.2 `audit-monitor-tests`

- Output: `tests/test_engine_audit_monitor_table.py`. Import `from app.engines import audit, monitor`.
- At least **35 cases**:
  - `audit.check_action` for agents 02/06/07/08/11 × tools `meta_ads.create_draft`, `meta_ads.publish`,
    `crm.reply_draft`, `crm.ticket_note`, `payment.charge`, `messaging.send`, `mock.market`, an unknown
    tool; decision ALLOW / BLOCK, and NEEDS_APPROVAL for agent 06 `meta_ads.create_draft` with
    `budget_php` 5000 and 9000 (threshold default 5000, use `monkeypatch.delenv('APPROVAL_THRESHOLD_PHP', raising=False)`),
    ALLOW at 4999; a monkeypatched threshold of 3000 turns 4000 into NEEDS_APPROVAL.
  - `audit.run`: clean tool calls → PASS; a BLOCK decision → FAIL rule `blocked_action`; NEEDS_APPROVAL
    → WARN rule `pending_approval`; a requested action with no matching tool call → FAIL `not_via_gateway`;
    campaign status not DRAFT → FAIL `draft_only`.
  - `monitor.classify` (timeout / empty / other) and `monitor.run`: all completed → PASS; timeout → FAIL
    rule `timeout`; "Empty model response" and "empty narrative" → `empty_response`; other error →
    `task_failed`; SKIPPED → WARN; attempt 2 completed → WARN `retried`; llm errors → WARN;
    `mock_budget` narrative source → WARN `token_budget`; `monitor`/`summary` tasks are ignored.

### 4.3 `graph-soft-tests`

- Output: `tests/test_graph_soft_table.py`. Import `from app.core import graph as g`.
- At least **20 cases** on `g.GRAPH` with `soft=g.SOFT`: `next_ready` returns `qa` when every BUSINESS
  task is finished even if `kpi` FAILED and `finance` SKIPPED; `qa` is not ready while any BUSINESS task
  is PENDING or RUNNING; `summary` waits for `qa`, `audit`, `monitor` to finish; `to_skip` never returns
  a soft task for FAILED/SKIPPED deps but does for a CANCELLED dep; without `soft` the old strict
  behaviour holds (one regression case each); `can_rerun` true only for soft COMPLETED→PENDING;
  `retry_plan(..., soft=g.SOFT)` re-arms SKIPPED descendants and COMPLETED/FAILED soft descendants but
  never COMPLETED business tasks.

## 5. Report back

Job id, output path, checker last line, case count, anything not done, "SUSPECTED BUGS" (or "none").

## 6. Acceptance (Claude)

Runner clean; Claude reruns checker + full pytest; re-derives a sample; investigates every suspected bug;
one row in `ai-jobs/LEDGER.md`.

## 7. Result

2026-11-05: 3/3 jobs exit 0, 235 s, no stray write, no suspected bugs. Checker OK x3; full suite 424 passed.
Claude spot-checked case names: every rule covered, incl. +/-0.01 tolerance and comma decimals.
