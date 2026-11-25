import os, json
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db
from app.mock import data


@asynccontextmanager
async def lifespan(_app):
    from app import auth
    from app.core import workflow
    auth.actors()  # fail fast on a bad AUTH_* config instead of on the first Approve click
    for run_id in workflow.recover():  # checkpoint: resume runs that had not finished any task yet
        workflow.spawn(run_id)
    yield


app = FastAPI(title="Level Up 13-Agent Sandbox Demo", version="0.2.0", lifespan=lifespan)
MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-v4-flash')
SAMPLE = data.sample()


class DemoRequest(BaseModel):
    objective: str = Field(default='Đề xuất kế hoạch bán thử sản phẩm tại Philippines, không chạy quảng cáo thật.',max_length=600)
    inject_error: bool = False
    use_llm: bool = False

from app.mock.router import router as mock_router
from app.runs_api import router as runs_router
app.include_router(mock_router)
app.include_router(runs_router)

WEB = Path(__file__).with_name('web')
class RevalidatingStatic(StaticFiles):
    """Dashboard files change between demo versions; make the browser revalidate (304 when unchanged) so an
    updated page never runs against a stale cached script or stylesheet."""

    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        resp.headers['Cache-Control'] = 'no-cache'
        return resp


app.mount('/static', RevalidatingStatic(directory=WEB), name='static')


@app.get('/dashboard', include_in_schema=False)
def dashboard():
    return FileResponse(WEB / 'dashboard.html', headers={'Cache-Control': 'no-cache'})

@app.get('/health')
def health(): return {'ok':True,'service':'levelup-demo','live_integrations':False,'model':MODEL}

@app.get('/agents')
def agents():
    from app.core import registry
    return registry.public()

@app.get('/sample')
def sample(): return SAMPLE

@app.get('/events/{run_id}')
def events(run_id:str):
    with db.tx() as c:
        rows=c.execute('select ts,actor,event,detail from events where run_id=? order by id',(run_id,)).fetchall()
    return [{'ts':a,'actor':b,'event':d,'detail':json.loads(e)} for a,b,d,e in rows]

@app.post('/demo/run')
async def run(req:DemoRequest):
    """Legacy endpoint kept for old scripts: now a thin wrapper over the Commander workflow (/runs)."""
    from app.core import workflow as wf
    from app.core.registry import AGENTS
    key=os.getenv('DEEPSEEK_API_KEY','')
    if req.use_llm and (not key or key=='PUT_YOUR_KEY_HERE'):
        raise HTTPException(400,'Missing DEEPSEEK_API_KEY. Configure .env or set use_llm=false.')
    run_id=wf.create_run(req.objective,'llm' if req.use_llm else 'mock',['bad_cost'] if req.inject_error else [])
    await wf.execute(run_id)
    r=wf.get_run(run_id)
    arts={t['task_key']:t['artifact'] or {} for t in r['tasks']}
    check=lambda k:{'status':arts.get(k,{}).get('status','NOT_RUN'),'findings':arts.get(k,{}).get('findings',[])}
    return {'run_id':run_id,'environment':'MOCK_ONLY','status':r['run']['status'],
            'checks':{'qa':check('qa'),'audit':check('audit'),'monitor':check('monitor')},
            'business_margin_before_ads_php':arts.get('offer',{}).get('margin_per_unit_php'),
            'outputs':[{'agent':AGENTS[t['agent_id']]['name'],'task':t['task_key'],'status':t['status'],
                        'output':(t['artifact'] or {}).get('narrative') or t['error']} for t in r['tasks']]}
