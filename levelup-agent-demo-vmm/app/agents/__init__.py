"""Agent dispatch: compute() in Python -> Act through the gateway -> narrative (mock or LLM) -> artifact.

Error injection (DEMO_ONLY P5), from the run's `inject` list:
  bad_cost                 mock data: LU-PH-001 supplier cost 9999 (applied in app.mock.data.facts_for)
  publish_attempt          Campaign Operator also requests meta_ads.publish (gateway blocks it)
  timeout:<task>           the agent hangs until the workflow timeout          } first attempt only, so a
  missing_field:<task>     one required artifact field is dropped              } retry of the same agent
  empty_response:<task>    the narrative comes back empty (like an empty LLM)  } succeeds
"""
import asyncio

from app.agents import business, checks, supervisors
from app.agents.narrate import mock_narrative, narrate
from app.core import artifacts, gateway
from app.core.graph import GRAPH
from app.core.registry import AGENTS
from app.engines import audit as audit_engine
from app.engines import monitor as monitor_engine
from app.engines import qa as qa_engine
from app.mock import data

_SIMPLE = {'market': business.market, 'product': business.product, 'offer': business.offer,
           'content': business.content, 'campaign': business.campaign, 'leads': business.leads,
           'care': business.care, 'kpi': business.kpi, 'finance': business.finance}
_COMMON = {'type', 'agent_id', 'summary', 'synthetic'}


def _injected(ctx, kind: str) -> bool:
    return ctx.attempt == 1 and f'{kind}:{ctx.task_key}' in ctx.inject


def compute(ctx, run_artifacts=None) -> dict:
    key = ctx.task_key
    if key == 'plan':
        return business.plan(ctx.facts, ctx.inputs, ctx.objective, GRAPH)
    if key in _SIMPLE:
        art = _SIMPLE[key](ctx.facts, ctx.inputs)
        if key == 'campaign' and 'publish_attempt' in ctx.inject:
            art['requested_actions'].append({'tool': 'meta_ads.publish', 'target': art['campaign_id']})
        art, applied = checks.apply_artifact(art, getattr(ctx, 'checks', ()))  # A4: e.g. drop a blocked action
        if applied:
            art['checks_applied'] = applied
        return art
    if key == 'summary':
        return business.summary(ctx.objective, run_artifacts)
    raise KeyError(f'no agent for task {key}')


def supervise(ctx) -> dict:
    """Run the deterministic engine for a supervisory task, store its result, return the agent's report."""
    from app.core import workflow  # read-only helpers + engine_results writer; avoids an import cycle
    if ctx.task_key == 'qa':
        result = qa_engine.run(workflow.completed_artifacts(ctx.run_id), data.facts_for([], ctx.objective),
                               workflow.rejected_artifacts(ctx.run_id))
    elif ctx.task_key == 'audit':
        result = audit_engine.run(workflow.completed_artifacts(ctx.run_id), workflow.tool_calls(ctx.run_id))
    else:
        result = monitor_engine.run(workflow.evidence(ctx.run_id))
    rid = workflow.save_engine_result(ctx.run_id, result)
    return supervisors.report(ctx.task_key, result, rid)


async def handle(ctx) -> dict:
    from app.core import workflow
    if _injected(ctx, 'timeout'):
        await asyncio.sleep(3600)  # the workflow's per-task timeout fires first
    if ctx.task_key in ('qa', 'audit', 'monitor'):
        art = supervise(ctx)
    else:
        art = compute(ctx, workflow.completed_artifacts(ctx.run_id) if ctx.task_key == 'summary' else None)
    if art.get('requested_actions'):
        art['action_results'] = [gateway.execute(ctx.run_id, ctx.task_key, ctx.agent_id, a, ctx.attempt)
                                 for a in art['requested_actions']]
    applied = list(getattr(ctx, 'applied', ())) + art.pop('checks_applied', [])
    if applied:
        art['checks_applied'] = applied  # split off and logged as check_applied by the workflow
    if getattr(ctx, 'feedback', ()):
        art['rework_feedback'] = list(ctx.feedback)
    if _injected(ctx, 'missing_field'):
        field = next(f for f in artifacts.SPEC[art['type']] if f not in _COMMON)
        art.pop(field, None)
    if _injected(ctx, 'empty_response'):
        text, source = '', 'mock'
    elif getattr(ctx, 'rework', False):  # A4: reworked tasks never spend LLM budget
        text, source = mock_narrative(ctx.task_key, art), 'mock'
    else:
        text, source = await narrate(ctx, ctx.task_key, AGENTS[ctx.agent_id], art)
    if not (text or '').strip():
        raise ValueError('empty narrative (agent returned no text)')
    art['narrative'], art['narrative_source'] = text, source
    return art
