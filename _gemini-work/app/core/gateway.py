"""Mock Tool Gateway: the only path for an agent to "Act" (Think != Act). Every call asks the Audit Engine
first and is written to decision_log. Nothing leaves the container: ALLOW creates a DRAFT inside the mock
systems, NEEDS_APPROVAL parks the action for a human, BLOCK never executes."""
import json

from app import db
from app.engines import audit


def execute(run_id: str, task_key: str, agent_id: str, action: dict) -> dict:
    tool, target = action['tool'], action.get('target')
    verdict = audit.check_action(agent_id, tool, action)
    result = {'tool': tool, 'target': target, **verdict}
    with db.tx() as c:
        if verdict['decision'] == 'ALLOW':
            result['result'] = {'status': 'DRAFT', 'system': tool.split('.')[0] + ' (mock)', 'target': target}
        elif verdict['decision'] == 'NEEDS_APPROVAL':
            aid = c.execute('INSERT INTO approvals(run_id,task_key,reason,amount,status,created_at) VALUES (?,?,?,?,?,?)',
                            (run_id, task_key, f'{tool} {target}: {verdict["reason"]}', action.get('budget_php'),
                             'PENDING', db.now())).lastrowid
            result['result'] = {'status': 'WAITING_APPROVAL', 'approval_id': aid}
        else:
            result['result'] = {'status': 'BLOCKED'}
        c.execute('INSERT INTO decision_log(run_id,task_key,agent_id,action,tool,permission,allowed,detail,ts) '
                  'VALUES (?,?,?,?,?,?,?,?,?)',
                  (run_id, task_key, agent_id, 'tool_call', tool, verdict['permission'],
                   int(verdict['decision'] != 'BLOCK'),
                   json.dumps({'decision': verdict['decision'], 'target': target, 'reason': verdict['reason'],
                               'result': result['result']}, ensure_ascii=False), db.now()))
    db.log_event(run_id, agent_id, 'tool_call', {'tool': tool, 'decision': verdict['decision']})
    return result
