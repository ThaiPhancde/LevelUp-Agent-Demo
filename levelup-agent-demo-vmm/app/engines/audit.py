"""Audit Engine (deterministic, no LLM): permission decisions for the gateway and a post-run audit.

check_action() is what the Mock Tool Gateway calls before any "Act". run() audits the decision_log:
  blocked_action    an agent attempted a tool it may not use (e.g. meta_ads.publish) -> FAIL, it was blocked
  not_via_gateway   an artifact requested an action that has no gateway decision -> FAIL
  draft_only        campaign artifact not in DRAFT -> FAIL
  pending_approval  an action waits for a human (HITL threshold) -> WARN
"""
import os

from app.core import registry
from app.core.graph import BUSINESS


def approval_threshold() -> float:
    return float(os.getenv('APPROVAL_THRESHOLD_PHP', '5000'))


def check_action(agent_id: str, tool: str, payload: dict | None = None) -> dict:
    """Decision for one requested action: ALLOW (executes as DRAFT), NEEDS_APPROVAL, or BLOCK."""
    need = registry.required_permission(tool)
    if not registry.allowed(agent_id, tool):
        reason = 'WRITE_EXTERNAL is never granted in the demo' if need == registry.WRITE_EXTERNAL \
            else f'agent {agent_id} lacks {need}'
        return {'decision': 'BLOCK', 'permission': need, 'reason': reason}
    budget = (payload or {}).get('budget_php')
    if need == registry.WRITE_DRAFT and budget is not None and float(budget) >= approval_threshold():
        return {'decision': 'NEEDS_APPROVAL', 'permission': need,
                'reason': f'budget {budget} >= approval threshold {approval_threshold():g} PHP'}
    return {'decision': 'ALLOW', 'permission': need, 'reason': 'allowed by registry'}


def _f(rule, task_key, detail, severity='FAIL'):
    return {'rule': rule, 'severity': severity, 'task_key': task_key, 'detail': detail}


def run(arts: dict, tool_calls: list) -> dict:
    """tool_calls = decision_log rows with action='tool_call': {task_key, agent_id, tool, allowed, detail{decision}}."""
    findings = []
    seen = {(t['task_key'], t['tool'], (t.get('detail') or {}).get('target')) for t in tool_calls}
    for t in tool_calls:
        decision = (t.get('detail') or {}).get('decision')
        if decision == 'BLOCK':
            findings.append(_f('blocked_action', t['task_key'], f'{t["tool"]} by agent {t["agent_id"]} was blocked'))
        elif decision == 'NEEDS_APPROVAL':
            findings.append(_f('pending_approval', t['task_key'], f'{t["tool"]} waits for human approval', 'WARN'))
    for key in BUSINESS:
        for act in (arts.get(key) or {}).get('requested_actions', []):
            if (key, act['tool'], act.get('target')) not in seen:
                findings.append(_f('not_via_gateway', key, f'{act["tool"]} {act.get("target")} has no gateway decision'))
    camp = arts.get('campaign')
    if camp and camp.get('status') != 'DRAFT':
        findings.append(_f('draft_only', 'campaign', f'campaign status {camp.get("status")}'))
    status = 'FAIL' if any(f['severity'] == 'FAIL' for f in findings) else ('WARN' if findings else 'PASS')
    return {'engine': 'audit', 'status': status, 'findings': findings,
            'actions': [{'task_key': t['task_key'], 'agent_id': t['agent_id'], 'tool': t['tool'],
                         'decision': (t.get('detail') or {}).get('decision'), 'allowed': bool(t['allowed'])} for t in tool_calls]}
