"""Commander + Workflow Engine: run/task persistence, dependency-ordered execution, retry, cancel,
replay and restart recovery. Rules live in app.core.graph (pure); this module does the I/O.

Tasks run one at a time in topo order (DEMO_DECISIONS M-12), so SQLite never sees concurrent writers
from one run. Agent logic plugs in through HANDLERS (Phase 4); until then `placeholder` runs.
"""
import asyncio
import hashlib
import inspect
import json
import os
import time
import uuid
from dataclasses import dataclass

from app import db
from app.core import artifacts as schemas
from app.agents import checks as fixes
from app.core import graph as g
from app.mock import data

HANDLERS: dict = {}  # per-task overrides (tests, error injection); callable(Ctx) -> dict payload, sync or async
DEFAULT_HANDLER = None  # None -> app.agents.handle (the 13 real agents). Tests may set wf.placeholder.
_background: set = set()
ACTIVE_RUN_STATES = ('PENDING', 'RUNNING', 'WAITING_APPROVAL')


class WorkflowError(Exception):
    """Bad request against the current run state. `status` is the HTTP code the API should use."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


@dataclass
class Ctx:
    run_id: str
    task_key: str
    agent_id: str
    objective: str
    mode: str
    inject: list
    attempt: int
    facts: dict   # run-scoped mock data, injections applied
    inputs: dict  # dep task_key -> upstream artifact payload
    feedback: tuple = ()  # A4: findings the Commander sent back to this task (display + artifact only)
    memory: tuple = ()    # A6
    rework: bool = False  # A4: dispatched by the rework loop -> narrative is always mock
    checks: tuple = ()    # A4: artifact-level checks for this task (checks.apply_artifact)
    applied: tuple = ()   # A4: facts-level checks already applied to `facts` (recorded as check_applied)


def task_timeout(mode: str = 'mock') -> float:
    """Mock agents finish in milliseconds; LLM agents may retry DeepSeek (60 s timeout x 3)."""
    if mode == 'llm':
        return float(os.getenv('LLM_TASK_TIMEOUT_S', '200'))
    return float(os.getenv('TASK_TIMEOUT_S', '5'))


def step_delay(mode: str) -> float:
    """Mock agents finish in milliseconds; pause each RUNNING task so a person watching the dashboard can follow
    the hand-offs. Presentation only: tests and scripts set MOCK_STEP_DELAY_S=0. LLM mode is already slow."""
    return float(os.getenv('MOCK_STEP_DELAY_S', '0.8')) if mode == 'mock' else 0.0


def stop_poll() -> float:
    """How often a run paused by the emergency stop re-checks it (seconds)."""
    return float(os.getenv('STOP_POLL_S', '0.5'))


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _decision(c, run_id, action, task_key=None, agent_id=None, **kw):
    c.execute('INSERT INTO decision_log(run_id,task_key,agent_id,action,tool,permission,allowed,input_hash,output_ref,'
              'duration_ms,tokens,detail,ts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (run_id, task_key, agent_id, action, kw.get('tool'), kw.get('permission'), int(kw.get('allowed', True)),
               kw.get('input_hash'), kw.get('output_ref'), kw.get('duration_ms'), kw.get('tokens'),
               json.dumps(kw.get('detail') or {}, ensure_ascii=False), db.now()))


def _statuses(c, run_id) -> dict:
    return {r['task_key']: r['status'] for r in c.execute('SELECT task_key,status FROM tasks WHERE run_id=?', (run_id,))}


def _move(c, run_id, key, src, dst, rework=False, **fields) -> bool:
    """Conditional task transition; False when another writer moved it first. Only the rework loop passes
    rework=True, which also allows a COMPLETED business task back to PENDING (g.can_rework)."""
    if not (g.can_transition(src, dst) or g.can_rerun(key, src, dst, g.SOFT)
            or (rework and g.can_rework(key, src, dst))):
        raise WorkflowError(409, f'task {key}: {src} -> {dst} not allowed')
    sets = ', '.join(['status=?'] + [f'{k}=?' for k in fields])
    cur = c.execute(f'UPDATE tasks SET {sets} WHERE run_id=? AND task_key=? AND status=?',
                    (dst, *fields.values(), run_id, key, src))
    return cur.rowcount == 1


def placeholder(ctx: Ctx) -> dict:
    """Phase 3 stand-in agent: proves hand-off by reading every upstream artifact it depends on."""
    depth = 1 + max((p.get('chain_depth', 0) for p in ctx.inputs.values()), default=0)
    return {'type': f'{ctx.task_key}_placeholder', 'agent_id': ctx.agent_id, 'chain_depth': depth,
            'received_from': {k: p.get('type') for k, p in ctx.inputs.items()},
            'summary': f'{ctx.task_key}: placeholder output built from {len(ctx.inputs)} upstream artifact(s).'}


# ---- run lifecycle --------------------------------------------------------------------------------

def create_run(objective: str, mode: str = 'mock', inject=(), max_rework: int = 0) -> str:
    run_id = str(uuid.uuid4())
    sources = data.input_sources_for(objective)
    with db.tx() as c:
        c.execute('INSERT INTO runs(run_id,objective,mode,status,inject,created_at,max_rework) VALUES (?,?,?,?,?,?,?)',
                  (run_id, objective, mode, 'PENDING', json.dumps(list(inject)), db.now(), max_rework))
        for key, (agent_id, deps) in g.TASKS.items():
            c.execute('INSERT INTO tasks(run_id,task_key,agent_id,status,depends_on) VALUES (?,?,?,?,?)',
                      (run_id, key, agent_id, g.PENDING, json.dumps(list(deps))))
        _decision(c, run_id, 'plan_tasks', 'plan', '01',
                  detail={'objective': objective, 'mode': mode, 'inject': list(inject), 'max_rework': max_rework,
                          'graph': g.GRAPH,
                          'input_sources': sources['sources'], 'needs_review': sources['needs_review'],
                          'currency_note': sources['currency_note']})
    db.log_event(run_id, 'Commander', 'run_started', {'objective': objective, 'mode': mode, 'inject': list(inject)})
    return run_id


def spawn(run_id: str) -> None:
    """Execute in the background; keep a reference so the task is not garbage-collected."""
    t = asyncio.get_running_loop().create_task(execute(run_id))
    _background.add(t)
    t.add_done_callback(_background.discard)


async def execute(run_id: str) -> None:
    with db.tx() as c:
        if c.execute("UPDATE runs SET status='RUNNING' WHERE run_id=? AND status='PENDING'", (run_id,)).rowcount != 1:
            return  # someone else owns the run, or it is not runnable
    paused = False
    try:
        while True:
            # Emergency stop (A3): dispatch nothing new; the task that was running has finished, PENDING ones
            # wait here and the run carries on after /admin/resume. Cancel still works while paused.
            # ponytail: polls system_stop every STOP_POLL_S; an asyncio.Event if many runs ever wait at once.
            if db.get_stop_state()['stopped']:
                with db.tx() as c:
                    if _get_run_row(c, run_id)['status'] != 'RUNNING':
                        break
                    if not paused:
                        _decision(c, run_id, 'dispatch_paused', None, '01', detail={'reason': 'emergency stop'})
                paused = True
                await asyncio.sleep(stop_poll())
                continue
            if paused:
                with db.tx() as c:
                    _decision(c, run_id, 'dispatch_resumed', None, '01', detail={'reason': 'emergency stop cleared'})
                paused = False
            with db.tx() as c:
                run = c.execute('SELECT * FROM runs WHERE run_id=?', (run_id,)).fetchone()
                if run['status'] != 'RUNNING':
                    break  # cancelled between tasks
                st = _statuses(c, run_id)
                while skip := g.to_skip(st, g.GRAPH, g.SOFT):
                    for k in skip:
                        bad = [d for d in g.GRAPH[k] if st[d] in g.BLOCKING]
                        _move(c, run_id, k, g.PENDING, g.SKIPPED, error=f'dependency not completed: {", ".join(bad)}',
                              finished_at=db.now())
                        _decision(c, run_id, 'task_skipped', k, g.TASKS[k][0], detail={'blocked_by': bad})
                        st[k] = g.SKIPPED
                key = g.next_ready(st, g.GRAPH, g.SOFT)
                if key is None:
                    break
                if key == 'monitor' and run['max_rework'] and _rework_point(c, run_id, run, st):
                    continue  # work was sent back: dispatch the target first
                attempt = c.execute('SELECT attempt FROM tasks WHERE run_id=? AND task_key=?',
                                    (run_id, key)).fetchone()[0] + 1
                rw = _open_rework(c, run_id)
                in_rework = bool(rw and key in rw['changes'])
                reason = g.dispatch_reason(key, g.GRAPH, g.SOFT, attempt, rw['reason'] if in_rework else None)
                if not _move(c, run_id, key, g.PENDING, g.RUNNING, attempt=attempt, started_at=db.now(),
                             finished_at=None, error=None):
                    continue
                _decision(c, run_id, 'dispatch', key, g.TASKS[key][0],
                          detail={'reason': reason, 'attempt': attempt, 'deps': g.GRAPH[key],
                                  **({'rework_round': rw['round']} if in_rework else {})})
                inputs = {}
                for dep in g.GRAPH[key]:
                    row = c.execute('SELECT a.payload FROM tasks t JOIN artifacts a ON a.artifact_id=t.artifact_id '
                                    'WHERE t.run_id=? AND t.task_key=?', (run_id, dep)).fetchone()
                    if row is not None:  # a soft task may start with failed/skipped deps: only real artifacts are handed on
                        inputs[dep] = json.loads(row['payload'])
                inject = json.loads(run['inject'])
                fact_checks, art_checks = _run_checks(c, run_id)
                facts, applied = fixes.apply_facts(data.facts_for(inject, run['objective']), fact_checks,
                                                   data.facts_for((), run['objective']))
                ctx = Ctx(run_id, key, g.TASKS[key][0], run['objective'], run['mode'], inject, attempt, facts, inputs,
                          feedback=tuple(rw['feedback']) if in_rework and key == rw['target'] else (),
                          rework=in_rework, checks=tuple(art_checks.get(key, ())),
                          applied=tuple(applied) if key in g.BUSINESS else ())
            if step_delay(ctx.mode):
                await asyncio.sleep(step_delay(ctx.mode))  # task shows RUNNING meanwhile
            await _run_task(ctx)
    finally:
        _finish(run_id)


async def _run_task(ctx: Ctx) -> None:
    handler = HANDLERS.get(ctx.task_key) or DEFAULT_HANDLER
    if handler is None:
        from app.agents import handle as handler
    started = time.monotonic()
    input_hash = _hash(ctx.inputs)
    db.log_event(ctx.run_id, ctx.agent_id, 'task_started', {'task': ctx.task_key, 'attempt': ctx.attempt})
    try:
        result = handler(ctx)
        if inspect.isawaitable(result):
            result = await asyncio.wait_for(result, timeout=task_timeout(ctx.mode))
        if not isinstance(result, dict) or not result.get('type'):
            raise ValueError('agent returned no artifact (dict with "type" required)')
        applied = result.pop('checks_applied', None) or []
        errors = schemas.validate(result) if result['type'] in schemas.SPEC else []
        if errors:
            _store_invalid(ctx, result, errors)
            raise ValueError('artifact failed schema: ' + '; '.join(errors[:5]))
    except asyncio.TimeoutError:
        _fail(ctx, f'timeout after {task_timeout(ctx.mode):g}s', started, input_hash)
        return
    except Exception as exc:  # any agent failure becomes a FAILED task, never a silent success
        _fail(ctx, f'{type(exc).__name__}: {str(exc)[:300]}', started, input_hash)
        return
    ms = int((time.monotonic() - started) * 1000)
    with db.tx() as c:
        art = c.execute('INSERT INTO artifacts(run_id,task_key,agent_id,type,attempt,payload,narrative,created_at) '
                        'VALUES (?,?,?,?,?,?,?,?)',
                        (ctx.run_id, ctx.task_key, ctx.agent_id, result['type'], ctx.attempt,
                         json.dumps(result, ensure_ascii=False), result.get('narrative'), db.now())).lastrowid
        if _move(c, ctx.run_id, ctx.task_key, g.RUNNING, g.COMPLETED, artifact_id=art, finished_at=db.now()):
            _decision(c, ctx.run_id, 'task_completed', ctx.task_key, ctx.agent_id, input_hash=input_hash,
                      output_ref=f'artifact:{art}', duration_ms=ms,
                      detail={'inputs_from': sorted(ctx.inputs), 'attempt': ctx.attempt})
            for item in applied:
                _decision(c, ctx.run_id, 'check_applied', ctx.task_key, ctx.agent_id, output_ref=f'artifact:{art}',
                          detail={**item, 'attempt': ctx.attempt})
            _decision(c, ctx.run_id, 'dispatch_result', ctx.task_key, ctx.agent_id,
                      detail={'outcome': 'done', 'attempt': ctx.attempt})
    db.log_event(ctx.run_id, ctx.agent_id, 'task_completed', {'task': ctx.task_key, 'artifact_id': art})


def _store_invalid(ctx: Ctx, result: dict, errors: list) -> None:
    """Keep the rejected artifact as evidence (valid=0); it is never linked to the task or handed on."""
    with db.tx() as c:
        c.execute('INSERT INTO artifacts(run_id,task_key,agent_id,type,attempt,payload,narrative,valid,validation_errors,created_at) '
                  'VALUES (?,?,?,?,?,?,?,0,?,?)',
                  (ctx.run_id, ctx.task_key, ctx.agent_id, result['type'], ctx.attempt,
                   json.dumps(result, ensure_ascii=False), result.get('narrative'), json.dumps(errors, ensure_ascii=False), db.now()))


def _fail(ctx: Ctx, error: str, started: float, input_hash: str) -> None:
    ms = int((time.monotonic() - started) * 1000)
    with db.tx() as c:
        if _move(c, ctx.run_id, ctx.task_key, g.RUNNING, g.FAILED, error=error, finished_at=db.now()):
            _decision(c, ctx.run_id, 'task_failed', ctx.task_key, ctx.agent_id, input_hash=input_hash,
                      duration_ms=ms, detail={'error': error, 'attempt': ctx.attempt})
            _decision(c, ctx.run_id, 'dispatch_result', ctx.task_key, ctx.agent_id,
                      detail={'outcome': 'failed', 'attempt': ctx.attempt})
    db.log_event(ctx.run_id, ctx.agent_id, 'task_failed', {'task': ctx.task_key, 'error': error})


def _interrupt_orphans(c, run_id: str, reason: str) -> list:
    """Tasks still RUNNING with no executor (process stopping, or a crash) become FAILED so they can be retried."""
    hit = []
    for row in c.execute('SELECT task_key, status, attempt FROM tasks WHERE run_id=?', (run_id,)).fetchall():
        key, st, attempt = row['task_key'], row['status'], row['attempt']
        if st == g.RUNNING and _move(c, run_id, key, g.RUNNING, g.FAILED, error=f'interrupted: {reason}', finished_at=db.now()):
            _decision(c, run_id, 'task_interrupted', key, g.TASKS[key][0], detail={'reason': reason})
            _decision(c, run_id, 'dispatch_result', key, g.TASKS[key][0],
                      detail={'outcome': 'interrupted', 'attempt': attempt})
            hit.append(key)
    return hit


def _finish(run_id: str) -> None:
    with db.tx() as c:
        # The executor loop is over: a task still RUNNING here was cut off (e.g. uvicorn cancelled us on shutdown).
        _interrupt_orphans(c, run_id, 'executor stopped (service shutdown)')
        run = c.execute('SELECT status FROM runs WHERE run_id=?', (run_id,)).fetchone()
        if run['status'] == 'CANCELLED':
            _cancel_open_tasks(c, run_id)
            final = 'CANCELLED'
        else:
            final = g.run_status(_statuses(c, run_id))
            if final in ('PENDING', 'RUNNING'):
                final = 'FAILED'  # executor stopped with work left: never report it as still going
            pending = c.execute("SELECT COUNT(*) FROM approvals WHERE run_id=? AND status='PENDING'", (run_id,)).fetchone()[0]
            if final == 'COMPLETED' and pending:
                final = 'WAITING_APPROVAL'  # Human-in-the-Loop: a parked action needs a decision
            c.execute("UPDATE runs SET status=?, finished_at=? WHERE run_id=? AND status='RUNNING'",
                      (final, None if final == 'WAITING_APPROVAL' else db.now(), run_id))
        _decision(c, run_id, 'run_finished', 'summary', '01', detail={'status': final})
    db.log_event(run_id, 'Commander', 'run_finished', {'status': final})


def _cancel_open_tasks(c, run_id):
    for key, st in _statuses(c, run_id).items():
        if st in (g.PENDING, g.SKIPPED):
            _move(c, run_id, key, st, g.CANCELLED, finished_at=db.now())
    c.execute('UPDATE runs SET finished_at=COALESCE(finished_at, ?) WHERE run_id=?', (db.now(), run_id))


def cancel(run_id: str) -> str:
    with db.tx() as c:
        run = _get_run_row(c, run_id)
        if run['status'] not in ACTIVE_RUN_STATES:
            raise WorkflowError(409, f'run is already {run["status"]}')
        c.execute('UPDATE runs SET status=? WHERE run_id=?', ('CANCELLED', run_id))
        c.execute("UPDATE approvals SET status='REJECTED', decided_at=? WHERE run_id=? AND status='PENDING'", (db.now(), run_id))
        _decision(c, run_id, 'run_cancelled', None, None, detail={'previous': run['status']})
        if run['status'] != 'RUNNING':
            _cancel_open_tasks(c, run_id)  # no executor loop alive to do it
    db.log_event(run_id, 'Commander', 'run_cancelled', {})
    return 'CANCELLED'


def retry(run_id: str, task_key: str) -> None:
    """Re-arm one FAILED task (and its SKIPPED descendants). COMPLETED artifacts are kept as they are."""
    with db.tx() as c:
        run = _get_run_row(c, run_id)
        if task_key not in g.TASKS:
            raise WorkflowError(404, f'unknown task {task_key}')
        if run['status'] != 'FAILED':
            raise WorkflowError(409, f'only a FAILED run can be retried; run is {run["status"]}')
        st = _statuses(c, run_id)
        try:
            changes = g.retry_plan(task_key, st, g.GRAPH, g.SOFT)
        except ValueError as exc:
            raise WorkflowError(409, str(exc))
        for key, dst in changes.items():
            _move(c, run_id, key, st[key], dst, error=None, finished_at=None)
        c.execute("UPDATE runs SET status='PENDING', finished_at=NULL WHERE run_id=? AND status='FAILED'", (run_id,))
        _decision(c, run_id, 'task_retry', task_key, g.TASKS[task_key][0], detail={'rearmed': sorted(changes)})
    db.log_event(run_id, g.TASKS[task_key][0], 'task_retry', {'task': task_key})


def recover() -> list:
    """Startup checkpoint handling: tasks left RUNNING by a dead process become FAILED ('interrupted') so
    they can be retried; runs that had not started any task are resumed. Returns run ids to resume."""
    resume = []
    with db.tx() as c:
        # Any run with an orphaned RUNNING task, whatever the run status says (a killed process never ran _finish).
        rows = c.execute("SELECT DISTINCT r.run_id, r.status FROM runs r LEFT JOIN tasks t ON t.run_id=r.run_id "
                         "WHERE r.status IN ('PENDING','RUNNING') OR t.status='RUNNING'").fetchall()
        for run in rows:
            rid = run['run_id']
            _interrupt_orphans(c, rid, 'service restarted')
            if run['status'] not in ('PENDING', 'RUNNING'):
                continue  # run already has a final status; its interrupted task is now retryable
            final = g.run_status(_statuses(c, rid))
            if final == 'PENDING':
                c.execute("UPDATE runs SET status='PENDING' WHERE run_id=?", (rid,))
                resume.append(rid)
            else:
                c.execute('UPDATE runs SET status=?, finished_at=? WHERE run_id=?', (final, db.now(), rid))
            _decision(c, rid, 'run_recovered', None, None, detail={'status': final})
    return resume


# ---- read side (replay never calls an agent or the LLM) ---------------------------------------------

def _get_run_row(c, run_id):
    run = c.execute('SELECT * FROM runs WHERE run_id=?', (run_id,)).fetchone()
    if run is None:
        raise WorkflowError(404, 'run not found')
    return run


def get_run(run_id: str) -> dict:
    with db.tx() as c:
        _get_run_row(c, run_id)
        run = dict(c.execute('SELECT rowid AS seq, * FROM runs WHERE run_id=?', (run_id,)).fetchone())  # seq = friendly run number
        tasks = []
        for t in c.execute('SELECT t.*, a.payload, a.narrative, a.type AS artifact_type FROM tasks t '
                           'LEFT JOIN artifacts a ON a.artifact_id=t.artifact_id WHERE t.run_id=?', (run_id,)):
            t = dict(t)
            t['depends_on'] = json.loads(t['depends_on'])
            t['artifact'] = json.loads(t.pop('payload')) if t['artifact_id'] else None
            tasks.append(t)
        order = {k: i for i, k in enumerate(g.TASKS)}
        tasks.sort(key=lambda t: order[t['task_key']])
        llm = c.execute('SELECT COUNT(*), COALESCE(SUM(prompt_tokens+completion_tokens),0), COALESCE(SUM(cost_est),0) '
                        'FROM llm_calls WHERE run_id=?', (run_id,)).fetchone()
        engines = [{**dict(r), 'findings': json.loads(r['findings'])} for r in c.execute(
            'SELECT * FROM engine_results WHERE run_id=? ORDER BY id', (run_id,))]
        approvals = [dict(r) for r in c.execute('SELECT * FROM approvals WHERE run_id=? ORDER BY id', (run_id,))]
        rework = [{**dict(r), **{k: json.loads(r[k]) for k in ('source_result_ids', 'findings', 'checks')}}
                  for r in c.execute('SELECT * FROM rework_requests WHERE run_id=? ORDER BY round', (run_id,))]
        dispatch_rows = c.execute("SELECT task_key, detail, ts FROM decision_log WHERE run_id=? AND action='dispatch' "
                                  'ORDER BY id', (run_id,)).fetchall()
    last_dispatch = {}  # latest dispatch per task (a retry dispatches again); links each task back to its reason
    for r in dispatch_rows:
        last_dispatch[r['task_key']] = {**json.loads(r['detail']), 'ts': r['ts']}
    for t in tasks:
        t['last_dispatch'] = last_dispatch.get(t['task_key'])
    run['inject'] = json.loads(run['inject'])
    latest = {e['engine']: e for e in engines}  # newest per engine (a retry re-runs supervisors)
    return {'environment': 'MOCK_ONLY', 'run': run, 'tasks': tasks,
            'llm': {'calls': llm[0], 'tokens': llm[1], 'cost_est': llm[2]},
            'engines': latest, 'approvals': approvals,
            'rework': {'requests': rework, **rework_summary(run_id)}}


def completed_artifacts(run_id: str) -> dict:
    """task_key -> payload of every COMPLETED task (read-only; Commander and supervisors use it)."""
    with db.tx() as c:
        rows = c.execute('SELECT t.task_key, a.payload FROM tasks t JOIN artifacts a ON a.artifact_id=t.artifact_id '
                         "WHERE t.run_id=? AND t.status='COMPLETED'", (run_id,)).fetchall()
    return {r['task_key']: json.loads(r['payload']) for r in rows}


def rejected_artifacts(run_id: str) -> dict:
    """task_key -> validation errors of rejected (valid=0) artifacts, latest wins."""
    with db.tx() as c:
        rows = c.execute('SELECT task_key, validation_errors FROM artifacts WHERE run_id=? AND valid=0 ORDER BY artifact_id',
                         (run_id,)).fetchall()
    return {r['task_key']: json.loads(r['validation_errors'] or '[]') for r in rows}


def tool_calls(run_id: str) -> list:
    """Gateway calls of each task's current attempt only (A3): a retried task's old calls, e.g. a BLOCK of
    attempt 1, are no longer reported by the Audit. decision-log over HTTP still returns every row."""
    from app.core import gateway
    with db.tx() as c:
        rows = c.execute("SELECT task_key, agent_id, tool, permission, allowed, detail FROM decision_log "
                         "WHERE run_id=? AND action='tool_call' ORDER BY id", (run_id,)).fetchall()
        attempts = {r['task_key']: r['attempt'] for r in c.execute('SELECT task_key, attempt FROM tasks WHERE run_id=?',
                                                                   (run_id,))}
    return gateway.current_attempt([{**dict(r), 'detail': json.loads(r['detail'] or '{}')} for r in rows], attempts)


def save_engine_result(run_id: str, result: dict) -> int:
    with db.tx() as c:
        rid = c.execute('INSERT INTO engine_results(run_id,engine,status,findings,created_at) VALUES (?,?,?,?,?)',
                        (run_id, result['engine'], result['status'],
                         json.dumps(result['findings'], ensure_ascii=False), db.now())).lastrowid
        _decision(c, run_id, 'engine_result', result['engine'], None, output_ref=f'engine_result:{rid}',
                  detail={'status': result['status'], 'findings': len(result['findings'])})
    return rid


def decide_approval(run_id: str, approval_id: int, decision: str, actor: str | None = None) -> str:
    """Human decision on a parked action. The run leaves WAITING_APPROVAL when nothing is pending.
    Approval only marks the mock DRAFT as approved; nothing is published (DEMO ONLY)."""
    if decision not in ('APPROVED', 'REJECTED'):
        raise WorkflowError(422, 'decision must be APPROVED or REJECTED')
    with db.tx() as c:
        run = _get_run_row(c, run_id)
        if c.execute("UPDATE approvals SET status=?, decided_at=?, decided_by=? WHERE id=? AND run_id=? "
                     "AND status='PENDING'", (decision, db.now(), actor, approval_id, run_id)).rowcount != 1:
            raise WorkflowError(409, 'approval not found or already decided')
        _decision(c, run_id, 'human_approval', None, None,
                  detail={'approval_id': approval_id, 'decision': decision, 'decided_by': actor})
        left = c.execute("SELECT COUNT(*) FROM approvals WHERE run_id=? AND status='PENDING'", (run_id,)).fetchone()[0]
        status = run['status']
        if run['status'] == 'WAITING_APPROVAL' and not left:
            status = 'COMPLETED'
            c.execute("UPDATE runs SET status='COMPLETED', finished_at=? WHERE run_id=? AND status='WAITING_APPROVAL'",
                      (db.now(), run_id))
    db.log_event(run_id, actor or 'Human', 'approval', {'approval_id': approval_id, 'decision': decision})
    return status


def evidence(run_id: str) -> dict:
    """Run health records for the Monitor: task states/attempts and LLM usage."""
    with db.tx() as c:
        tasks = [dict(r) for r in c.execute('SELECT task_key, status, attempt, error FROM tasks WHERE run_id=?', (run_id,))]
        llm = c.execute("SELECT COUNT(*), COALESCE(SUM(prompt_tokens+completion_tokens),0), "
                        "COALESCE(SUM(CASE WHEN status NOT IN ('COMPLETED','WARN') THEN 1 ELSE 0 END),0) "
                        'FROM llm_calls WHERE run_id=?', (run_id,)).fetchone()
    order = {k: i for i, k in enumerate(g.TASKS)}
    tasks.sort(key=lambda t: order[t['task_key']])
    sources = {k: a.get('narrative_source') for k, a in completed_artifacts(run_id).items()}
    return {'tasks': tasks, 'llm': {'calls': llm[0], 'tokens': llm[1], 'errors': llm[2]}, 'narrative_sources': sources,
            'rework': rework_summary(run_id)}


def list_runs(limit: int = 50) -> list:
    with db.tx() as c:
        rows = c.execute('SELECT rowid AS seq,run_id,objective,mode,status,inject,created_at,finished_at FROM runs '
                         'ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    return [{**dict(r), 'inject': json.loads(r['inject'])} for r in rows]


def table(run_id: str, name: str) -> list:
    if name not in ('decision_log', 'llm_calls'):
        raise ValueError(name)
    with db.tx() as c:
        _get_run_row(c, run_id)
        return [dict(r) for r in c.execute(f'SELECT * FROM {name} WHERE run_id=? ORDER BY id', (run_id,))]


# ---- A4: rework loop (DEMO_PLAN_OPTION_A 7.2) ---------------------------------------------------------
# Volatile fields left out of the NO_CHANGE hash: they change on every run without the work changing.
VOLATILE = ('narrative', 'narrative_source', 'rework_feedback', 'memory_notes', 'action_results', 'memory_used',
            'checks_applied')


def _target_hash(c, run_id, task_key):
    row = c.execute('SELECT a.payload FROM tasks t JOIN artifacts a ON a.artifact_id=t.artifact_id '
                    'WHERE t.run_id=? AND t.task_key=?', (run_id, task_key)).fetchone()
    payload = json.loads(row['payload']) if row else {}
    return _hash({k: v for k, v in payload.items() if k not in VOLATILE})


def _latest_engines(c, run_id) -> dict:
    out = {}
    for r in c.execute("SELECT id, engine, status, findings FROM engine_results WHERE run_id=? AND engine IN ('qa','audit') "
                       'ORDER BY id', (run_id,)):
        out[r['engine']] = {'id': r['id'], 'status': r['status'], 'findings': json.loads(r['findings'])}
    return out


def _open_rework(c, run_id):
    """The OPEN rework request of the run with the plan it was made from (changes, feedback), or None."""
    req = c.execute("SELECT * FROM rework_requests WHERE run_id=? AND status='OPEN' ORDER BY round DESC LIMIT 1",
                    (run_id,)).fetchone()
    if req is None:
        return None
    row = c.execute("SELECT detail FROM decision_log WHERE run_id=? AND action='rework_requested' ORDER BY id DESC LIMIT 1",
                    (run_id,)).fetchone()
    plan = json.loads(row['detail']) if row else {}
    return {'round': req['round'], 'target': req['target_task'], 'changes': plan.get('changes', []),
            'feedback': plan.get('feedback', []), 'reason': plan.get('reason', '')}


def _run_checks(c, run_id):
    """(facts-level checks, {task_key: artifact-level checks}) from every rework request of this run.
    drop_blocked_action:<tool> is only given to the task whose own blocked_action finding named that tool."""
    fact_checks, art_checks = set(), {}
    for r in c.execute('SELECT findings, checks FROM rework_requests WHERE run_id=?', (run_id,)):
        fact_checks |= {ch for ch in json.loads(r['checks']) if fixes.level(ch) == 'facts'}
        for f in json.loads(r['findings']):
            if f.get('rule') == 'blocked_action':
                ch = f"{fixes.FIX['blocked_action']}:{str(f.get('detail', '')).split(' ', 1)[0]}"
                art_checks.setdefault(f['task_key'], set()).add(ch)
    return sorted(fact_checks), {k: sorted(v) for k, v in art_checks.items()}


def _resolved(req, engines) -> bool:
    """RESOLVED: for each source finding, the newest result of the same engine has no FAIL with the same
    (rule, task_key) and that engine's status is not FAIL. Leftover WARNs do not block."""
    for f in json.loads(req['findings']):
        e = engines.get(f.get('engine'))
        if e is None or e['status'] == 'FAIL' or any(
                x['severity'] == 'FAIL' and x['rule'] == f['rule'] and x['task_key'] == f['task_key'] for x in e['findings']):
            return False
    return True


def _close(c, run_id, req, status):
    c.execute('UPDATE rework_requests SET status=?, resolved_at=? WHERE id=?', (status, db.now(), req['id']))


def _rework_point(c, run_id, run, st) -> bool:
    """Decision point: QA and Audit are done, the Monitor has not run. Settle the previous request, then maybe
    send work back. True when tasks were re-armed (the caller loops to dispatch them)."""
    engines = _latest_engines(c, run_id)
    reqs = c.execute('SELECT * FROM rework_requests WHERE run_id=? ORDER BY round', (run_id,)).fetchall()
    last = reqs[-1] if reqs else None
    unresolved = None
    if last is not None and last['status'] == 'OPEN':
        if _resolved(last, engines):
            _close(c, run_id, last, 'RESOLVED')
            _decision(c, run_id, 'rework_resolved', last['target_task'], '01', detail={'round': last['round']})
        elif _target_hash(c, run_id, last['target_task']) == last['prev_hash']:
            _close(c, run_id, last, 'NO_CHANGE')  # safety net: the rework produced the same artifact
            _decision(c, run_id, 'rework_skipped', last['target_task'], '01',
                      detail={'reason': 'no_change', 'round': last['round']})
            return False
        else:
            unresolved = last
    findings = [{**f, 'engine': name} for name in ('qa', 'audit') if name in engines for f in engines[name]['findings']]
    plan, reason = g.rework_plan(findings, st, len(reqs), g.GRAPH, g.SOFT, run['max_rework'], fixes.FIX)
    if unresolved is not None:
        # ponytail: a round that changed the artifact but left a FAIL is closed EXHAUSTED (its round is spent);
        # whether the whole loop is exhausted is told by rework_skipped(reason='exhausted'), see rework_summary().
        _close(c, run_id, unresolved, 'EXHAUSTED')
    if plan is None:
        if reason != 'no_fail':  # a healthy run gets no rework rows at all
            _decision(c, run_id, 'rework_skipped', None, '01', detail={'reason': reason, 'rounds_used': len(reqs)})
        return False
    target, rnd = plan['target'], len(reqs) + 1
    c.execute('INSERT INTO rework_requests(run_id,round,target_task,agent_id,source_result_ids,findings,checks,status,'
              'prev_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',
              (run_id, rnd, target, g.TASKS[target][0], json.dumps(sorted(e['id'] for e in engines.values())),
               json.dumps(plan['findings'], ensure_ascii=False), json.dumps(plan['checks']), 'OPEN',
               _target_hash(c, run_id, target), db.now()))
    for key, (src, dst) in plan['changes'].items():
        _move(c, run_id, key, src, dst, rework=True, error=None, finished_at=None)
    _decision(c, run_id, 'rework_requested', target, '01',
              detail={'round': rnd, 'target': target, 'agent_id': g.TASKS[target][0],
                      'rule': ', '.join(sorted({f['rule'] for f in plan['feedback']})), 'reason': plan['reason'],
                      'changes': list(plan['changes']), 'checks': plan['checks'],
                      'feedback': [{k: f[k] for k in ('rule', 'task_key', 'detail', 'engine')} for f in plan['feedback']]})
    return True


def rework_summary(run_id: str) -> dict:
    """For the Monitor and get_run: tasks sent back by the rework loop, and whether it stopped without fixing."""
    with db.tx() as c:
        rows = c.execute("SELECT action, detail FROM decision_log WHERE run_id=? "
                         "AND action IN ('rework_requested','rework_skipped') ORDER BY id", (run_id,)).fetchall()
    reworked, exhausted = set(), False
    for r in rows:
        d = json.loads(r['detail'] or '{}')
        if r['action'] == 'rework_requested':
            reworked |= set(d.get('changes', []))
        elif d.get('reason') in ('exhausted', 'no_change'):
            exhausted = True
    return {'reworked_tasks': sorted(reworked), 'exhausted': exhausted}


# Child-before-parent so `PRAGMA foreign_keys = ON` doesn't block the delete.
RESET_TABLES = (
    'room_messages', 'rooms', 'rework_requests', 'learning_runs',
    'channel_outbox', 'channel_inbox', 'brain_inbox',
    'decision_log', 'llm_calls', 'approvals', 'engine_results', 'artifacts', 'tasks', 'runs', 'events',
)
# Never deleted by reset_demo, in either mode: learning_meta counters, and the emergency stop + its log.
RESET_EXCLUDE_ALWAYS = ('learning_meta', 'system_stop', 'system_stop_log')
# Only deleted when include_memory=True, and only intended for a test database (see AGENTS.md M-06 / A2 ticket).
MEMORY_TABLES = ('memory_items', 'learning_proposals')


def reset_demo(include_memory: bool = False) -> dict:
    """Delete every run and its records; keep the schema. Refused while a run is active (409).

    include_memory=False (default) keeps memory_items and decided learning_proposals (OA-D05);
    any proposal still open (PROPOSED/REPLAYED_*) is expired since its source run is gone.
    include_memory=True also deletes memory_items and learning_proposals outright — a test-DB-only path.
    learning_meta and system_stop/system_stop_log are never touched by either mode.
    """
    with db.tx() as c:
        active = c.execute("SELECT COUNT(*) FROM runs WHERE status IN ('PENDING','RUNNING')").fetchone()[0]
        if active:
            raise WorkflowError(409, f'{active} run(s) still active; cancel them first')
        counts = {t: c.execute(f'DELETE FROM {t}').rowcount for t in RESET_TABLES}
        if include_memory:
            counts.update({t: c.execute(f'DELETE FROM {t}').rowcount for t in MEMORY_TABLES})
        else:
            counts['learning_proposals_expired'] = c.execute(
                "UPDATE learning_proposals SET status='EXPIRED', decided_at=? "
                "WHERE status IN ('PROPOSED','REPLAYED_PASS','REPLAYED_FAIL')", (db.now(),)).rowcount
    return counts
