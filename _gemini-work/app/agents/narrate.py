"""Narrative layer: text only, never numbers of record. Mock Mode fills templates from the artifact
(app/llm/mock_texts.json); LLM Mode asks DeepSeek to explain the artifact within a per-run token budget."""
import json
import os
import string
from pathlib import Path

from app import db

_TEXTS_PATH = Path(__file__).resolve().parent.parent / 'llm' / 'mock_texts.json'


def _texts() -> dict:
    try:
        return json.loads(_TEXTS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def flat(artifact: dict) -> dict:
    """Top-level scalars + one level of dict scalars as parent_child + list lengths as name_count."""
    out = {}
    for k, v in artifact.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, dict):
            out.update({f'{k}_{ck}': cv for ck, cv in v.items() if isinstance(cv, (str, int, float, bool))})
        elif isinstance(v, list):
            out[f'{k}_count'] = len(v)
    return out


def mock_narrative(task_key: str, artifact: dict) -> str:
    """Template text for this task; falls back to the artifact summary. Unknown placeholders never crash."""
    tpl = _texts().get(task_key)
    if not tpl:
        return artifact['summary']
    values = flat(artifact)
    try:
        names = {f for _, f, _, _ in string.Formatter().parse(tpl) if f}
        if not names <= set(values):
            return artifact['summary']
        return tpl.format(**values)
    except (ValueError, KeyError, IndexError):
        return artifact['summary']


def run_tokens(run_id: str) -> int:
    with db.tx() as c:
        return c.execute('SELECT COALESCE(SUM(prompt_tokens+completion_tokens),0) FROM llm_calls WHERE run_id=?',
                         (run_id,)).fetchone()[0]


def budget() -> int:
    return int(os.getenv('LLM_RUN_TOKEN_BUDGET', '20000'))


async def narrate(ctx, task_key: str, agent: dict, artifact: dict) -> tuple[str, str]:
    """Return (text, source). source: mock | llm | mock_budget. LLM errors propagate (task -> FAILED)."""
    if ctx.mode != 'llm':
        return mock_narrative(task_key, artifact), 'mock'
    if run_tokens(ctx.run_id) >= budget():
        return mock_narrative(task_key, artifact), 'mock_budget'
    from app.llm.deepseek import complete
    role = (artifact['agent_id'], agent['name'],
            f'{agent["responsibility"]}. Explain the artifact below in 2-4 Vietnamese sentences. '
            'Do not change, add or round any number; quote numbers exactly as given. Everything is synthetic and DRAFT.')
    text = await complete(role, ctx.objective, artifact, [], run_id=ctx.run_id, task_id=task_key)
    return text, 'llm'
