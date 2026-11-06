"""Phase 4 integration: 13 real agents through the workflow, hand-off evidence, Mock and LLM modes."""
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app import db
from app.core import artifacts, registry
from app.core import workflow as wf
from app.core.graph import GRAPH, TASKS
from app.llm import deepseek
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def real_agents(monkeypatch):
    monkeypatch.setattr(wf, 'DEFAULT_HANDLER', None)
    wf.HANDLERS.clear()
    yield
    wf.HANDLERS.clear()


async def run(client, **body):
    return (await client.post('/runs?wait=true', json=body)).json()


def arts(body):
    return {t['task_key']: t['artifact'] for t in body['tasks']}


async def test_registry_has_13_roles_with_distinct_outputs(client):
    agents = (await client.get('/agents')).json()
    assert len(agents) == 13 and {a['id'] for a in agents} == {f'{i:02d}' for i in range(1, 14)}
    outputs = [o for a in agents for o in a['outputs']]
    assert len(outputs) == len(set(outputs)) == 14  # Commander owns plan + summary
    assert not any(registry.WRITE_EXTERNAL in a['permissions'] for a in agents)
    assert sorted(t for a in agents for t in a['tasks']) == sorted(TASKS)


async def test_mock_run_produces_13_role_specific_valid_artifacts(client):
    body = await run(client)
    a = arts(body)
    assert body['run']['status'] == 'COMPLETED' and body['llm']['calls'] == 0
    assert len({x['type'] for x in a.values()}) == 14
    for key, art in a.items():
        assert artifacts.validate(art) == [], key
        assert art['agent_id'] == TASKS[key][0]
        assert art['narrative'] and art['narrative_source'] == 'mock'
    assert len({x['narrative'] for x in a.values()}) == 14  # not 13 copies of one text


async def test_numbers_flow_between_agents_and_match_fixtures(client):
    a = arts(await run(client))
    assert a['product']['selected_sku'] == a['offer']['sku'] == a['campaign']['sku'] == a['kpi']['sku'] == 'LU-PH-001'
    o, k, f = a['offer'], a['kpi'], a['finance']
    assert (o['margin_per_unit_php'], o['breakeven_orders']) == (226, 18)       # 499-180-75-18 ; ceil(4000/226)
    assert a['campaign']['budget_php'] == o['campaign_budget_php'] == 4000 and a['campaign']['status'] == 'DRAFT'
    assert (k['net_units'], k['net_revenue_php'], k['roas']) == (13, 6487, 1.62)
    assert f['contribution_after_ads_php'] == 13 * 226 - 4000 == -1062
    assert f['margin_per_unit_php'] == o['margin_per_unit_php'] and f['risk_level'] == 'HIGH'
    s = a['summary']
    assert s['key_numbers']['roas'] == k['roas'] and s['key_numbers']['breakeven_orders'] == o['breakeven_orders']
    assert s['decision'] == 'HOLD_DRAFT' and set(s['supervision'].values()) == {'PASS'}


async def test_handoff_trace_in_decision_log(client):
    body = await run(client)
    log = (await client.get(f"/runs/{body['run']['run_id']}/decision-log")).json()
    done = {r['task_key']: json.loads(r['detail'])['inputs_from'] for r in log if r['action'] == 'task_completed'}
    assert all(done[k] == sorted(deps) for k, deps in GRAPH.items())
    assert all(r['input_hash'] for r in log if r['action'] == 'task_completed')


async def test_bad_cost_propagates_instead_of_being_hidden(client):
    a = arts(await run(client, inject=['bad_cost']))
    assert a['product']['selected_sku'] == 'LU-PH-001' and a['product']['warnings']
    assert a['offer']['unit_cost_php'] == 9999 and a['offer']['margin_per_unit_php'] < 0 and a['offer']['breakeven_orders'] == 0
    assert a['finance']['risk_level'] == 'HIGH'


async def test_invalid_artifact_is_rejected_and_kept_as_evidence(client):
    from app import agents

    async def broken(ctx):
        art = await agents.handle(ctx)
        del art['roas']
        return art
    wf.HANDLERS['kpi'] = broken
    body = await run(client)
    kpi = next(t for t in body['tasks'] if t['task_key'] == 'kpi')
    assert kpi['status'] == 'FAILED' and 'roas' in kpi['error']
    with db.tx() as c:
        row = c.execute("SELECT valid, validation_errors FROM artifacts WHERE run_id=? AND task_key='kpi'",
                        (body['run']['run_id'],)).fetchone()
    assert row['valid'] == 0 and 'roas' in row['validation_errors']


def fake_llm(tokens=50, text='Diễn giải giả lập.'):
    async def complete(role, objective, facts, prior, *, run_id=None, task_id=None, **kw):
        deepseek._log_call(run_id, task_id, {'model': 'fake', 'usage': {'prompt_tokens': tokens, 'completion_tokens': 0}},
                           1, 'COMPLETED' if text else 'ERROR', 'stop')
        if not text:
            raise deepseek.LLMEmptyError('Empty model response (finish_reason=stop)')
        return f'{text} [{task_id}] số {facts.get("type")}'
    return complete


async def test_llm_mode_narrates_each_agent_without_changing_numbers(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test')
    monkeypatch.setattr(deepseek, 'complete', fake_llm())
    body = await run(client, mode='llm')
    a = arts(body)
    assert body['run']['status'] == 'COMPLETED' and body['llm']['calls'] == 14
    assert {x['narrative_source'] for x in a.values()} == {'llm'}
    assert a['offer']['margin_per_unit_php'] == 226  # numbers stay Python's


async def test_token_budget_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test')
    monkeypatch.setenv('LLM_RUN_TOKEN_BUDGET', '120')
    monkeypatch.setattr(deepseek, 'complete', fake_llm(tokens=50))
    body = await run(client, mode='llm')
    src = [arts(body)[k]['narrative_source'] for k in TASKS]
    assert body['run']['status'] == 'COMPLETED'
    assert src[:3] == ['llm', 'llm', 'llm'] and set(src[3:]) == {'mock_budget'} and body['llm']['calls'] == 3


async def test_empty_llm_response_fails_the_task(client, monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test')
    monkeypatch.setattr(deepseek, 'complete', fake_llm(text=''))
    body = await run(client, mode='llm')
    plan = next(t for t in body['tasks'] if t['task_key'] == 'plan')
    assert plan['status'] == 'FAILED' and 'Empty model response' in plan['error']
    assert body['run']['status'] == 'FAILED'


async def test_legacy_demo_run_wraps_workflow(client):
    body = (await client.post('/demo/run', json={'inject_error': True})).json()
    assert body['status'] == 'COMPLETED' and len(body['outputs']) == 14
    assert body['business_margin_before_ads_php'] < 0 and all(o['output'] for o in body['outputs'])
