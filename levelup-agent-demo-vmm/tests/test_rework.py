"""A4: rework loop (DEMO_PLAN_OPTION_A 7.2, S6). The Commander sends work back once QA/Audit are done and
before the Monitor runs; only checks.FIX decides what is fixed; max_rework=0 keeps every old behaviour."""
import json
from collections import Counter

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents import checks as fixes
from app.core import workflow as wf
from app.engines import monitor
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
    r = await client.post('/runs?wait=true', json=body)
    assert r.status_code == 202, r.text[:300]
    return r.json()


def by_key(body):
    return {t['task_key']: t for t in body['tasks']}


def rules(body, engine):
    return {f['rule'] for f in body['engines'][engine]['findings']}


def log(rid, action=None):
    rows = [{**r, 'detail': json.loads(r['detail'] or '{}')} for r in wf.table(rid, 'decision_log')]
    return [r for r in rows if action is None or r['action'] == action]


def engine_history(rid, engine):
    return [r['detail']['status'] for r in log(rid, 'engine_result') if r['task_key'] == engine]


REWORK_ACTIONS = {'rework_requested', 'rework_resolved', 'rework_skipped', 'check_applied'}


# ---- S6 ---------------------------------------------------------------------------------------------------

async def test_s6_bad_cost_one_rework_of_product_fixes_qa(client):
    body = await run(client, inject=['bad_cost'], max_rework=2)
    rid, t = body['run']['run_id'], by_key(body)
    assert engine_history(rid, 'qa') == ['FAIL', 'PASS']
    [req] = body['rework']['requests']
    assert (req['round'], req['target_task'], req['agent_id'], req['status']) == (1, 'product', '03', 'RESOLVED')
    assert req['checks'] == ['verify_supplier_cost:LU-PH-001']
    assert body['run']['status'] == 'COMPLETED'
    assert t['summary']['artifact']['decision'] == 'HOLD_DRAFT'
    cand = next(c for c in t['product']['artifact']['candidates'] if c['sku'] == 'LU-PH-001')
    assert cand['unit_cost_php'] == 180 and t['offer']['artifact']['unit_cost_php'] == 180
    assert t['product']['artifact']['rework_feedback'][0]['rule'] == 'reference'
    assert 'checks_applied' not in t['product']['artifact']  # split off the payload, logged instead
    assert body['engines']['monitor']['status'] == 'WARN' and rules(body, 'monitor') == {'reworked'}
    [asked] = log(rid, 'rework_requested')
    assert asked['task_key'] == 'product' and asked['agent_id'] == '01' and asked['detail']['rule'] == 'reference'
    assert asked['detail']['changes'] == ['product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi',
                                          'finance', 'qa', 'audit']
    applied = log(rid, 'check_applied')
    assert {a['task_key'] for a in applied if a['detail']['before'] == 9999} >= {'product', 'offer'}
    assert all(a['detail']['after'] == 180 and a['detail']['attempt'] == 2 for a in applied)
    redo = [d for d in log(rid, 'dispatch') if d['detail'].get('rework_round') == 1]
    assert [d['task_key'] for d in redo] == asked['detail']['changes']
    assert all('Làm lại theo yêu cầu của Commander' in d['detail']['reason'] for d in redo)
    assert len(log(rid, 'rework_resolved')) == 1 and not log(rid, 'rework_skipped')


async def test_s6_default_run_has_14_dispatch_with_reason(client):
    body = await run(client)
    rows = log(body['run']['run_id'], 'dispatch')
    assert len(rows) == 14 and all(r['detail']['reason'] for r in rows)


async def test_s6_publish_attempt_campaign_drops_blocked_publish(client):
    body = await run(client, inject=['publish_attempt'], max_rework=2)
    rid, t = body['run']['run_id'], by_key(body)
    assert engine_history(rid, 'audit') == ['FAIL', 'PASS']
    assert body['engines']['audit']['status'] == 'PASS'
    assert [a['tool'] for a in t['campaign']['artifact']['requested_actions']] == ['meta_ads.create_draft']
    assert t['campaign']['artifact']['status'] == 'DRAFT'
    tools = [(r['tool'], r['detail']['decision']) for r in log(rid, 'tool_call') if r['task_key'] == 'campaign']
    assert ('meta_ads.publish', 'BLOCK') in tools  # the blocked attempt stays in the history
    [drop] = log(rid, 'check_applied')  # only the task that was blocked gets the artifact-level check
    assert drop['task_key'] == 'campaign' and drop['detail']['check'] == 'drop_blocked_action:meta_ads.publish'
    assert body['rework']['requests'][0]['status'] == 'RESOLVED'


async def test_s6_missing_field_offer_no_rework_needs_review(client):
    body = await run(client, inject=['missing_field:offer'], max_rework=2)
    rid = body['run']['run_id']
    assert body['run']['status'] == 'FAILED'
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'
    assert body['rework']['requests'] == []
    [skip] = log(rid, 'rework_skipped')
    assert skip['detail'] == {'reason': 'business_task_not_completed', 'rounds_used': 0}


async def test_healthy_run_with_max_rework_has_no_rework_rows(client):
    body = await run(client, max_rework=2)
    rid = body['run']['run_id']
    assert not REWORK_ACTIONS & {r['action'] for r in log(rid)}
    assert body['rework'] == {'requests': [], 'reworked_tasks': [], 'exhausted': False}
    assert body['run']['status'] == 'COMPLETED'


async def test_two_runs_give_the_same_decision_chain(client):
    chains = []
    for _ in range(2):
        body = await run(client, inject=['bad_cost', 'publish_attempt'], max_rework=2)
        chains.append([(r['action'], r['task_key'], r['agent_id']) for r in log(body['run']['run_id'])])
    assert chains[0] == chains[1]


# ---- max_rework=0 keeps the old behaviour ---------------------------------------------------------------------

@pytest.mark.parametrize('inject, engine, rule', [
    (['bad_cost'], 'qa', 'reference'),
    (['publish_attempt'], 'audit', 'blocked_action'),
], ids=['s2-bad-cost', 's3-publish'])
async def test_max_rework_0_is_unchanged(client, inject, engine, rule):
    body = await run(client, inject=inject)
    rid = body['run']['run_id']
    assert body['engines'][engine]['status'] == 'FAIL' and rule in rules(body, engine)
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'
    assert not REWORK_ACTIONS & {r['action'] for r in log(rid)} and body['rework']['requests'] == []


async def test_retry_still_reported_as_retried_not_reworked(client, monkeypatch):
    monkeypatch.setenv('TASK_TIMEOUT_S', '0.2')
    body = await run(client, inject=['timeout:market'], max_rework=2)
    rid = body['run']['run_id']
    assert body['run']['status'] == 'FAILED'
    after = (await client.post(f'/runs/{rid}/tasks/market/retry?wait=true')).json()
    assert after['run']['status'] == 'COMPLETED'
    assert 'retried' in rules(after, 'monitor') and 'reworked' not in rules(after, 'monitor')


@pytest.mark.parametrize('value', [3, -1], ids=['above-ceiling', 'negative'])
async def test_max_rework_out_of_range_is_422(client, value):
    assert (await client.post('/runs', json={'max_rework': value})).status_code == 422


# ---- stopping without a fix ----------------------------------------------------------------------------------

async def test_no_change_stops_the_loop_and_monitor_warns(client, monkeypatch):
    monkeypatch.setattr(fixes, 'apply_facts', lambda facts, checks, ref: (facts, []))  # a fix that fixes nothing
    body = await run(client, inject=['bad_cost'], max_rework=2)
    rid = body['run']['run_id']
    [req] = body['rework']['requests']
    assert req['status'] == 'NO_CHANGE'
    assert [s['detail']['reason'] for s in log(rid, 'rework_skipped')] == ['no_change']
    assert 'rework_exhausted' in rules(body, 'monitor') and body['rework']['exhausted'] is True
    assert by_key(body)['summary']['artifact']['decision'] == 'NEEDS_REVIEW'


async def test_exhausted_when_rounds_run_out(client, monkeypatch):
    real = fixes.apply_facts

    def wrong_quote(facts, checks, ref):  # changes the cost, but still not to the reference
        out, applied = real(facts, checks, ref)
        for s in out['suppliers']['items']:
            if s['sku'] == 'LU-PH-001' and checks:
                s['unit_cost_php'] = 9998
        return out, applied
    monkeypatch.setattr(fixes, 'apply_facts', wrong_quote)
    body = await run(client, inject=['bad_cost'], max_rework=1)
    rid = body['run']['run_id']
    assert [r['status'] for r in body['rework']['requests']] == ['EXHAUSTED']
    assert [s['detail']['reason'] for s in log(rid, 'rework_skipped')] == ['exhausted']
    assert 'rework_exhausted' in rules(body, 'monitor')
    assert engine_history(rid, 'qa') == ['FAIL', 'FAIL']


# ---- LLM budget ---------------------------------------------------------------------------------------------------

async def test_llm_mode_reworked_tasks_use_mock_narrative(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test')

    async def fake(role, objective, facts, prior, *, run_id=None, task_id=None, **kw):
        deepseek._log_call(run_id, task_id, {'model': 'fake', 'usage': {'prompt_tokens': 1, 'completion_tokens': 1}},
                           1, 'COMPLETED', 'stop')
        return 'Diễn giải giả lập, không đổi số.'
    monkeypatch.setattr(deepseek, 'complete', fake)
    body = await run(client, inject=['bad_cost'], mode='llm', max_rework=2)
    rid = body['run']['run_id']
    changes = log(rid, 'rework_requested')[0]['detail']['changes']
    calls = Counter(r['task_id'] for r in wf.table(rid, 'llm_calls'))
    assert all(calls[k] == 1 for k in changes)  # first attempt only; the rework added none
    t = by_key(body)
    assert all(t[k]['artifact']['narrative_source'] == 'mock' for k in changes)


# ---- Monitor rule table (retry + rework in one run) ----------------------------------------------------------

@pytest.mark.parametrize('tasks, rework, expected', [
    ([('market', 2)], {}, {('retried', 'market')}),
    ([('product', 2)], {'reworked_tasks': ['product']}, {('reworked', 'product')}),
    ([('market', 2), ('product', 2)], {'reworked_tasks': ['product']}, {('retried', 'market'), ('reworked', 'product')}),
    ([('product', 1)], {'reworked_tasks': ['product']}, set()),
    ([], {'exhausted': True}, {('rework_exhausted', None)}),
], ids=['retry-only', 'rework-only', 'retry-and-rework', 'attempt-1-not-flagged', 'exhausted'])
def test_monitor_reworked_vs_retried(tasks, rework, expected):
    ev = {'tasks': [{'task_key': k, 'status': 'COMPLETED', 'attempt': a, 'error': None} for k, a in tasks],
          'llm': {}, 'rework': rework}
    found = {(f['rule'], f['task_key']) for f in monitor.run(ev)['findings']}
    assert found == expected
    assert all(f['severity'] == 'WARN' for f in monitor.run(ev)['findings'])


def test_drop_blocked_action_only_goes_to_the_task_that_was_blocked():
    """7.2 step 4: drop_blocked_action:<tool> reaches ctx.checks only for the (task_key, tool) of a blocked_action
    finding in this run's rework requests; facts-level checks are run-wide."""
    from app import db
    rid = wf.create_run('kiểm phạm vi phép kiểm')
    findings = [{'rule': 'reference', 'severity': 'FAIL', 'task_key': 'product', 'engine': 'qa',
                 'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180'},
                {'rule': 'blocked_action', 'severity': 'FAIL', 'task_key': 'campaign', 'engine': 'audit',
                 'detail': 'meta_ads.publish by agent 06 was blocked'}]
    with db.tx() as c:
        c.execute('INSERT INTO rework_requests(run_id,round,target_task,agent_id,source_result_ids,findings,checks,'
                  "status,created_at) VALUES (?,1,'product','03','[]',?,?,'OPEN',?)",
                  (rid, json.dumps(findings), json.dumps(['drop_blocked_action:meta_ads.publish',
                                                          'verify_supplier_cost:LU-PH-001']), db.now()))
        assert wf._run_checks(c, rid) == (['verify_supplier_cost:LU-PH-001'],
                                          {'campaign': ['drop_blocked_action:meta_ads.publish']})
