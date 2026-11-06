"""Checker for ai-jobs/p4-agents. Stdlib only.   python -I checker.py <job-id> <repo-root>"""
import json
import re
import string
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'p3-workflow'))
from checker import check_test_file  # noqa: E402  reuse: static checks + pytest in the demo image

KEYS = ['plan', 'market', 'product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary']
MUST = {'offer': {'selling_price_php', 'margin_per_unit_php', 'breakeven_orders'},
        'kpi': {'roas', 'cpa_confirmed_php', 'cpa_delivered_php'},
        'finance': {'contribution_after_ads_php', 'risk_level'},
        'qa': {'status', 'findings_count'}, 'audit': {'status', 'findings_count'}, 'monitor': {'status', 'findings_count'}}
WORDS = {'plan': 'giả lập', 'market': 'giả lập', 'content': 'DRAFT', 'campaign': 'DRAFT'}
BANNED = re.compile(r'(đã publish|đã đăng quảng cáo|đã thanh toán|đã gửi tin|khách hàng thật|doanh số thật)', re.I)
VI = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.I)


def check_texts(root, errors):
    p = root / 'app/llm/mock_texts.json'
    if not p.is_file():
        errors.append('missing app/llm/mock_texts.json')
        return
    try:
        doc = json.loads(p.read_text(encoding='utf-8'))
    except ValueError as exc:
        errors.append(f'bad json: {exc}')
        return
    sample = json.loads((HERE / 'sample_flat.json').read_text(encoding='utf-8'))
    if sorted(doc) != sorted(KEYS):
        errors.append(f'keys must be exactly {KEYS}')
    for k in KEYS:
        t = doc.get(k)
        if not isinstance(t, str):
            errors.append(f'{k}: not a string')
            continue
        if not 60 <= len(t) <= 400:
            errors.append(f'{k}: length {len(t)}')
        if re.search(r'\d', t):
            errors.append(f'{k}: digits not allowed in template')
        try:
            fields = [(f, spec, conv) for _, f, spec, conv in string.Formatter().parse(t) if f is not None]
        except ValueError as exc:
            errors.append(f'{k}: bad format string {exc}')
            continue
        names = {f for f, _, _ in fields}
        if any(spec or conv for _, spec, conv in fields) or any(re.search(r'[.\[]', f) for f in names):
            errors.append(f'{k}: no format specs / attribute or index access')
        unknown = names - set(sample[k])
        if unknown:
            errors.append(f'{k}: unknown placeholders {sorted(unknown)}')
        if len(names) < 3:
            errors.append(f'{k}: need >= 3 placeholders')
        if not MUST.get(k, set()) <= names:
            errors.append(f'{k}: must use {sorted(MUST[k] - names)}')
        if k in WORDS and WORDS[k].lower() not in t.lower():
            errors.append(f'{k}: must mention {WORDS[k]!r}')
        if BANNED.search(t):
            errors.append(f'{k}: banned claim')
        if len(VI.findall(t)) < 5:
            errors.append(f'{k}: not Vietnamese enough')
        if not unknown:
            print(f'{k}: {t.format(**sample[k])}')


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    if job == 'mock-texts':
        check_texts(root, errors)
    elif job == 'compute-tests':
        check_test_file(root, 'tests/test_agents_table.py', 'app.agents.business', 40, errors)
    elif job == 'supervisor-tests':
        check_test_file(root, 'tests/test_supervisors_table.py', 'app.agents.supervisors', 30, errors)
    else:
        errors.append(f'unknown job {job}')
    for e in errors:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
