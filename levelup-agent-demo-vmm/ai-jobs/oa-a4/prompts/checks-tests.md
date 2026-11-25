# Work order oa-a4 / checks-tests (Gemini, headless)

> Written 2026-11-25 by Claude (brain). Owner ruling: Claude 60 / Gemini 40. Acceptance by Claude only.

Read `app/agents/checks.py` completely (docstrings are the spec) and `app/mock/fixtures.json` only for the shape
of `suppliers.items` (sku, supplier, unit_cost_php, lead_time_days). Build facts dicts by hand (only the
`suppliers` key is needed), e.g. LU-PH-001 cost 9999 in facts and 180 in ref_facts.

Write exactly one file: `tests/test_checks_table.py` with `from app.agents import checks`. At least **15 cases**:
- `FIX` and `CHECKS` contents (exact literal dicts); `level()` for both checks and an unknown name.
- `apply_facts`: 9999 -> 180 with applied == [{'check', 'field': 'suppliers[LU-PH-001].unit_cost_php', 'before': 9999,
  'after': 180, 'source': 'fixture'}]; already equal -> no change, applied []; unknown sku -> nothing; artifact-level
  check ignored; two checks for two skus; the input facts dict is NOT mutated (compare with a deepcopy taken before).
- `apply_artifact`: drop meta_ads.publish keeps meta_ads.create_draft, before/after tool lists exact; tool not present
  -> applied []; facts-level check ignored; no requested_actions key -> unchanged; input not mutated.

## Hard rules

Expected values are literals you derive by hand from the docstrings. Never call a function under test to produce
an expectation. If code disagrees with the docstring, keep the docstring expectation, let the test fail, and
report it under "SUSPECTED BUGS". Do not edit code.
You MUST run `python -I ai-jobs/oa-a4/checker.py <your-job-id> .` until it exits 0 (max three rounds).
You MUST NOT: edit any other file; use git, pip, docker or network yourself; import anything except `pytest`,
`copy`, `json`, `itertools`, `pathlib`, `os`, `math` and the module under test; invent products or tools
(SKUs are LU-PH-001, LU-PH-002, LU-PH-003; tools `meta_ads.create_draft`, `meta_ads.publish`, `crm.reply_draft`).
Style: `@pytest.mark.parametrize` tables with `ids=`, helper builders with `copy.deepcopy`. Read `tests/test_graph_table.py` for house style.
