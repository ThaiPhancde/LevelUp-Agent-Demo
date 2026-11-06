"""Monitoring Engine (deterministic, no LLM): health of a run from its own records.

evidence = {'tasks': [{task_key, status, attempt, error}], 'llm': {calls, tokens, errors},
            'narrative_sources': {task_key: 'mock'|'llm'|'mock_budget'}}
Rules: timeout (FAIL) · empty_response (FAIL) · task_failed (FAIL) · skipped (WARN) · retried (WARN) ·
       llm_errors (WARN) · token_budget (WARN, LLM budget exhausted and mock text used)
"""
from app.core.graph import BUSINESS

WATCHED = BUSINESS + ('qa', 'audit')


def _f(rule, task_key, detail, severity):
    return {'rule': rule, 'severity': severity, 'task_key': task_key, 'detail': detail}


def classify(error: str | None) -> str:
    e = (error or '').lower()
    if e.startswith('timeout'):
        return 'timeout'
    if 'empty' in e:
        return 'empty_response'
    return 'task_failed'


def run(evidence: dict) -> dict:
    findings = []
    for t in evidence['tasks']:
        if t['task_key'] not in WATCHED:
            continue
        if t['status'] == 'FAILED':
            findings.append(_f(classify(t.get('error')), t['task_key'], t.get('error') or 'failed', 'FAIL'))
        elif t['status'] == 'SKIPPED':
            findings.append(_f('skipped', t['task_key'], t.get('error') or 'skipped', 'WARN'))
        elif t['status'] == 'COMPLETED' and t['attempt'] > 1:
            findings.append(_f('retried', t['task_key'], f'completed on attempt {t["attempt"]}', 'WARN'))
    llm = evidence.get('llm', {})
    if llm.get('errors'):
        findings.append(_f('llm_errors', None, f'{llm["errors"]} failed LLM call(s)', 'WARN'))
    budget_hit = sorted(k for k, v in (evidence.get('narrative_sources') or {}).items() if v == 'mock_budget')
    if budget_hit:
        findings.append(_f('token_budget', None, f'LLM token budget reached; mock text used for {", ".join(budget_hit)}', 'WARN'))
    status = 'FAIL' if any(f['severity'] == 'FAIL' for f in findings) else ('WARN' if findings else 'PASS')
    return {'engine': 'monitor', 'status': status, 'findings': findings,
            'tasks': evidence['tasks'], 'llm_calls': llm.get('calls', 0), 'tokens': llm.get('tokens', 0)}
