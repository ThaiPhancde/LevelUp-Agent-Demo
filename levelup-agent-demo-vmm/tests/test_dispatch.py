"""A1: dispatch/dispatch_result decision-log entries (giao việc có lý do) and input-source tracking."""
import pytest
from httpx import ASGITransport, AsyncClient

from app import db
from app.core import graph as g
from app.core import workflow as wf
from app.main import app
from app.mock import data


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def clean_handlers(monkeypatch):
    monkeypatch.setattr(wf, 'DEFAULT_HANDLER', wf.placeholder)
    wf.HANDLERS.clear()
    yield
    wf.HANDLERS.clear()


async def test_happy_path_logs_14_dispatch_and_14_dispatch_result(client):
    body = (await client.post('/runs?wait=true', json={})).json()
    assert body['run']['status'] == 'COMPLETED'
    log = (await client.get(f"/runs/{body['run']['run_id']}/decision-log")).json()
    dispatches = [r for r in log if r['action'] == 'dispatch']
    results = [r for r in log if r['action'] == 'dispatch_result']
    assert len(dispatches) == 14
    assert len(results) == 14
    assert [r['task_key'] for r in dispatches] == g.topo_order(g.GRAPH)  # dispatched dependency-first
    assert all(r['detail'] for r in dispatches)  # reason always recorded (non-empty JSON)


async def test_dispatch_reason_never_empty_and_outcome_done(client):
    body = (await client.post('/runs?wait=true', json={})).json()
    rid = body['run']['run_id']
    log = (await client.get(f'/runs/{rid}/decision-log')).json()
    import json
    for row in log:
        if row['action'] == 'dispatch':
            detail = json.loads(row['detail'])
            assert detail['reason']
            assert detail['attempt'] == 1
        if row['action'] == 'dispatch_result':
            detail = json.loads(row['detail'])
            assert detail['outcome'] == 'done'


async def test_last_dispatch_links_task_to_its_reason(client):
    body = (await client.post('/runs?wait=true', json={})).json()
    for t in body['tasks']:
        assert t['last_dispatch'] is not None
        assert t['last_dispatch']['reason']


async def test_interrupted_task_logs_dispatch_result_interrupted(client):
    rid = wf.create_run('restart test for dispatch_result')
    with db.tx() as c:
        c.execute("UPDATE runs SET status='RUNNING' WHERE run_id=?", (rid,))
        c.execute("UPDATE tasks SET status='RUNNING', attempt=1 WHERE run_id=? AND task_key='plan'", (rid,))
    assert rid not in wf.recover()
    import json
    log = wf.table(rid, 'decision_log')
    hit = [json.loads(r['detail']) for r in log if r['action'] == 'dispatch_result' and r['task_key'] == 'plan']
    assert hit and hit[0]['outcome'] == 'interrupted' and hit[0]['attempt'] == 1


async def test_dispatch_reason_mentions_retry_on_attempt_2(client):
    def boom(ctx):
        raise RuntimeError('boom')
    wf.HANDLERS['market'] = boom
    body = (await client.post('/runs?wait=true', json={})).json()
    rid = body['run']['run_id']
    assert body['run']['status'] == 'FAILED'
    wf.HANDLERS.clear()
    after = (await client.post(f'/runs/{rid}/tasks/market/retry?wait=true')).json()
    assert after['run']['status'] == 'COMPLETED'
    import json
    log = (await client.get(f'/runs/{rid}/decision-log')).json()
    retries = [json.loads(r['detail']) for r in log if r['action'] == 'dispatch' and r['task_key'] == 'market' and
               json.loads(r['detail'])['attempt'] == 2]
    assert retries
    assert 'thử' in retries[0]['reason'].lower()


def test_input_sources_default_objective_all_fixture():
    result = data.input_sources_for(None)
    assert result['sources'] == {'market': 'fixture', 'product': 'fixture', 'price': 'fixture', 'budget': 'fixture'}
    assert result['needs_review'] == []
    assert result['currency_note'] is None
    assert data.input_sources_for('') == result
    default_obj = 'Phân tích thị trường Philippines, chọn sản phẩm tiềm năng và lập chiến dịch bán hàng giả lập.'
    assert data.input_sources_for(default_obj) == result


def test_input_sources_custom_market_flags_php_currency_note():
    obj = 'Đề xuất bán thử sản phẩm bình giữ nhiệt tại Thái Lan, giá bán 450, ngân sách quảng cáo 5000.'
    result = data.input_sources_for(obj)
    assert result['sources']['market'] == 'extracted'
    assert result['sources']['product'] == 'extracted'
    assert result['sources']['price'] == 'extracted'
    assert result['sources']['budget'] == 'extracted'
    assert result['needs_review'] == []
    assert result['currency_note'] is not None and 'PHP' in result['currency_note']


def test_input_sources_unmatched_fields_need_review():
    # No market alias, no product/price/budget trigger words or numbers -> everything falls back to a default guess.
    obj = 'Xem xét số liệu vận hành của quý vừa qua để chuẩn bị báo cáo tổng kết gửi lãnh đạo công ty tuần sau.'
    result = data.input_sources_for(obj)
    assert result['sources'] == {'market': 'default', 'product': 'default', 'price': 'default', 'budget': 'default'}
    assert set(result['needs_review']) == {'market', 'product', 'price', 'budget'}
    assert result['currency_note'] is not None  # market defaulted to 'Đông Nam Á', still not Philippines


def test_dispatch_reason_pure_table():
    assert g.dispatch_reason('plan', g.GRAPH, g.SOFT, 1) == 'Không phụ thuộc task nào, sẵn sàng chạy ngay.'
    assert 'hoàn tất' in g.dispatch_reason('market', g.GRAPH, g.SOFT, 1)
    assert 'giám sát' in g.dispatch_reason('qa', g.GRAPH, g.SOFT, 1)
    assert 'thử #3' in g.dispatch_reason('market', g.GRAPH, g.SOFT, 3)
