# 02 — Work order: Phase 4 agents batch (Gemini, headless `agy -p`)

> Written 2026-11-05 by Claude (brain). Owner ruling: Claude 60 / Gemini 40 (2026-11-05).
> Executor: one headless `agy -p` run per job (`gemini-4-argon-high`, mode `write`).
> Acceptance: Claude, never the executor's own report (section 6).

## 1. What you are producing

A local demo where 13 simulated AI agents of a sales team cooperate on a **synthetic** Philippines
scenario. Claude wrote the agents: each one computes an "artifact" (a JSON dict of numbers) in Python.
You produce three independent pieces:

- `mock-texts`: Vietnamese narrative templates shown on the dashboard when no LLM is used.
- `compute-tests`: table-driven pytest for the business agents' pure functions.
- `supervisor-tests`: table-driven pytest for the supervisory agents and the permission registry.

Read before working, in this order (only these):
1. `app/agents/business.py`, `app/agents/supervisors.py`, `app/core/registry.py`, `app/core/artifacts.py`,
   `app/agents/narrate.py` (function `flat` and `mock_narrative`).
2. `app/mock/fixtures.json`: the only data.
3. `ai-jobs/p4-agents/sample_flat.json`: real flattened artifacts from one run (placeholder names + values).
4. `tests/test_graph_table.py`: test style to match.
5. Your brief in section 4.

## 2. Hard rules

You MUST:
- Write exactly the one file named in your brief, and nothing else.
- Compute every expected number **by hand from `app/mock/fixtures.json` and the formulas in the
  docstrings**, and write it as a literal in the test (e.g. `226`, `0.1333`). Do not call the function
  under test to produce an expected value. If your hand result differs from the code, keep your hand
  value, let the test fail, and report it under "SUSPECTED BUGS" — do not edit the code.
- Run `python -I ai-jobs/p4-agents/checker.py <your-job-id> .` and fix your output until it exits 0
  (at most three rounds). If a failure is a suspected code bug, stop and report it instead.

You MUST NOT:
- Edit, create or delete any other file. No git, no pip, no docker, no network.
- Import anything except `pytest`, `copy`, `json`, `pathlib`, `math` and the modules under test.
- Invent numbers, products, brands, people or URLs.

## 3. Style

Python: `@pytest.mark.parametrize` tables with `ids=`, small helper to load fixtures with
`copy.deepcopy`, one idea per test function. JSON: UTF-8, 2-space indent.

## 4. Briefs

### 4.1 `mock-texts`

- Output: `app/llm/mock_texts.json` — an object with exactly these 14 keys:
  `plan, market, product, offer, content, campaign, leads, care, kpi, finance, qa, audit, monitor, summary`.
- Each value: one Vietnamese template string, 1–3 sentences, 60–400 characters, natural business tone,
  in the voice of that agent reporting to the Commander (e.g. "Market Intelligence: ...").
- Placeholders use Python `str.format` syntax `{name}` and **must be keys that exist for that task in
  `sample_flat.json`**. Use at least 3 placeholders per template, and always the task's most important
  numbers (offer: price, margin, break-even; kpi: roas and CPAs; finance: contribution after ads and
  risk level; qa/audit/monitor: status and findings count).
- **No digits at all** in the template text: every number comes from a placeholder.
- Mention that data is synthetic ("giả lập") in `plan` and `market`; mention DRAFT in `content` and
  `campaign`; never claim real sales, real customers, publishing, payment or messages sent.
- No format specs (`{x:.2f}`), no attribute/index access (`{a.b}`, `{a[0]}`).

### 4.2 `compute-tests`

- Output: `tests/test_agents_table.py`. Import `from app.agents import business as b`.
- Build `facts` from `app/mock/fixtures.json` (deep copy per test); build `inputs` for each function by
  hand-writing the minimal upstream dicts it reads (read the function body to see which keys).
- At least **40 cases** covering: `market` (rates), `product` (margin and margin_pct for all 3 SKUs,
  selected SKU, warning present only when the selected SKU is below 30%; a facts variant where no SKU
  has a campaign → highest passing margin wins), `offer` (margin 226, break-even 18, budget 4000, and a
  variant with unit cost 9999 → break-even 0), `content` (angles come only from lead-stage
  conversations, 3 drafts, status DRAFT), `campaign` (status DRAFT, budget share, exactly one requested
  action `meta_ads.create_draft`), `leads` (cost per lead, per confirmed, open conversations = lead
  stage ids), `care` (in_transit, ticket ids = complaint/return_request conversations), `kpi` (gross,
  net, roas, cpa values), `finance` (contribution before/after ads, risks list contents, risk level
  LOW / MEDIUM / HIGH with three crafted input variants).

### 4.3 `supervisor-tests`

- Output: `tests/test_supervisors_table.py`. Import `from app.agents import supervisors as s` and
  `from app.core import registry as r`.
- At least **30 cases** covering: `r.required_permission` and `r.allowed` for every tool in
  `r.TOOL_PERMISSION`, a `mock.*` tool, an unknown tool, for agents `02`, `06`, `07`, `11` (e.g. `06`
  may `meta_ads.create_draft` but never `meta_ads.publish`; `02` may not `crm.reply_draft`);
  `s.qa` (all valid → PASS; a missing artifact → FAIL with rule `schema`; a wrong-typed field → FAIL);
  `s.audit` (allowed draft actions → PASS; `meta_ads.publish` requested by agent `06` → FAIL with rule
  `permission`; campaign status not DRAFT → FAIL with rule `draft_only`); `s.monitor` (all completed
  → PASS; a retried task → WARN; a FAILED business task → FAIL; llm errors → WARN).
- Build valid artifacts for `s.qa` by hand (satisfying `app/core/artifacts.py` SPEC), not by calling
  the business functions.

## 5. Report back

Job id, output path, checker last line, case count, anything not done, and "SUSPECTED BUGS" (or "none").

## 6. Acceptance (Claude)

1. Runner: no error, no timeout, no stray write. 2. Claude reruns checker + full pytest in container.
3. Claude re-derives a sample of expected numbers; every SUSPECTED BUG is investigated.
4. Claude reads all 14 templates rendered against a real run. 5. One row in `ai-jobs/LEDGER.md`.

## 7. Result

2026-11-05: 3/3 jobs exit 0, 280 s, no stray write, no suspected bugs. Checker OK x3; full suite 281 passed.
Claude edit: `summary` template wording ("lãi" with a negative number -> "lợi nhuận"). Expected values are
hand literals; Claude re-derived finance (2938 / -1062 / HIGH-MEDIUM-LOW variants) and they match.
