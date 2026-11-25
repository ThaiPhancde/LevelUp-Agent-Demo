# Work order oa-a3: table tests for the gateway's attempt filter and reuse rule (Gemini, headless)

> Written 2026-11-25 by Claude (brain). Owner ruling: Claude 60 / Gemini 40.
> Acceptance is done by Claude, never by the executor's own report.

## What exists

A local demo where 13 simulated agents act only through a "Mock Tool Gateway" (`app/core/gateway.py`).
Phase A3 added three PURE functions there. Read `app/core/gateway.py` completely: the docstrings are the spec.
Also read `tests/test_graph_table.py` for the house style. Read nothing else.

- `action_hash(action) -> str`: sha256 hex (64 lowercase hex chars) of the canonical JSON of the whole action.
- `reusable(prior, target, a_hash, decision) -> dict | None`: newest earlier detail that is not BLOCK, same
  target, same action_hash, same decision as the new verdict; otherwise None.
- `current_attempt(rows, attempts) -> list`: keep rows whose `detail['attempt']` (missing = 1) equals
  `attempts[task_key]` (missing task = 1); order preserved.

## Output

Write exactly one file: `tests/test_gateway_attempt_table.py`, importing `from app.core import gateway`.
Do NOT call `gateway.execute` (it writes to a database). Only the three pure functions.

At least **30 cases** in `@pytest.mark.parametrize` tables with `ids=`:
- `action_hash`: key order does not change the hash; nested dict key order does not change it; a different
  `budget_php`, `target` or `tool` changes it; Vietnamese text (UTF-8) is stable; result is 64 hex chars.
  You may only compare hashes with each other (equal / not equal) and check the format; never hard-code a digest.
- `reusable`: empty prior -> None; exact match -> that detail; BLOCK with everything matching -> None;
  decision differs (old ALLOW, new NEEDS_APPROVAL and vice versa) -> None; target differs -> None;
  hash differs -> None; detail without action_hash (a pre-A3 row) -> None; two matches -> the newer (last) one;
  a match followed by a non-matching row -> still the match; a reused row (has `reused: True`) also counts.
- `current_attempt`: all rows attempt 1 with tasks at 1 -> all kept; task retried (attempt 2) keeps only its
  attempt-2 rows and other tasks are unaffected; row without `attempt` counts as 1; row with `detail` None or
  missing counts as 1; task missing from `attempts` counts as 1; a BLOCK row of attempt 1 disappears when the
  task is at attempt 2; order preserved; empty input -> [].

Expected values are literals you derive by hand from the docstrings. Never call a function under test to
produce an expectation. If code disagrees with the docstring, keep the docstring expectation, let the test
fail, and report it under "SUSPECTED BUGS". Do not edit code.

## Hard rules

You MUST run `python -I ai-jobs/oa-a3/checker.py attempt-tests .` until it exits 0 (max three rounds).
You MUST NOT: edit any other file; use git, pip, docker or network yourself; import anything except `pytest`,
`copy`, `json`, `itertools`, `pathlib`, `os`, `math` and `app.core.gateway`; invent data unrelated to the demo
(use tools like `meta_ads.create_draft`, `meta_ads.publish`, targets like `CMP-LU-PH-001`).
