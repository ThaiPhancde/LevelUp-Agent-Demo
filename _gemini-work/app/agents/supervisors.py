"""Supervisory agents (QA Tester, Auditor, Monitor). They never judge by themselves: each one turns the
result of its deterministic engine (app/engines/*) into a report artifact. The LLM may only explain it."""

_SPEC = {
    'qa': ('qa_report', '11', 'QA'),
    'audit': ('audit_report', '12', 'Audit'),
    'monitor': ('monitoring_report', '13', 'Monitor'),
}


def report(task_key: str, engine_result: dict, engine_result_id: int | None = None) -> dict:
    type_, agent_id, label = _SPEC[task_key]
    fails = sum(1 for f in engine_result['findings'] if f['severity'] == 'FAIL')
    warns = len(engine_result['findings']) - fails
    art = {'type': type_, 'agent_id': agent_id, 'synthetic': True,
           'summary': f'{label} {engine_result["status"]}: {fails} lỗi, {warns} cảnh báo.',
           'status': engine_result['status'], 'findings': engine_result['findings'],
           'engine': engine_result['engine'], 'engine_result_id': engine_result_id}
    if task_key == 'qa':
        art['checked'] = engine_result['checked']
        art['scope'] = 'schema, đối chiếu giá vốn, phép tính, nhất quán, diễn giải'
    elif task_key == 'audit':
        art['actions'] = engine_result['actions']
    else:
        art.update(tasks=engine_result['tasks'], llm_calls=engine_result['llm_calls'], tokens=engine_result['tokens'])
    return art
