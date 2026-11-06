# 01 — Work order: Phase 3 support batch (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner ruling: split work Claude 60 / Gemini 40 (2026-11-05).
> Executor: one headless `agy -p` run per job through `tools/agy-runner/run_agy.py`
> (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude, never the executor's own report (section 6).

## 1. What you are producing

A local demo where 13 simulated AI agents of a sales team cooperate on a **synthetic** Philippines
e-commerce scenario. Nothing is real: no live ads, no real customers, no payments. Claude owns the
engine. You produce three independent pieces:

- `graph-tests`: a table-driven pytest file for the pure functions in `app/core/graph.py`.
- `data-tests`: a table-driven pytest file for the pure functions in `app/mock/data.py`.
- `conversations`: a JSON file of synthetic customer chat transcripts used later by the
  "Lead & Sales" and "Customer Success" agents.

Read before working, in this order (only these):
1. `app/core/graph.py` (graph-tests) or `app/mock/data.py` + `app/mock/fixtures.json` (data-tests,
   conversations). These are the only facts you may use.
2. `tests/conftest.py` and `tests/test_llm.py`: test style to match.
3. Your brief in section 4.

## 2. Hard rules

You MUST:
- Write exactly the one file named in your brief, and nothing else.
- Derive every expected value by reading the code/fixture, not by guessing. If the code looks wrong
  to you, still write the test for what the docstring says, and list the suspected bug in your final
  reply under "SUSPECTED BUGS". Do not edit the code.
- Run `python -I ai-jobs/p3-workflow/checker.py <your-job-id> .` and fix your output until it exits 0
  (at most three rounds).

You MUST NOT:
- Edit, create or delete any other file. No git, no pip, no docker, no network fetches.
- Import anything other than `pytest`, the standard library, and the module under test.
- Invent numbers, prices, SKUs or brands that are not in `app/mock/fixtures.json`.
- Mention real companies, real people, real phone numbers, real URLs or real payment details.

## 3. Style

Python: plain functions, `@pytest.mark.parametrize` tables with an `ids=` list of short readable
case names, one assertion idea per test function. No classes, no fixtures beyond what conftest gives.
JSON: UTF-8, 2-space indent, no comments.

## 4. Briefs

### 4.1 `graph-tests`

- Output: `tests/test_graph_table.py`
- Module under test: `app.core.graph` (import as `from app.core import graph as g`).
- Cover, with at least **45 parametrized cases in total**:
  - `can_transition`: every pair in `TASK_STATES x TASK_STATES` (36 cases) generated from an explicit
    expected table you write out (do not compute the expectation from `TRANSITIONS`), plus 2 unknown
    state cases.
  - `topo_order`: the real `g.GRAPH` (assert `plan` first, `summary` last, every task after all its
    dependencies), a small diamond graph, declaration-order tie break, unknown dependency raises
    `ValueError`, a 2-node cycle raises `ValueError`, a self-loop raises `ValueError`.
  - `descendants`: on `g.GRAPH` for `plan` (all 13 others), `campaign`, `finance`, `summary` (empty).
  - `next_ready`: fresh run (all PENDING) returns `plan`; after `plan` COMPLETED returns `market`;
    `campaign` waits until both `offer` and `content` are COMPLETED; nothing ready returns None.
  - `to_skip`: `market` FAILED with all later tasks PENDING returns only `product` (one pass);
    a CANCELLED dependency also blocks; COMPLETED dependencies do not.
  - `run_status`: empty, all COMPLETED, mixed with RUNNING, CANCELLED wins over FAILED, FAILED +
    PENDING leftovers, PENDING + COMPLETED with nothing failed.
  - `retry_plan`: retrying FAILED `market` with downstream SKIPPED re-arms exactly those SKIPPED
    descendants; COMPLETED descendants are untouched; retrying a non-FAILED task raises `ValueError`.

### 4.2 `data-tests`

- Output: `tests/test_mock_data.py`
- Module under test: `app.mock.data` (import as `from app.mock import data`).
- Cover, with at least **15 parametrized cases in total**:
  - `fixture(domain)` returns a deep copy (mutating the result does not change the next call), for
    every domain in `data.DOMAINS`.
  - `facts_for([])` equals the fixtures; `facts_for(['bad_cost'])` sets only LU-PH-001
    `unit_cost_php` to `data.BAD_COST_PHP`, leaves LU-PH-002 / LU-PH-003 suppliers unchanged, and
    does not leak into a later `facts_for([])` call. Unknown injection names change nothing.
  - `sample()` returns exactly the numbers in the fixtures: price 499, cost 180, shipping 75,
    payment fee 18, budget 15000, stock 50, leads 100, confirmed 20, delivered 15, returned 2,
    campaign status DRAFT, spend 4000. Read each from the fixture file in the test, then compare.
  - `sample(facts_for(['bad_cost']))` reports cost 9999.

### 4.3 `conversations`

- Output: `app/mock/conversations.json`
- Shape: `{"synthetic": true, "items": [ ... ]}` with **exactly 12** items. Each item:
  - `conversation_id`: `CONV-001` … `CONV-012`, in order, unique.
  - `channel`: one of `messenger_mock`, `tiktok_mock`, `website_chat_mock`.
  - `language`: one of `en`, `fil`, `taglish` — at least 3 of each.
  - `sku`: one of `LU-PH-001`, `LU-PH-002`, `LU-PH-003` — each used at least 3 times.
  - `stage`: one of `lead`, `confirmed`, `delivered`, `returned` — each at least 2 times.
  - `intent`: one of `product_question`, `price_question`, `shipping_question`, `order_status`,
    `complaint`, `return_request` — each at least once.
  - `messages`: 2 to 6 objects `{"from": "customer" | "agent_draft", "text": "..."}`, first one
    from `customer`. Text 5–280 characters. Written in the item's language.
  - `synthetic`: `true`.
- Numbers in any text may only be: the item's own price (499 for LU-PH-001, 699 for LU-PH-002,
  299 for LU-PH-003, optionally with "PHP" or "₱"), shipping fee 75, delivery days 3, or the
  conversation's own order reference written as `ORD-<conversation number>` (e.g. `ORD-007`).
  No other digits anywhere in text. Customer names: first name only, clearly fictional.
- `agent_draft` messages are drafts that a human would review: never promise refunds, discounts,
  or delivery dates beyond "3 days"; never ask for card numbers, passwords or one-time codes.

## 5. Report back (your final reply)

Job id, output path, the checker's last output line, case count, anything you could not do, and
"SUSPECTED BUGS" (or "none").

## 6. Acceptance (Claude, not the executor)

1. `run_agy.py` reports no error, no timeout, no stray write.
2. Claude reruns the checker and `pytest` on the file inside the demo container.
3. Claude re-derives a sample of expected values by hand; every SUSPECTED BUG is investigated.
4. Conversations: Claude reads all 12 for tone, safety and number rules.
5. One row in `ai-jobs/LEDGER.md`.

## 7. Result

2026-11-05: 3/3 jobs exit 0, 374 s, no stray write. Checker OK for all three; full suite 133 passed.
Brief defect (Claude): 4.1 said `to_skip` with `market` FAILED "returns only product"; on the real graph
qa/audit/monitor also depend directly on market. Gemini tested the real behaviour and flagged it. Code unchanged.
Conversations merged into `app/mock/fixtures.json` -> `conversations` (single source).
