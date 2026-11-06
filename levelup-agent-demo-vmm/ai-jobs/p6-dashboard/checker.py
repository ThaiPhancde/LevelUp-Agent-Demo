"""Checker for ai-jobs/p6-dashboard. Stdlib + node.   python -I checker.py <job-id> <repo-root>"""
import json
import re
import subprocess
import sys
from pathlib import Path

VI = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.I)
HANDLERS = ['onStart', 'onRetry', 'onCancel', 'onApprove', 'onOpenRun', 'onToggle', 'onResetCamera', 'onView', 'onRefreshHistory']
METHODS = ['setAgents', 'render', 'renderHistory', 'selectTask', 'setView', 'showError']
MUST_TEXT = ['Văn phòng Level Up', 'MOCK ONLY', 'Start Demo', 'Tự xoay', 'Bong bóng', 'Toàn cảnh', 'Tổng quan',
             'Kết quả cuối', 'Nhật ký', 'Lịch sử', 'Token', 'Duyệt', 'Từ chối', 'Retry', 'Đầu vào', 'Đầu ra']
INJECT = ['bad_cost', 'publish_attempt', 'timeout:', 'missing_field:', 'empty_response:']


def node_check(path, errors):
    p = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        errors.append(f'{path.name}: syntax error {p.stderr.strip()[:300]}')


def check_panels(root, errors):
    web = root / 'app/web'
    files = {n: web / n for n in ('dashboard.html', 'styles.css', 'panels.js')}
    for n, p in files.items():
        if not p.is_file():
            errors.append(f'missing app/web/{n}')
    if errors:
        return
    html, css, js = (files[n].read_text(encoding='utf-8') for n in ('dashboard.html', 'styles.css', 'panels.js'))
    for tag in ['"three":"/static/vendor/three.module.min.js"', '"three/addons/":"/static/vendor/"',
                'src="/static/main.js"', 'href="/static/styles.css"', 'id="office"', 'id="app"']:
        if tag not in html.replace(' ', '').replace("'", '"') and tag.replace(' ', '') not in html.replace(' ', ''):
            errors.append(f'dashboard.html missing {tag}')
    node_check(files['panels.js'], errors)
    if not re.search(r'export\s+function\s+createPanels\s*\(', js):
        errors.append('panels.js must export function createPanels')
    for h in HANDLERS:
        if h not in js:
            errors.append(f'panels.js never calls handlers.{h}')
    for m in METHODS:
        if not re.search(rf'\b{m}\b', js):
            errors.append(f'panels.js does not return {m}')
    for inj in INJECT:
        if inj not in js:
            errors.append(f'injection {inj} not built')
    allfiles = html + css + js
    if re.search(r'https?://', allfiles):
        errors.append('external URL found (offline only)')
    if re.search(r'\beval\s*\(|new\s+Function\s*\(', js):
        errors.append('eval/new Function forbidden')
    if re.search(r'\son[a-z]+\s*=\s*["\']', html):
        errors.append('inline event attribute in HTML')
    for m in re.finditer(r'\.(innerHTML|outerHTML)\s*=\s*([^;\n]+)', js):
        if m.group(2).strip() not in ("''", '""', '``'):
            errors.append(f'{m.group(1)} assignment with content: {m.group(0)[:60]}')
    if 'insertAdjacentHTML' in js or 'document.write' in js:
        errors.append('insertAdjacentHTML/document.write forbidden')
    fetches = re.findall(r'fetch\s*\(([^)]*)', js)
    if any('decision-log' not in f for f in fetches):
        errors.append('only fetch allowed: GET /runs/{id}/decision-log')
    if 'prefers-reduced-motion' not in css:
        errors.append('styles.css must respect prefers-reduced-motion')
    if not re.search(r'data-view\s*=\s*["\']?2d', css):
        errors.append('styles.css must handle body[data-view="2d"]')
    if '<svg' not in js and "createElementNS" not in js:
        errors.append('2D overview must draw an SVG graph')
    text = html + js
    for t in MUST_TEXT:
        if t not in text:
            errors.append(f'missing UI text {t!r}')
    if len(VI.findall(text)) < 150:
        errors.append('too little Vietnamese text')
    print(f'panels-ui: html {len(html)} B, css {len(css)} B, js {len(js)} B')


PROPS_CHECK = r"""
const L = await import(process.argv[1]); const P = await import(process.argv[2]);
const errs = []; const rooms = Object.fromEntries(L.ROOMS.map(r => [r.agentId, r]));
const keys = [...Object.keys(rooms), 'gateway'];
const props = P.PROPS || {}; let total = 0;
for (const k of keys) if (!(k in props)) errs.push('missing room ' + k);
for (const k of Object.keys(props)) if (!keys.includes(k)) errs.push('unknown room ' + k);
for (const [k, items] of Object.entries(props)) {
  if (!Array.isArray(items)) { errs.push(k + ' not an array'); continue; }
  const max = k === 'gateway' ? 12 : 10; const min = k === 'gateway' ? 3 : 4;
  if (items.length < min || items.length > max) errs.push(`${k}: ${items.length} items`);
  total += items.length;
  const r = rooms[k] || { w: 6, d: 6 };
  items.forEach((it, i) => {
    const id = `${k}[${i}]`; const s = it.size || []; const p = it.pos || [];
    if (!['box', 'cylinder', 'cone', 'sphere'].includes(it.shape)) errs.push(id + ' bad shape');
    const want = { box: 3, cylinder: 2, cone: 2, sphere: 1 }[it.shape];
    if (s.length !== want || s.some(v => typeof v !== 'number' || v <= 0)) errs.push(id + ' bad size');
    if (p.length !== 3 || p.some(v => typeof v !== 'number')) { errs.push(id + ' bad pos'); return; }
    if (!/^#[0-9a-fA-F]{6}$/.test(it.color || '')) errs.push(id + ' bad color');
    if (it.label !== undefined && (typeof it.label !== 'string' || it.label.length > 24)) errs.push(id + ' bad label');
    const hw = it.shape === 'box' ? s[0] / 2 : s[0]; const hd = it.shape === 'box' ? s[2] / 2 : s[0];
    const h = it.shape === 'box' ? s[1] : it.shape === 'sphere' ? 2 * s[0] : s[1];
    if (Math.abs(p[0]) + hw > r.w / 2 - 0.3 + 1e-9 || Math.abs(p[2]) + hd > r.d / 2 - 0.3 + 1e-9) errs.push(id + ' outside room');
    if (p[1] < 0 || p[1] + h > 3) errs.push(id + ' too high or below floor');
    if (k !== 'gateway' && Math.abs(p[0]) - hw < 0.9 && Math.abs(p[2]) - hd < 0.9) errs.push(id + ' blocks the desk centre');
  });
}
if (total > 140) errs.push('too many props ' + total);
console.log(JSON.stringify({ total, errs }));
"""


def check_props(root, errors):
    p = root / 'app/web/office-props.js'
    if not p.is_file():
        errors.append('missing app/web/office-props.js')
        return
    node_check(p, errors)
    if errors:
        return
    layout = (root / 'app/web/office-layout.js').resolve().as_uri()
    proc = subprocess.run(['node', '--input-type=module', '-e', PROPS_CHECK, layout, p.resolve().as_uri()],
                          capture_output=True, text=True, encoding='utf-8')
    if proc.returncode != 0:
        errors.append('node failed: ' + proc.stderr.strip()[:400])
        return
    res = json.loads(proc.stdout.strip().splitlines()[-1])
    errors += res['errs'][:30]
    print(f'office-props: {res["total"]} items')


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    if job == 'panels-ui':
        check_panels(root, errors)
    elif job == 'office-props':
        check_props(root, errors)
    else:
        errors.append(f'unknown job {job}')
    for e in errors:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
