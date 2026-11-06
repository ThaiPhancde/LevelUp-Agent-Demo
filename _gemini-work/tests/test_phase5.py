"""Phase 5 integration: deterministic engines, Mock Tool Gateway, 5 error injections, Human-in-the-Loop."""
import ast
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app import db
from app.core import workflow as wf
from app.core.graph import SOFT
from app.llm import deepseek
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def real_agents(monkeypatch):
    monkeypatch.setattr(wf, 'DEFAULT_HANDLER', None)
    monkeypatch.delenv('APPROVAL_THRESHOLD_PHP', raising=False)
    wf.HANDLERS.clear()
    yield
    wf.HANDLERS.clear()


async def run(client, **body):
    return (await client.post('/runs?wait=true', json=body)).json()


def by_key(body):
    return {t['task_key']: t for t in body['tasks']}


def rules(body, engine):
    return {f['rule'] for f in body['engines'][engine]['findings']}


async def tool_rows(client, rid):
    log = (await client.get(f'/runs/{rid}/decision-log')).json()
    return [r for r in log if r['action'] == 'tool_call']


async def test_happy_path_all_engines_pass_and_actions_go_through_gateway(client):
    body = await run(client)
    t = by_key(body)
    assert body['run']['status'] == 'COMPLETED'
    assert {e: body['engines'][e]['status'] for e in ('qa', 'audit', 'monitor')} == {'qa': 'PASS', 'audit': 'PASS', 'monitor': 'PASS'}
    calls = await tool_rows(client, body['run']['run_id'])
    assert len(calls) == 8 and all(r['allowed'] == 1 for r in calls)  # 1 campaign draft + 3 reply drafts + 4 ticket notes
    assert {json.loads(r['detail'])['result']['status'] for r in calls} == {'DRAFT'}
    assert t['qa']['artifact']['engine_result_id'] == body['engines']['qa']['id']  # report reads the engine result
    assert t['summary']['artifact']['decision'] == 'HOLD_DRAFT'


async def test_s2_invalid_cost_qa_fails_on_reference_check(client):
    body = await run(client, inject=['bad_cost'])
    qa = body['engines']['qa']
    assert qa['status'] == 'FAIL' and 'reference' in rules(body, 'qa')
    assert any('9999' in f['detail'] and f['task_key'] == 'offer' for f in qa['findings'])
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'


async def test_s3_publish_attempt_is_blocked_by_audit_and_campaign_stays_draft(client):
    body = await run(client, inject=['publish_attempt'])
    rid = body['run']['run_id']
    camp = by_key(body)['campaign']['artifact']
    blocked = [r for r in await tool_rows(client, rid) if r['tool'] == 'meta_ads.publish']
    assert len(blocked) == 1 and blocked[0]['allowed'] == 0 and blocked[0]['permission'] == 'WRITE_EXTERNAL'
    assert json.loads(blocked[0]['detail'])['result']['status'] == 'BLOCKED'
    assert camp['status'] == 'DRAFT'
    assert body['engines']['audit']['status'] == 'FAIL' and 'blocked_action' in rules(body, 'audit')
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'


async def test_s4_timeout_monitor_detects_keeps_old_results_and_retry_fixes_only_that_agent(client, monkeypatch):
    monkeypatch.setenv('TASK_TIMEOUT_S', '0.2')
    body = await run(client, inject=['timeout:market'])
    t, rid = by_key(body), body['run']['run_id']
    assert t['market']['status'] == 'FAILED' and t['market']['error'].startswith('timeout')
    assert body['engines']['monitor']['status'] == 'FAIL' and 'timeout' in rules(body, 'monitor')
    assert all(t[k]['status'] == 'COMPLETED' for k in SOFT)  # supervisors still reported
    plan_artifact = t['plan']['artifact_id']

    after = (await client.post(f'/runs/{rid}/tasks/market/retry?wait=true')).json()
    t2 = by_key(after)
    assert after['run']['status'] == 'COMPLETED'
    assert t2['market']['attempt'] == 2 and t2['plan']['attempt'] == 1 and t2['plan']['artifact_id'] == plan_artifact
    assert after['engines']['monitor']['status'] == 'WARN' and rules(after, 'monitor') == {'retried'}
    assert after['engines']['qa']['status'] == 'PASS'
    assert t2['summary']['artifact']['decision'] == 'HOLD_DRAFT'  # a WARN (retried) does not force a review


async def test_missing_field_is_rejected_and_reported_by_qa_and_monitor(client):
    body = await run(client, inject=['missing_field:kpi'])
    t = by_key(body)
    assert t['kpi']['status'] == 'FAILED' and 'schema' in t['kpi']['error']
    qa = body['engines']['qa']
    assert qa['status'] == 'FAIL' and any(f['task_key'] == 'kpi' and 'rejected' in f['detail'] for f in qa['findings'])
    assert 'task_failed' in rules(body, 'monitor')


async def test_empty_response_fails_task_and_monitor_flags_it(client):
    body = await run(client, inject=['empty_response:offer'])
    t = by_key(body)
    assert t['offer']['status'] == 'FAILED' and 'empty' in t['offer']['error']
    assert 'empty_response' in rules(body, 'monitor') and body['engines']['monitor']['status'] == 'FAIL'


async def test_human_in_the_loop_parks_draft_above_threshold_until_approved(client, monkeypatch):
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')
    body = await run(client)
    rid = body['run']['run_id']
    assert body['run']['status'] == 'WAITING_APPROVAL' and body['run']['finished_at'] is None
    [appr] = body['approvals']
    assert appr['status'] == 'PENDING' and appr['amount'] == 4000
    assert body['engines']['audit']['status'] == 'WARN' and rules(body, 'audit') == {'pending_approval'}
    assert (await client.post(f'/runs/{rid}/approvals/{appr["id"]}', json={'decision': 'MAYBE'})).status_code == 422
    resp = (await client.post(f'/runs/{rid}/approvals/{appr["id"]}', json={'decision': 'APPROVED'})).json()
    assert resp['run_status'] == 'COMPLETED'
    assert (await client.post(f'/runs/{rid}/approvals/{appr["id"]}', json={'decision': 'APPROVED'})).status_code == 409


async def test_engines_are_independent_of_llm_output(client, monkeypatch):
    """Same run in LLM mode with a lying narrator: engine verdicts on the numbers do not move; the made-up
    number only raises a narrative WARN."""
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test')

    async def liar(role, objective, facts, prior, *, run_id=None, task_id=None, **kw):
        deepseek._log_call(run_id, task_id, {'model': 'fake', 'usage': {'prompt_tokens': 1, 'completion_tokens': 1}}, 1, 'COMPLETED', 'stop')
        return 'Lợi nhuận đạt 999999 PHP, rất tốt.'
    monkeypatch.setattr(deepseek, 'complete', liar)
    body = await run(client, mode='llm')
    a = {k: t['artifact'] for k, t in by_key(body).items()}
    assert a['offer']['margin_per_unit_php'] == 226 and a['finance']['contribution_after_ads_php'] == -1062
    assert body['engines']['qa']['status'] == 'WARN' and rules(body, 'qa') == {'narrative'}
    assert body['engines']['audit']['status'] == 'PASS'


def test_engines_do_not_import_llm_or_agents():
    for path in Path('app/engines').glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
               {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not any(m and (m.startswith('app.llm') or m.startswith('app.agents') or m == 'httpx') for m in mods), path


async def test_cancel_while_waiting_for_approval(client, monkeypatch):
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')
    rid = (await run(client))['run']['run_id']
    assert (await client.post(f'/runs/{rid}/cancel')).json()['status'] == 'CANCELLED'
    with db.tx() as c:
        assert c.execute('SELECT status FROM runs WHERE run_id=?', (rid,)).fetchone()[0] == 'CANCELLED'
        assert c.execute("SELECT status FROM approvals WHERE run_id=?", (rid,)).fetchone()[0] == 'REJECTED'


async def test_reset_demo_requires_confirm_and_keeps_schema(client):
    await run(client)
    assert (await client.post('/admin/reset-demo', json={})).status_code == 400
    r = (await client.post('/admin/reset-demo', json={'confirm': True})).json()
    assert r['deleted']['runs'] >= 1 and r['deleted']['tasks'] >= 14
    assert (await client.get('/runs')).json() == []
    assert (await run(client))['run']['status'] == 'COMPLETED'  # schema still works after reset


async def test_reset_demo_refused_while_a_run_is_active(client):
    rid = wf.create_run('active')
    assert (await client.post('/admin/reset-demo', json={'confirm': True})).status_code == 409
    wf.cancel(rid)
