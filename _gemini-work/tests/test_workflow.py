"""Phase 3 integration: Commander graph, hand-off, failure/skip, retry, timeout, cancel, recovery, replay."""
import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app import db
from app.core import graph as g
from app.core import workflow as wf
from app.main import app


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def clean_handlers(monkeypatch):
    monkeypatch.setattr(wf, 'DEFAULT_HANDLER', wf.placeholder)  # engine tests: placeholder agents
    wf.HANDLERS.clear()
    yield
    wf.HANDLERS.clear()


def statuses(body):
    return {t['task_key']: t['status'] for t in body['tasks']}


async def test_happy_path_runs_all_tasks_in_dependency_order_with_handoff(client):
    body = (await client.post('/runs?wait=true', json={})).json()
    assert body['run']['status'] == 'COMPLETED' and body['run']['mode'] == 'mock'
    assert set(statuses(body).values()) == {'COMPLETED'} and len(body['tasks']) == 14
    arts = {t['task_key']: t['artifact'] for t in body['tasks']}
    for key, deps in g.GRAPH.items():
        assert set(arts[key]['received_from']) == set(deps)  # each agent read exactly its upstream artifacts
    assert arts['summary']['chain_depth'] == 13  # longest path: plan…kpi→finance→qa→monitor→summary
    log = (await client.get(f"/runs/{body['run']['run_id']}/decision-log")).json()
    done = [r['task_key'] for r in log if r['action'] == 'task_completed']
    assert done == g.topo_order(g.GRAPH)


async def test_failed_agent_skips_downstream_and_retry_keeps_earlier_results(client):
    def boom(ctx):
        raise RuntimeError('boom')
    wf.HANDLERS['kpi'] = boom
    body = (await client.post('/runs?wait=true', json={})).json()
    st = statuses(body)
    rid = body['run']['run_id']
    assert body['run']['status'] == 'FAILED'
    assert st['kpi'] == 'FAILED' and 'boom' in next(t['error'] for t in body['tasks'] if t['task_key'] == 'kpi')
    assert {k for k, v in st.items() if v == 'SKIPPED'} == {'finance'}
    # soft tasks still report on a failed run (DEMO_ONLY P5: Monitor must see the failure)
    assert all(st[k] == 'COMPLETED' for k in g.SOFT)
    before = {t['task_key']: t['artifact_id'] for t in body['tasks']
              if t['status'] == 'COMPLETED' and t['task_key'] not in g.SOFT}

    wf.HANDLERS.clear()
    after = (await client.post(f'/runs/{rid}/tasks/kpi/retry?wait=true')).json()
    assert after['run']['status'] == 'COMPLETED'
    for t in after['tasks']:
        if t['task_key'] in before:
            assert t['artifact_id'] == before[t['task_key']]  # old business results not recomputed or lost
    assert all(t['attempt'] == 2 for t in after['tasks'] if t['task_key'] in g.SOFT)  # supervisors re-ran
    kpi = next(t for t in after['tasks'] if t['task_key'] == 'kpi')
    assert kpi['attempt'] == 2


async def test_timeout_marks_task_failed(client, monkeypatch):
    monkeypatch.setenv('TASK_TIMEOUT_S', '0.05')

    async def slow(ctx):
        await asyncio.sleep(1)
    wf.HANDLERS['market'] = slow
    body = (await client.post('/runs?wait=true', json={})).json()
    market = next(t for t in body['tasks'] if t['task_key'] == 'market')
    assert market['status'] == 'FAILED' and market['error'].startswith('timeout')


@pytest.mark.parametrize('bad', [lambda ctx: None, lambda ctx: {'no_type': 1}, lambda ctx: ''], ids=['none', 'no-type', 'empty'])
async def test_agent_without_artifact_is_failed_not_success(client, bad):
    wf.HANDLERS['offer'] = bad
    body = (await client.post('/runs?wait=true', json={})).json()
    assert statuses(body)['offer'] == 'FAILED'


async def test_cancel_while_running_stops_remaining_tasks(client):
    gate = asyncio.Event()
    started = asyncio.Event()

    async def blocking(ctx):
        started.set()
        await gate.wait()
        return wf.placeholder(ctx)
    wf.HANDLERS['market'] = blocking
    rid = (await client.post('/runs', json={})).json()['run_id']
    await asyncio.wait_for(started.wait(), 5)
    assert (await client.post(f'/runs/{rid}/cancel')).json()['status'] == 'CANCELLED'
    gate.set()
    for _ in range(100):
        body = (await client.get(f'/runs/{rid}')).json()
        if body['run']['finished_at']:
            break
        await asyncio.sleep(0.02)
    st = statuses(body)
    assert body['run']['status'] == 'CANCELLED'
    assert st['plan'] == 'COMPLETED' and st['market'] == 'COMPLETED'  # in-flight task allowed to finish
    assert all(st[k] == 'CANCELLED' for k in g.TASKS if k not in ('plan', 'market'))
    assert (await client.post(f'/runs/{rid}/cancel')).status_code == 409


async def test_restart_recovery_marks_interrupted_and_retry_finishes(client):
    rid = wf.create_run('restart test')
    with db.tx() as c:  # simulate a crash: plan done, market was running
        c.execute("UPDATE runs SET status='RUNNING' WHERE run_id=?", (rid,))
        c.execute("UPDATE tasks SET status='RUNNING' WHERE run_id=? AND task_key='market'", (rid,))
        c.execute("INSERT INTO artifacts(run_id,task_key,agent_id,type,attempt,payload,created_at) "
                  "VALUES (?, 'plan', '01', 'plan_placeholder', 1, '{\"type\":\"plan_placeholder\",\"chain_depth\":1}', 'x')", (rid,))
        art = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        c.execute("UPDATE tasks SET status='COMPLETED', artifact_id=? WHERE run_id=? AND task_key='plan'", (art, rid))
    assert rid not in wf.recover()
    body = wf.get_run(rid)
    market = next(t for t in body['tasks'] if t['task_key'] == 'market')
    assert body['run']['status'] == 'FAILED' and market['error'].startswith('interrupted')
    after = (await client.post(f'/runs/{rid}/tasks/market/retry?wait=true')).json()
    assert after['run']['status'] == 'COMPLETED'


async def test_recovery_resumes_run_stopped_between_tasks():
    rid = wf.create_run('resume test')
    with db.tx() as c:
        c.execute("UPDATE runs SET status='RUNNING' WHERE run_id=?", (rid,))
    assert rid in wf.recover()
    await wf.execute(rid)
    assert wf.get_run(rid)['run']['status'] == 'COMPLETED'


async def test_replay_is_read_only_and_does_not_call_llm(client):
    rid = (await client.post('/runs?wait=true', json={})).json()['run']['run_id']
    with db.tx() as c:
        before = (c.execute('SELECT COUNT(*) FROM llm_calls').fetchone()[0],
                  c.execute('SELECT COUNT(*) FROM artifacts WHERE run_id=?', (rid,)).fetchone()[0])
    first = (await client.get(f'/runs/{rid}')).json()
    second = (await client.get(f'/runs/{rid}')).json()
    with db.tx() as c:
        after = (c.execute('SELECT COUNT(*) FROM llm_calls').fetchone()[0],
                 c.execute('SELECT COUNT(*) FROM artifacts WHERE run_id=?', (rid,)).fetchone()[0])
    assert first == second and before == after and first['llm']['calls'] == 0


async def test_bad_cost_injection_reaches_agent_facts_only_for_that_run(client):
    seen = {}

    def capture(ctx):
        seen[ctx.run_id] = next(s['unit_cost_php'] for s in ctx.facts['suppliers']['items'] if s['sku'] == 'LU-PH-001')
        return wf.placeholder(ctx)
    wf.HANDLERS['product'] = capture
    bad = (await client.post('/runs?wait=true', json={'inject': ['bad_cost']})).json()['run']['run_id']
    good = (await client.post('/runs?wait=true', json={})).json()['run']['run_id']
    assert seen == {bad: 9999, good: 180}


@pytest.mark.parametrize('path,payload,code', [
    ('/runs', {'inject': ['drop_tables']}, 422),
    ('/runs', {'inject': ['timeout:nobody']}, 422),
    ('/runs', {'mode': 'paid'}, 422),
    ('/runs', {'objective': ''}, 422),
    ('/runs', {'mode': 'llm'}, 400),
], ids=['unknown-inject', 'unknown-task', 'bad-mode', 'empty-objective', 'llm-without-key'])
async def test_create_run_validation(client, path, payload, code):
    assert (await client.post(path, json=payload)).status_code == code


async def test_retry_and_lookup_errors(client):
    rid = (await client.post('/runs?wait=true', json={})).json()['run']['run_id']
    assert (await client.get('/runs/nope')).status_code == 404
    assert (await client.post(f'/runs/{rid}/tasks/kpi/retry')).status_code == 409  # run COMPLETED
    assert (await client.post(f'/runs/{rid}/tasks/ghost/retry')).status_code == 404
    assert (await client.post(f'/runs/{rid}/cancel')).status_code == 409
    listed = (await client.get('/runs')).json()
    assert any(r['run_id'] == rid for r in listed)


async def test_executor_cancelled_on_shutdown_leaves_retryable_task(client):
    """Regression (found by the Phase 8 restart E2E): uvicorn cancels the background executor on shutdown.
    The task that was RUNNING must end FAILED 'interrupted', never stuck RUNNING, and retry must finish the run."""
    started = asyncio.Event()

    async def hang(ctx):
        started.set()
        await asyncio.sleep(3600)
    wf.HANDLERS['market'] = hang
    rid = wf.create_run('shutdown test')
    runner = asyncio.get_running_loop().create_task(wf.execute(rid))
    await asyncio.wait_for(started.wait(), 5)
    runner.cancel()
    with pytest.raises(asyncio.CancelledError):
        await runner
    body = wf.get_run(rid)
    market = next(t for t in body['tasks'] if t['task_key'] == 'market')
    assert market['status'] == 'FAILED' and market['error'].startswith('interrupted')
    assert body['run']['status'] == 'FAILED'
    wf.HANDLERS.clear()
    after = (await client.post(f'/runs/{rid}/tasks/market/retry?wait=true')).json()
    assert after['run']['status'] == 'COMPLETED'


async def test_recover_fixes_running_task_under_a_finished_run():
    rid = wf.create_run('orphan test')
    with db.tx() as c:
        c.execute("UPDATE runs SET status='FAILED' WHERE run_id=?", (rid,))
        c.execute("UPDATE tasks SET status='RUNNING' WHERE run_id=? AND task_key='plan'", (rid,))
    assert rid not in wf.recover()
    plan = next(t for t in wf.get_run(rid)['tasks'] if t['task_key'] == 'plan')
    assert plan['status'] == 'FAILED' and plan['error'].startswith('interrupted')


async def test_runs_expose_friendly_number_and_scenario(client):
    first = (await client.post('/runs?wait=true', json={})).json()['run']
    second = (await client.post('/runs?wait=true', json={'inject': ['bad_cost']})).json()['run']
    assert isinstance(first['seq'], int) and second['seq'] == first['seq'] + 1
    listed = {r['run_id']: r for r in (await client.get('/runs')).json()}
    assert listed[second['run_id']]['inject'] == ['bad_cost'] and listed[second['run_id']]['seq'] == second['seq']
    assert listed[first['run_id']]['inject'] == []
