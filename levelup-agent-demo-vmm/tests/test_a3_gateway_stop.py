"""A3: gateway safe on re-run (attempt + action_hash, reuse without a second approval, Audit sees only the
current attempt), emergency stop blocks dispatch, personal tokens decide who may approve / stop / resume."""
import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app import agents, auth, db
from app.core import workflow as wf
from app.main import app

OWNER_TOK, AN_TOK, BINH_TOK = 'owner-token-0123456789', 'an-token-0123456789', 'binh-token-0123456789'


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setattr(wf, 'DEFAULT_HANDLER', None)
    monkeypatch.delenv('APPROVAL_THRESHOLD_PHP', raising=False)
    monkeypatch.setenv('AUTH_OWNER', f'jarvis:{OWNER_TOK}')
    monkeypatch.setenv('AUTH_DELEGATES', f'an:{AN_TOK},binh:{BINH_TOK}')
    monkeypatch.setenv('STOP_POLL_S', '0.01')
    wf.HANDLERS.clear()
    db.set_stop(False, actor='test-setup')
    yield
    wf.HANDLERS.clear()
    db.set_stop(False, actor='test-teardown')  # the stop is global: never leak it into other tests


def bearer(tok):
    return {'Authorization': f'Bearer {tok}'}


async def run(client, **body):
    return (await client.post('/runs?wait=true', json=body)).json()


async def retry(client, rid, key):
    return (await client.post(f'/runs/{rid}/tasks/{key}/retry?wait=true')).json()


async def tool_rows(client, rid, key=None):
    log = (await client.get(f'/runs/{rid}/decision-log')).json()
    return [{**r, 'detail': json.loads(r['detail'])} for r in log
            if r['action'] == 'tool_call' and (key is None or r['task_key'] == key)]


def rules(body, engine):
    return {f['rule'] for f in body['engines'][engine]['findings']}


# ---- gateway: attempt, action_hash, reuse -------------------------------------------------------------

async def test_happy_path_still_8_tool_calls_all_attempt_1_with_hash(client):
    body = await run(client)
    rows = await tool_rows(client, body['run']['run_id'])
    assert len(rows) == 8
    assert all(r['detail']['attempt'] == 1 and len(r['detail']['action_hash']) == 64 for r in rows)
    assert not any(r['detail'].get('reused') for r in rows)


async def test_rerun_same_action_reuses_result_with_one_approval(client, monkeypatch):
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')
    body = await run(client, inject=['missing_field:campaign'])  # gateway is called, then the artifact fails
    rid = body['run']['run_id']
    assert body['run']['status'] == 'FAILED'
    [appr] = body['approvals']
    assert appr['tool'] == 'meta_ads.create_draft' and appr['status'] == 'PENDING'

    after = await retry(client, rid, 'campaign')
    assert len(after['approvals']) == 1                      # no second approval for the same action
    first, second = await tool_rows(client, rid, 'campaign')
    assert second['detail']['reused'] is True and second['detail']['attempt'] == 2
    for f in ('decision', 'target', 'reason', 'result', 'action_hash'):
        assert second['detail'][f] == first['detail'][f]    # full copy of the original detail
    assert second['detail']['result']['approval_id'] == appr['id']
    campaign = {t['task_key']: t for t in after['tasks']}['campaign']
    assert campaign['status'] == 'COMPLETED' and campaign['attempt'] == 2
    # Regression (retry): the Audit of the re-run still sees the current attempt's call
    assert 'not_via_gateway' not in rules(after, 'audit') and 'pending_approval' in rules(after, 'audit')


async def test_verdict_crossing_the_threshold_on_rerun_creates_a_new_approval(client, monkeypatch):
    body = await run(client, inject=['missing_field:campaign'])  # threshold 5000 > budget 4000: ALLOW
    rid = body['run']['run_id']
    assert body['approvals'] == []
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')          # same action, new verdict: HITL not skipped
    after = await retry(client, rid, 'campaign')
    [appr] = after['approvals']
    assert appr['status'] == 'PENDING'
    first, second = await tool_rows(client, rid, 'campaign')
    assert first['detail']['decision'] == 'ALLOW' and second['detail']['decision'] == 'NEEDS_APPROVAL'
    assert 'reused' not in second['detail']


async def test_audit_on_attempt_2_no_longer_sees_the_block_of_attempt_1(client, monkeypatch):
    real = agents.compute

    def publish_on_first_attempt_only(ctx, run_artifacts=None):
        art = real(ctx, run_artifacts)
        if ctx.task_key == 'campaign' and ctx.attempt == 1:
            art['requested_actions'].append({'tool': 'meta_ads.publish', 'target': art['campaign_id']})
        return art
    monkeypatch.setattr(agents, 'compute', publish_on_first_attempt_only)

    body = await run(client, inject=['missing_field:campaign'])
    rid = body['run']['run_id']
    assert 'blocked_action' in rules(body, 'audit')
    after = await retry(client, rid, 'campaign')
    assert 'blocked_action' not in rules(after, 'audit') and 'not_via_gateway' not in rules(after, 'audit')
    assert after['engines']['audit']['status'] == 'PASS'
    decisions = [r['detail']['decision'] for r in await tool_rows(client, rid, 'campaign')]
    assert decisions == ['ALLOW', 'BLOCK', 'ALLOW']           # history keeps the BLOCK; only the Audit filters it
    assert [c['detail']['attempt'] for c in wf.tool_calls(rid) if c['task_key'] == 'campaign'] == [2]


# ---- emergency stop -------------------------------------------------------------------------------------

async def test_stop_needs_a_token_and_resume_is_owner_only(client):
    assert (await client.post('/admin/stop', json={})).status_code == 401
    assert (await client.post('/admin/stop', json={}, headers=bearer('wrong-token-0123456789'))).status_code == 401
    assert (await client.post('/admin/stop', json={}, headers={'Authorization': AN_TOK})).status_code == 401
    r = await client.post('/admin/stop', json={'reason': 'kiểm tra'}, headers=bearer(AN_TOK))
    assert r.status_code == 200 and r.json()['stopped'] is True and r.json()['actor'] == 'an'
    assert (await client.post('/admin/resume', json={}, headers=bearer(BINH_TOK))).status_code == 403
    assert (await client.get('/admin/stop')).json()['stopped'] is True
    r = await client.post('/admin/resume', json={}, headers=bearer(OWNER_TOK))
    assert r.status_code == 200 and r.json()['stopped'] is False and r.json()['actor'] == 'jarvis'


async def test_new_run_is_refused_with_409_while_stopped(client):
    db.set_stop(True, actor='an')
    before = len(wf.list_runs(200))
    r = await client.post('/runs', json={})
    assert r.status_code == 409 and 'emergency stop' in r.json()['detail']
    assert len(wf.list_runs(200)) == before


async def test_running_run_dispatches_nothing_while_stopped_then_carries_on(client):
    rid = wf.create_run('dừng khẩn giữa chừng')
    db.set_stop(True, actor='an')
    task = asyncio.create_task(wf.execute(rid))
    await asyncio.sleep(0.2)
    body = wf.get_run(rid)
    assert body['run']['status'] == 'RUNNING' and not task.done()
    assert {t['status'] for t in body['tasks']} == {'PENDING'}
    db.set_stop(False, actor='jarvis')
    await asyncio.wait_for(task, 10)
    assert wf.get_run(rid)['run']['status'] == 'COMPLETED'
    actions = [r['action'] for r in wf.table(rid, 'decision_log')]
    assert actions.count('dispatch_paused') == 1 and actions.count('dispatch_resumed') == 1
    assert actions.index('dispatch_resumed') < actions.index('dispatch')


async def test_cancel_works_while_paused(client):
    rid = wf.create_run('hủy khi đang dừng')
    db.set_stop(True, actor='an')
    task = asyncio.create_task(wf.execute(rid))
    await asyncio.sleep(0.1)
    wf.cancel(rid)
    await asyncio.wait_for(task, 5)
    assert wf.get_run(rid)['run']['status'] == 'CANCELLED'


# ---- approvals: who decides ----------------------------------------------------------------------------

async def test_first_decision_wins_and_decided_by_comes_from_the_token(client, monkeypatch):
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')
    body = await run(client)
    rid, [appr] = body['run']['run_id'], body['approvals']
    url = f'/runs/{rid}/approvals/{appr["id"]}'
    assert (await client.post(url, json={'decision': 'APPROVED'})).status_code == 401
    r = await client.post(url, json={'decision': 'REJECTED'}, headers=bearer(BINH_TOK))
    assert r.status_code == 200 and r.json()['decided_by'] == 'binh'
    assert (await client.post(url, json={'decision': 'APPROVED'}, headers=bearer(OWNER_TOK))).status_code == 409
    [stored] = wf.get_run(rid)['approvals']
    assert stored['status'] == 'REJECTED' and stored['decided_by'] == 'binh'


async def test_tokens_are_never_stored(client, monkeypatch):
    monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', '3000')
    body = await run(client)
    await client.post(f'/runs/{body["run"]["run_id"]}/approvals/{body["approvals"][0]["id"]}',
                      json={'decision': 'APPROVED'}, headers=bearer(AN_TOK))
    await client.post('/admin/stop', json={}, headers=bearer(AN_TOK))
    with db.tx() as c:
        dump = json.dumps([[tuple(r) for r in c.execute(f'SELECT * FROM {t}')]
                           for t in ('approvals', 'decision_log', 'events', 'system_stop', 'system_stop_log')],
                          ensure_ascii=False)
    assert not any(tok in dump for tok in (OWNER_TOK, AN_TOK, BINH_TOK))


# ---- auth config ------------------------------------------------------------------------------------------

def _delegates(n):
    return ','.join(f'p{i}:token-of-person-{i:04d}' for i in range(n))


@pytest.mark.parametrize('env, ok', [
    ({'AUTH_DELEGATES': _delegates(3)}, True),
    ({'AUTH_DELEGATES': _delegates(4)}, False),                               # over the limit of 3
    ({'AUTH_DELEGATES': _delegates(4), 'AUTH_MAX_DELEGATES': '4'}, True),     # limit raised by config only
    ({'AUTH_DELEGATES': 'an:short'}, False),                                  # token too short
    ({'AUTH_DELEGATES': 'an'}, False),                                        # no token
    ({'AUTH_DELEGATES': f'an:{OWNER_TOK}'}, False),                           # token shared with the owner
    ({'AUTH_DELEGATES': 'an:token-of-person-0001,an:token-of-person-0002'}, False),  # duplicate name
    ({'AUTH_OWNER': 'a:token-of-person-0001,b:token-of-person-0002'}, False),  # two owners
    ({'AUTH_OWNER': '', 'AUTH_DELEGATES': ''}, True),                         # nobody configured: secure default
], ids=['3-delegates', '4-over-limit', '4-limit-raised', 'short-token', 'no-token', 'shared-token',
        'duplicate-name', 'two-owners', 'empty'])
def test_auth_config(monkeypatch, env, ok):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    if ok:
        auth.actors()
    else:
        with pytest.raises(auth.AuthConfigError) as exc:
            auth.actors()
        assert OWNER_TOK not in str(exc.value) and 'token-of-person' not in str(exc.value)


async def test_nobody_configured_means_nobody_can_act(client, monkeypatch):
    monkeypatch.setenv('AUTH_OWNER', '')
    monkeypatch.setenv('AUTH_DELEGATES', '')
    assert (await client.post('/admin/stop', json={}, headers=bearer(OWNER_TOK))).status_code == 401
