"""REST API for Commander runs (Phase 3). Read endpoints are pure replay: no agent, no LLM."""
import os
import re
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core import graph as g
from app.core import workflow as wf

router = APIRouter(tags=['runs'])
_INJECT = re.compile(r'^(bad_cost|publish_attempt|(timeout|missing_field|empty_response):(' + '|'.join(g.TASKS) + r'))$')


class RunRequest(BaseModel):
    objective: str = Field(default='Phân tích thị trường Philippines, chọn sản phẩm tiềm năng và lập chiến dịch bán hàng giả lập.',
                           min_length=1, max_length=600)
    mode: Literal['mock', 'llm', 'deepseek'] = 'mock'
    inject: list[str] = Field(default_factory=list, max_length=10)

    @field_validator('inject')
    @classmethod
    def _known(cls, v):
        bad = [x for x in v if not _INJECT.match(x)]
        if bad:
            raise ValueError(f'unknown injection(s): {bad}')
        return v


def _http(exc: wf.WorkflowError):
    return HTTPException(exc.status, str(exc))


@router.post('/runs', status_code=202)
async def create_run(req: RunRequest, wait: bool = False):
    norm_mode = 'llm' if req.mode in ('llm', 'deepseek') else 'mock'
    key = os.getenv('DEEPSEEK_API_KEY', '')
    if norm_mode == 'llm' and (not key or key == 'PUT_YOUR_KEY_HERE'):
        raise HTTPException(400, 'Missing DEEPSEEK_API_KEY. Use mode="mock" or configure .env.')
    run_id = wf.create_run(req.objective, norm_mode, req.inject)
    if wait:
        await wf.execute(run_id)
        return wf.get_run(run_id)
    wf.spawn(run_id)
    return {'environment': 'MOCK_ONLY', 'run_id': run_id, 'status': 'PENDING'}


@router.get('/runs')
def list_runs(limit: int = 50):
    return wf.list_runs(max(1, min(limit, 200)))


@router.get('/runs/{run_id}')
def get_run(run_id: str):
    try:
        return wf.get_run(run_id)
    except wf.WorkflowError as exc:
        raise _http(exc)


@router.post('/runs/{run_id}/cancel')
def cancel_run(run_id: str):
    try:
        return {'run_id': run_id, 'status': wf.cancel(run_id)}
    except wf.WorkflowError as exc:
        raise _http(exc)


@router.post('/runs/{run_id}/tasks/{task_key}/retry', status_code=202)
async def retry_task(run_id: str, task_key: str, wait: bool = False):
    try:
        wf.retry(run_id, task_key)
    except wf.WorkflowError as exc:
        raise _http(exc)
    if wait:
        await wf.execute(run_id)
        return wf.get_run(run_id)
    wf.spawn(run_id)
    return {'run_id': run_id, 'status': 'PENDING', 'retried': task_key}


class ApprovalRequest(BaseModel):
    decision: Literal['APPROVED', 'REJECTED']


@router.post('/runs/{run_id}/approvals/{approval_id}')
def decide(run_id: str, approval_id: int, req: ApprovalRequest):
    try:
        return {'run_id': run_id, 'approval_id': approval_id,
                'run_status': wf.decide_approval(run_id, approval_id, req.decision)}
    except wf.WorkflowError as exc:
        raise _http(exc)


@router.get('/runs/{run_id}/decision-log')
def decision_log(run_id: str):
    try:
        return wf.table(run_id, 'decision_log')
    except wf.WorkflowError as exc:
        raise _http(exc)


@router.get('/runs/{run_id}/llm-calls')
def llm_calls(run_id: str):
    try:
        return wf.table(run_id, 'llm_calls')
    except wf.WorkflowError as exc:
        raise _http(exc)


class ResetRequest(BaseModel):
    confirm: bool = False
    include_memory: bool = False


@router.post('/admin/reset-demo', tags=['admin'])
def reset_demo(req: ResetRequest):
    """Delete all demo runs, tasks, artifacts and logs (schema kept). Body must be {"confirm": true}.

    include_memory=true also deletes memory_items/learning_proposals — intended for a test database only.
    """
    if not req.confirm:
        raise HTTPException(400, 'Send {"confirm": true} to delete all demo runs. This cannot be undone.')
    try:
        return {'deleted': wf.reset_demo(include_memory=req.include_memory)}
    except wf.WorkflowError as exc:
        raise _http(exc)


class StopRequest(BaseModel):
    reason: str | None = None


@router.get('/admin/stop', tags=['admin'])
def get_stop():
    """Current emergency-stop state (A2: storage only — A3 enforces who may call this and blocks dispatch)."""
    from app import db
    return db.get_stop_state()


@router.post('/admin/stop', tags=['admin'])
def post_stop(req: StopRequest):
    """Set the emergency stop (A2: storage only, no auth/dispatch-blocking yet — that is A3's scope)."""
    from app import db
    return db.set_stop(True, actor='user', reason=req.reason)


@router.post('/admin/resume', tags=['admin'])
def post_resume(req: StopRequest):
    """Clear the emergency stop (A2: storage only — A3 restricts this to Jarvis)."""
    from app import db
    return db.set_stop(False, actor='user', reason=req.reason)
