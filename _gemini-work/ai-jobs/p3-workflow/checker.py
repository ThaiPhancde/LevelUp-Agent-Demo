"""Checker for ai-jobs/p3-workflow. Stdlib only.   python -I checker.py <job-id> <repo-root>
Static checks run anywhere; pytest runs inside the demo Docker image (bind mount of the repo root)."""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_IMPORTS = {'pytest', 'copy', 'json', 'itertools', 'pathlib', 'os', 'math'}


def count_cases(tree):
    """Sum of parametrize table lengths + plain test functions without parametrize."""
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            params = [d for d in node.decorator_list if isinstance(d, ast.Call)
                      and getattr(d.func, 'attr', '') == 'parametrize']
            if not params:
                total += 1
            for d in params:
                arg = d.args[1] if len(d.args) > 1 else None
                if isinstance(arg, (ast.List, ast.Tuple)):
                    total += len(arg.elts)
                else:
                    total += 1  # computed table: count once statically, pytest gives the real number
    return total


def check_test_file(root, rel, module, min_cases, errors):
    p = root / rel
    if not p.is_file():
        errors.append(f'missing {rel}')
        return
    src = p.read_text(encoding='utf-8')
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        errors.append(f'syntax error: {exc}')
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split('.')[0] not in ALLOWED_IMPORTS:
                    errors.append(f'forbidden import {a.name}')
        elif isinstance(node, ast.ImportFrom):
            if node.module != module.rsplit('.', 1)[0] and node.module != module and \
                    (node.module or '').split('.')[0] not in ALLOWED_IMPORTS:
                errors.append(f'forbidden import from {node.module}')
    if re.search(r'\b(requests|httpx|urllib|socket|subprocess)\b', src):
        errors.append('network/process usage is forbidden')
    if 'ids=' not in src:
        errors.append('parametrize tables need ids=')
    static = count_cases(tree)
    proc = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{root.resolve()}:/w', '-w', '/w', '-e', 'PYTHONPATH=/w',
         'levelup-vmm-demo-demo', 'pytest', '-p', 'no:cacheprovider', '-q', rel],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or ['']
    m = re.search(r'(\d+) passed', tail[0])
    ran = int(m.group(1)) if m else 0
    print(f'{rel}: static cases {static}, pytest: {tail[0]}')
    if proc.returncode != 0:
        errors.append(f'pytest failed: {tail[0]}')
        print((proc.stdout + proc.stderr)[-3000:])
    if ran < min_cases:
        errors.append(f'only {ran} passing cases, need >= {min_cases}')


PRICES = {'LU-PH-001': '499', 'LU-PH-002': '699', 'LU-PH-003': '299'}
ENUMS = {
    'channel': {'messenger_mock', 'tiktok_mock', 'website_chat_mock'},
    'language': {'en', 'fil', 'taglish'},
    'sku': set(PRICES),
    'stage': {'lead', 'confirmed', 'delivered', 'returned'},
    'intent': {'product_question', 'price_question', 'shipping_question', 'order_status', 'complaint', 'return_request'},
}
MINIMUM = {'language': 3, 'sku': 3, 'stage': 2, 'intent': 1}
BANNED = re.compile(r'(card number|cvv|password|one[- ]time|otp|refund (?:is|will be) (?:processed|guaranteed)|'
                    r'guarantee|http|www\.|@\w+\.\w+|discount)', re.I)


def check_conversations(root, errors):
    p = root / 'app/mock/conversations.json'
    if not p.is_file():
        errors.append('missing app/mock/conversations.json')
        return
    try:
        doc = json.loads(p.read_text(encoding='utf-8'))
    except ValueError as exc:
        errors.append(f'bad json: {exc}')
        return
    if doc.get('synthetic') is not True or set(doc) != {'synthetic', 'items'}:
        errors.append('top level must be exactly {"synthetic": true, "items": [...]}')
    items = doc.get('items') or []
    if len(items) != 12:
        errors.append(f'need exactly 12 items, got {len(items)}')
    counts = {k: {} for k in ENUMS}
    for n, it in enumerate(items, 1):
        cid = f'CONV-{n:03d}'
        if it.get('conversation_id') != cid:
            errors.append(f'item {n}: conversation_id must be {cid}')
        if set(it) != {'conversation_id', 'channel', 'language', 'sku', 'stage', 'intent', 'messages', 'synthetic'}:
            errors.append(f'{cid}: wrong keys {sorted(it)}')
        if it.get('synthetic') is not True:
            errors.append(f'{cid}: synthetic must be true')
        for k, allowed in ENUMS.items():
            v = it.get(k)
            if v not in allowed:
                errors.append(f'{cid}: {k}={v!r} not allowed')
            counts[k][v] = counts[k].get(v, 0) + 1
        msgs = it.get('messages') or []
        if not 2 <= len(msgs) <= 6:
            errors.append(f'{cid}: 2-6 messages')
        if msgs and msgs[0].get('from') != 'customer':
            errors.append(f'{cid}: first message must be from customer')
        allowed_nums = {PRICES.get(it.get('sku'), ''), '75', '3', f'{n:03d}'}
        for m in msgs:
            if set(m) != {'from', 'text'} or m.get('from') not in ('customer', 'agent_draft'):
                errors.append(f'{cid}: bad message {m}')
                continue
            t = m['text']
            if not 5 <= len(t) <= 280:
                errors.append(f'{cid}: text length {len(t)}')
            t_wo_ref = t.replace(f'ORD-{n:03d}', '')
            for num in re.findall(r'\d[\d,.]*', t_wo_ref):
                if num.rstrip('.,') not in allowed_nums:
                    errors.append(f'{cid}: number {num!r} not allowed')
            if BANNED.search(t):
                errors.append(f'{cid}: banned phrase in {t[:60]!r}')
    for k, minimum in MINIMUM.items():
        for v in ENUMS[k]:
            if counts[k].get(v, 0) < minimum:
                errors.append(f'{k}={v} used {counts[k].get(v, 0)} times, need >= {minimum}')
    print(f'conversations: {len(items)} items, languages {counts["language"]}')


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    if job == 'graph-tests':
        check_test_file(root, 'tests/test_graph_table.py', 'app.core.graph', 45, errors)
    elif job == 'data-tests':
        check_test_file(root, 'tests/test_mock_data.py', 'app.mock.data', 15, errors)
    elif job == 'conversations':
        check_conversations(root, errors)
    else:
        errors.append(f'unknown job {job}')
    for e in errors:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
