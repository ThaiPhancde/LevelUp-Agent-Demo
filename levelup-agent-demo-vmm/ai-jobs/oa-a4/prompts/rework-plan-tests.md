# Work order oa-a4 / rework-plan-tests (Gemini, headless)

> Written 2026-11-25 by Claude (brain). Owner ruling: Claude 60 / Gemini 40. Acceptance by Claude only.

Read `app/core/graph.py` completely: `TASKS`, `GRAPH`, `SOFT`, `BUSINESS`, `descendants`, `topo_order`, and the
A4 section at the end: `can_rework`, `rework_plan`, `MAX_REWORK_CEILING`, plus `dispatch_reason(..., rework=...)`.
Docstrings are the spec. Nothing else needs reading besides the house-style file below.

Write exactly one file: `tests/test_rework_plan_table.py`, using `from app.core import graph as g` and the real
`g.GRAPH`, `g.SOFT`. Use `fixable = {'reference': 'verify_supplier_cost', 'blocked_action': 'drop_blocked_action'}`
(a literal; do not import it). At least **30 cases**:

- `can_rework`: COMPLETED->PENDING allowed for each kind of task in BUSINESS; refused for soft tasks (qa, audit,
  monitor, summary) and plan; refused for every other (src, dst) pair you choose (FAILED->PENDING, COMPLETED->RUNNING, ...).
- `rework_plan` None reasons, and the ORDER of checks: a FAILED or SKIPPED business task wins over everything
  (even when there are fixable FAILs and rounds left); no FAIL (only WARN, or empty) -> 'no_fail'; only unfixable FAIL
  rules (schema, arithmetic, not_via_gateway...) -> 'no_fixable_rule'; a fixable rule on a non-business task_key
  -> 'no_fixable_rule'; rounds_used == max_rework and rounds_used > max_rework -> 'exhausted'; max_rework 0 -> 'exhausted'.
- `rework_plan` plans: reference FAIL on product and offer -> target 'product', checks
  ['verify_supplier_cost:LU-PH-001'] (deduplicated), changes = product and every COMPLETED descendant incl. qa and audit,
  but NOT monitor/summary when they are PENDING; blocked_action on campaign -> target 'campaign', check
  'drop_blocked_action:meta_ads.publish', changes = campaign, leads, care, kpi, finance, qa, audit; both at once -> target
  product (earliest), both checks sorted; feedback holds only the target's findings while findings holds all fixable
  ones; every value of changes is ('COMPLETED', 'PENDING'); a WARN with a fixable rule is ignored; the plan's second
  tuple element is 'planned'; a retry and a rework in the same run (some task attempt>1 does not matter: statuses only).
- `dispatch_reason` with `rework='reference tại product'` returns a text containing that string and the attempt number.

Realistic finding details: reference -> 'LU-PH-001 unit_cost_php 9999 != reference 180';
blocked_action -> 'meta_ads.publish by agent 06 was blocked'. Statuses: all 14 tasks, business+qa+audit COMPLETED,
monitor+summary PENDING (the decision point), unless a case says otherwise.

## Hard rules

Expected values are literals you derive by hand from the docstrings. Never call a function under test to produce
an expectation. If code disagrees with the docstring, keep the docstring expectation, let the test fail, and
report it under "SUSPECTED BUGS". Do not edit code.
You MUST run `python -I ai-jobs/oa-a4/checker.py <your-job-id> .` until it exits 0 (max three rounds).
You MUST NOT: edit any other file; use git, pip, docker or network yourself; import anything except `pytest`,
`copy`, `json`, `itertools`, `pathlib`, `os`, `math` and the module under test; invent products or tools
(SKUs are LU-PH-001, LU-PH-002, LU-PH-003; tools `meta_ads.create_draft`, `meta_ads.publish`, `crm.reply_draft`).
Style: `@pytest.mark.parametrize` tables with `ids=`, helper builders with `copy.deepcopy`. Read `tests/test_graph_table.py` for house style.
