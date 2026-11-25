"""Pure task-graph and state-machine rules for the Commander workflow. No I/O; table-tested.

Statuses follow DEMO_ONLY P3. Graph follows DEMO_PLAN.md section 4.2.
"""

PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED = 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED', 'CANCELLED'
TASK_STATES = (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED)
RUN_STATES = ('PENDING', 'RUNNING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED', 'CANCELLED')
TERMINAL = frozenset({COMPLETED, CANCELLED})
BLOCKING = frozenset({FAILED, SKIPPED, CANCELLED})  # a dependency in one of these can never complete on its own

# Allowed task transitions. FAILED -> PENDING is a retry; SKIPPED -> PENDING re-arms a task whose
# upstream is being retried. COMPLETED and CANCELLED are final.
TRANSITIONS = {
    PENDING: frozenset({RUNNING, SKIPPED, CANCELLED}),
    RUNNING: frozenset({COMPLETED, FAILED, CANCELLED}),
    FAILED: frozenset({PENDING}),
    SKIPPED: frozenset({PENDING, CANCELLED}),
    COMPLETED: frozenset(),
    CANCELLED: frozenset(),
}

# Soft tasks run once every dependency has *finished* (COMPLETED, FAILED or SKIPPED), so supervisors still
# report when a business agent fails (DEMO_ONLY P5: Monitor must see the timeout). Default arguments keep
# the strict behaviour; the workflow passes soft=SOFT.
FINISHED = frozenset({COMPLETED, FAILED, SKIPPED})

BUSINESS = ('market', 'product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance')

# task_key -> (agent_id, required dependencies). Declaration order is the tie-break order.
TASKS = {
    'plan': ('01', ()),
    'market': ('02', ('plan',)),
    'product': ('03', ('market',)),
    'offer': ('04', ('product',)),
    'content': ('05', ('offer',)),
    'campaign': ('06', ('offer', 'content')),
    'leads': ('07', ('campaign',)),
    'care': ('08', ('leads',)),
    'kpi': ('09', ('leads', 'care')),
    'finance': ('10', ('offer', 'kpi')),
    'qa': ('11', BUSINESS),
    'audit': ('12', BUSINESS),
    'monitor': ('13', BUSINESS + ('qa', 'audit')),
    'summary': ('01', ('qa', 'audit', 'monitor')),
}
GRAPH = {key: list(deps) for key, (_, deps) in TASKS.items()}
SOFT = frozenset({'qa', 'audit', 'monitor', 'summary'})


def can_transition(src: str, dst: str) -> bool:
    """True when a task may move from src to dst. Unknown states are never allowed."""
    return dst in TRANSITIONS.get(src, ())


def topo_order(graph: dict) -> list:
    """Dependency-first order, stable by declaration order. ValueError on a cycle or an unknown dependency."""
    for key, deps in graph.items():
        for d in deps:
            if d not in graph:
                raise ValueError(f'unknown dependency {d!r} of {key!r}')
    order, done = [], set()
    while len(order) < len(graph):
        progressed = False
        for key, deps in graph.items():
            if key not in done and all(d in done for d in deps):
                order.append(key)
                done.add(key)
                progressed = True
        if not progressed:
            raise ValueError('cycle in task graph: ' + ', '.join(k for k in graph if k not in done))
    return order


def descendants(task: str, graph: dict) -> set:
    """Every task that depends on `task`, directly or transitively. Excludes `task` itself."""
    out, frontier = set(), {task}
    while frontier:
        nxt = {k for k, deps in graph.items() if frontier & set(deps)} - out
        out |= nxt
        frontier = nxt
    return out


def to_skip(statuses: dict, graph: dict, soft=()) -> list:
    """PENDING tasks that can never run because a dependency is FAILED, SKIPPED or CANCELLED.
    Soft tasks are only skipped by a CANCELLED dependency. One pass only (caller repeats until empty)."""
    return [k for k in topo_order(graph)
            if statuses.get(k) == PENDING and any(
                statuses.get(d) == CANCELLED if k in soft else statuses.get(d) in BLOCKING for d in graph[k])]


def next_ready(statuses: dict, graph: dict, soft=()):
    """First PENDING task (topo order) whose dependencies are all COMPLETED (soft task: all FINISHED), or None."""
    for k in topo_order(graph):
        ok = FINISHED if k in soft else {COMPLETED}
        if statuses.get(k) == PENDING and all(statuses.get(d) in ok for d in graph[k]):
            return k
    return None


def dispatch_reason(key: str, graph: dict, soft=(), attempt: int = 1, rework: str | None = None) -> str:
    """Human-readable reason a task is dispatched now (A1 decision log). Pure; attempt>1 is a retry,
    unless `rework` (A4: the rules the Commander sent back, e.g. 'reference') says it is a rework."""
    if rework:
        return f'Làm lại theo yêu cầu của Commander (lần thử #{attempt}): {rework}.'
    if attempt > 1:
        return f'Làm lại lần thử #{attempt} sau khi được retry.'
    deps = graph[key]
    if not deps:
        return 'Không phụ thuộc task nào, sẵn sàng chạy ngay.'
    listed = ', '.join(deps)
    if key in soft:
        return f'Task giám sát: mọi phụ thuộc đã kết thúc (hoàn tất/lỗi/bỏ qua): {listed}.'
    return f'Mọi phụ thuộc đã hoàn tất: {listed}.'


def run_status(statuses: dict) -> str:
    """Overall run status from task statuses (WAITING_APPROVAL is set by the approval flow, not here).
    Empty -> PENDING. Any RUNNING -> RUNNING. Any CANCELLED -> CANCELLED. All COMPLETED -> COMPLETED.
    Any PENDING left with nothing failed -> PENDING. Otherwise (something FAILED/SKIPPED) -> FAILED."""
    values = list(statuses.values())
    if not values:
        return 'PENDING'
    if RUNNING in values:
        return 'RUNNING'
    if CANCELLED in values:
        return 'CANCELLED'
    if all(v == COMPLETED for v in values):
        return 'COMPLETED'
    if PENDING in values and not any(v in (FAILED, SKIPPED) for v in values):
        return 'PENDING'
    return 'FAILED'


def can_rerun(task: str, src: str, dst: str, soft=()) -> bool:
    """The one exception to TRANSITIONS: a COMPLETED soft task is re-armed when an upstream task is retried,
    because its report described the failed state. Business results are never re-armed."""
    return task in soft and src == COMPLETED and dst == PENDING


def retry_plan(task: str, statuses: dict, graph: dict, soft=()) -> dict:
    """Status changes for retrying `task`: it goes FAILED -> PENDING, every SKIPPED descendant -> PENDING,
    and (soft) every COMPLETED or FAILED soft descendant -> PENDING so supervisors report again.
    ValueError if `task` is not FAILED. COMPLETED non-soft descendants keep their results."""
    if statuses.get(task) != FAILED:
        raise ValueError(f'only a FAILED task can be retried, {task!r} is {statuses.get(task)}')
    changes = {task: PENDING}
    for d in descendants(task, graph):
        st = statuses.get(d)
        if st == SKIPPED or (d in soft and st in (COMPLETED, FAILED)):
            changes[d] = PENDING
    return changes


# ---- A4: rework loop (DEMO_PLAN_OPTION_A 7.2) -------------------------------------------------------

MAX_REWORK_CEILING = 2


def can_rework(task: str, src: str, dst: str) -> bool:
    """The rework exception to TRANSITIONS: a COMPLETED business task is sent back to PENDING by the
    Commander. Only COMPLETED -> PENDING, only BUSINESS tasks (soft tasks use can_rerun)."""
    return task in BUSINESS and src == COMPLETED and dst == PENDING


def rework_plan(findings: list, statuses: dict, rounds_used: int, graph: dict, soft=(), max_rework: int = 0,
                fixable: dict | None = None):
    """Pure. Decide whether the Commander sends work back before the Monitor runs.

    findings: QA + Audit findings ({'rule', 'severity', 'task_key', 'detail', ...}).
    fixable:  rule -> check name (app.agents.checks.FIX). A check is '<name>:<arg>' where arg is the first word
              of the finding's detail (the SKU for `reference`, the tool for `blocked_action`).
    Returns (plan, reason). plan is None, in this order of checks, with reason:
      'business_task_not_completed'  a BUSINESS task is FAILED or SKIPPED (nothing to compare against)
      'no_fail'                      no FAIL finding at all
      'no_fixable_rule'              no FAIL finding on a BUSINESS task has a rule in `fixable`
      'exhausted'                    rounds_used >= max_rework
    Otherwise plan = {'target', 'findings', 'feedback', 'checks', 'changes', 'reason'}:
      target    the earliest BUSINESS task (topo order) carrying a fixable FAIL
      findings  every fixable FAIL finding (all tasks); feedback = those of the target
      checks    sorted unique checks for `findings`
      changes   {task: (COMPLETED, PENDING)} for the target, its COMPLETED descendants (business and soft)
    """
    fixable = fixable or {}
    if any(statuses.get(t) in (FAILED, SKIPPED) for t in BUSINESS):
        return None, 'business_task_not_completed'
    fails = [f for f in findings if f.get('severity') == 'FAIL']
    if not fails:
        return None, 'no_fail'
    fix = [f for f in fails if f.get('rule') in fixable and f.get('task_key') in BUSINESS]
    if not fix:
        return None, 'no_fixable_rule'
    if rounds_used >= max_rework:
        return None, 'exhausted'
    order = topo_order(graph)
    target = min({f['task_key'] for f in fix}, key=order.index)
    # ponytail: the check argument is parsed from the finding text ("LU-PH-001 unit_cost_php ...",
    # "meta_ads.publish by agent 06 ..."); give findings a structured `ref` field if more rules become fixable.
    checks = sorted({f"{fixable[f['rule']]}:{str(f.get('detail', '')).split(' ', 1)[0]}" for f in fix})
    changes = {t: (COMPLETED, PENDING) for t in [target, *sorted(descendants(target, graph), key=order.index)]
               if statuses.get(t) == COMPLETED}
    rules = sorted({f['rule'] for f in fix if f['task_key'] == target})
    return ({'target': target, 'findings': fix, 'feedback': [f for f in fix if f['task_key'] == target],
             'checks': checks, 'changes': changes, 'reason': f'{", ".join(rules)} tại {target}'}, 'planned')
