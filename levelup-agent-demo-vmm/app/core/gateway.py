"""Mock Tool Gateway: the only path for an agent to "Act" (Think != Act). Every call asks the Audit Engine
first and is written to decision_log. Nothing leaves the container: ALLOW creates a DRAFT inside the mock
systems, NEEDS_APPROVAL parks the action for a human, BLOCK never executes.

Safe re-runs (A3): each call records `attempt` and `action_hash`. When a task runs again (retry, later rework)
and asks for the very same action with the same verdict, the earlier result is reused: no second DRAFT or
approval, but a new tool_call row (copy of the original detail + reused=true) so the Audit of the current
attempt still sees the call. Audit always runs first, so a changed threshold or budget never skips HITL."""
import hashlib
import json

from app import db
from app.engines import audit


def action_hash(action: dict) -> str:
    """sha256 of the canonical JSON of the whole action (key order and spacing do not matter)."""
    canon = json.dumps(action, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()


def reusable(prior: list, target, a_hash: str, decision: str) -> dict | None:
    """Pure. `prior` = details of earlier tool_call rows of the same (run, task, tool), oldest first.
    Returns the newest one that was not BLOCK, has the same target and action_hash, and whose decision
    equals the new verdict; None means take the normal path."""
    for d in reversed(prior):
        if d.get('decision') != 'BLOCK' and d.get('decision') == decision \
                and d.get('target') == target and d.get('action_hash') == a_hash:
            return d
    return None


def current_attempt(rows: list, attempts: dict) -> list:
    """Pure. Keep tool_call rows whose detail.attempt equals the task's current attempt in `attempts`
    (task_key -> tasks.attempt). Rows written before A3 have no attempt and count as attempt 1;
    a task missing from `attempts` is treated as attempt 1 as well. Order is preserved."""
    return [r for r in rows
            if (r.get('detail') or {}).get('attempt', 1) == attempts.get(r.get('task_key'), 1)]


def execute(run_id: str, task_key: str, agent_id: str, action: dict, attempt: int = 1) -> dict:
    tool, target = action['tool'], action.get('target')
    verdict = audit.check_action(agent_id, tool, action)  # always first, even when a result could be reused
    a_hash = action_hash(action)
    with db.tx() as c:
        prior = [json.loads(r['detail'] or '{}') for r in c.execute(
            "SELECT detail FROM decision_log WHERE run_id=? AND task_key=? AND action='tool_call' AND tool=? "
            'ORDER BY id', (run_id, task_key, tool))]
        old = reusable(prior, target, a_hash, verdict['decision'])
        if old is not None:
            detail = {**old, 'attempt': attempt, 'reused': True}
            result = {'tool': tool, 'target': target, **verdict, 'result': old.get('result'), 'reused': True}
        else:
            result = {'tool': tool, 'target': target, **verdict}
            if verdict['decision'] == 'ALLOW':
                result['result'] = {'status': 'DRAFT', 'system': tool.split('.')[0] + ' (mock)', 'target': target}
            elif verdict['decision'] == 'NEEDS_APPROVAL':
                aid = c.execute('INSERT INTO approvals(run_id,task_key,tool,reason,amount,status,created_at) '
                                'VALUES (?,?,?,?,?,?,?)',
                                (run_id, task_key, tool, f'{tool} {target}: {verdict["reason"]}',
                                 action.get('budget_php'), 'PENDING', db.now())).lastrowid
                result['result'] = {'status': 'WAITING_APPROVAL', 'approval_id': aid}
            else:
                result['result'] = {'status': 'BLOCKED'}
            detail = {'decision': verdict['decision'], 'target': target, 'reason': verdict['reason'],
                      'result': result['result'], 'attempt': attempt, 'action_hash': a_hash}
        c.execute('INSERT INTO decision_log(run_id,task_key,agent_id,action,tool,permission,allowed,detail,ts) '
                  'VALUES (?,?,?,?,?,?,?,?,?)',
                  (run_id, task_key, agent_id, 'tool_call', tool, verdict['permission'],
                   int(verdict['decision'] != 'BLOCK'), json.dumps(detail, ensure_ascii=False), db.now()))
    db.log_event(run_id, agent_id, 'tool_call', {'tool': tool, 'decision': verdict['decision'],
                                                 'reused': old is not None})
    return result
