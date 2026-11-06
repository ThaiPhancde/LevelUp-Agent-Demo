"""Phase 8 end-to-end scenarios (DEMO_ONLY P8) over real HTTP against a running container.

Skipped unless E2E_BASE_URL is set; `tools/e2e/run_e2e.py` starts a fresh container (Mock Mode, no DeepSeek key,
no step delay, short task timeout) and runs this file from a second container. The in-process suites in tests/
cover the same rules at unit/integration level; these prove the packaged service behaves the same.
"""
import os

import httpx
import pytest

BASE = os.getenv('E2E_BASE_URL')
pytestmark = pytest.mark.skipif(not BASE, reason='E2E_BASE_URL not set (run tools/e2e/run_e2e.py)')


@pytest.fixture(scope='module')
def http():
    with httpx.Client(base_url=BASE, timeout=60) as c:
        yield c


def run(http, **body):
    r = http.post('/runs?wait=true', json=body)
    assert r.status_code == 202, r.text
    return r.json()


def by_key(body):
    return {t['task_key']: t for t in body['tasks']}


def rules(body, engine):
    return {f['rule'] for f in body['engines'][engine]['findings']}


def tool_calls(http, rid):
    return [r for r in http.get(f'/runs/{rid}/decision-log').json() if r['action'] == 'tool_call']


def test_s1_happy_path_commander_coordinates_13_roles_and_reports(http):
    body = run(http)
    t = by_key(body)
    assert body['environment'] == 'MOCK_ONLY' and body['run']['status'] == 'COMPLETED'
    assert {x['status'] for x in t.values()} == {'COMPLETED'} and len(t) == 14
    assert len({x['agent_id'] for x in t.values()}) == 13                       # 13 roles, Commander twice
    assert len({x['artifact']['type'] for x in t.values()}) == 14               # role-specific artifacts
    assert {e: body['engines'][e]['status'] for e in ('qa', 'audit', 'monitor')} == dict.fromkeys(('qa', 'audit', 'monitor'), 'PASS')
    assert t['offer']['artifact']['margin_per_unit_php'] == 226 and t['kpi']['artifact']['roas'] == 1.62
    assert t['summary']['artifact']['decision'] == 'HOLD_DRAFT'
    log = http.get(f"/runs/{body['run']['run_id']}/decision-log").json()
    handoffs = {r['task_key'] for r in log if r['action'] == 'task_completed'}
    assert handoffs == set(t)
    calls = tool_calls(http, body['run']['run_id'])
    assert len(calls) == 8 and all(c['allowed'] == 1 for c in calls)


def test_s2_invalid_cost_qa_marks_fail(http):
    body = run(http, inject=['bad_cost'])
    qa = body['engines']['qa']
    assert qa['status'] == 'FAIL' and 'reference' in rules(body, 'qa')
    assert any('9999' in f['detail'] for f in qa['findings'])
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'


def test_s3_unauthorized_publish_is_blocked_by_auditor(http):
    body = run(http, inject=['publish_attempt'])
    blocked = [c for c in tool_calls(http, body['run']['run_id']) if c['tool'] == 'meta_ads.publish']
    assert len(blocked) == 1 and blocked[0]['allowed'] == 0 and blocked[0]['permission'] == 'WRITE_EXTERNAL'
    assert body['engines']['audit']['status'] == 'FAIL' and 'blocked_action' in rules(body, 'audit')
    assert by_key(body)['campaign']['artifact']['status'] == 'DRAFT'


def test_s4_agent_timeout_monitor_logs_keeps_old_results_and_retries_that_agent(http):
    body = run(http, inject=['timeout:market'])
    t, rid = by_key(body), body['run']['run_id']
    assert t['market']['status'] == 'FAILED' and t['market']['error'].startswith('timeout')
    assert body['engines']['monitor']['status'] == 'FAIL' and 'timeout' in rules(body, 'monitor')
    plan_artifact = t['plan']['artifact_id']
    r = http.post(f'/runs/{rid}/tasks/market/retry?wait=true')
    assert r.status_code == 202, r.text
    after = by_key(r.json())
    assert r.json()['run']['status'] == 'COMPLETED'
    assert after['market']['attempt'] == 2 and after['plan']['attempt'] == 1
    assert after['plan']['artifact_id'] == plan_artifact                       # old result not lost
    assert r.json()['engines']['monitor']['status'] == 'WARN' and rules(r.json(), 'monitor') == {'retried'}


def test_s5_no_llm_whole_demo_runs_in_mock_mode(http):
    assert http.post('/runs', json={'mode': 'llm'}).status_code == 400            # proves no DeepSeek key here
    body = run(http)
    assert body['run']['mode'] == 'mock' and body['run']['status'] == 'COMPLETED' and body['llm']['calls'] == 0
    assert {x['artifact']['narrative_source'] for x in body['tasks']} == {'mock'}
    assert http.get('/health').json()['live_integrations'] is False


def test_replay_reads_without_running_agents_again(http):
    rid = run(http)['run']['run_id']
    first, second = http.get(f'/runs/{rid}').json(), http.get(f'/runs/{rid}').json()
    assert first == second


def test_dashboard_and_assets_are_served(http):
    html = http.get('/dashboard')
    assert html.status_code == 200 and '/static/vendor/three.module.min.js' in html.text
    assert http.get('/static/vendor/three.module.min.js').status_code == 200
