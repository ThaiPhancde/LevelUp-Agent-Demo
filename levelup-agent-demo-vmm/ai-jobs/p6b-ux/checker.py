"""Checker for ai-jobs/p6b-ux. Static only; the browser acceptance is Claude's.   python -I checker.py left-rail-wording <repo-root>"""
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_TEXT = ['(Objective)', '(Mode)', 'Error Injection', 'inject:', '(attempt)', '(decision)', '(key)', '(task_key)',
                  '(detail)', '(depends_on)', 'HITL', 'Artifact', 'Phase 5', 'engine']
ENGLISH_STATUS = ['COMPLETED', 'FAILED', 'PENDING', 'RUNNING', 'SKIPPED', 'CANCELLED', 'WAITING_APPROVAL', 'PASS', 'FAIL', 'WARN']
MUST_USE = ['RUN_STATUS_LABEL', 'TASK_STATUS_LABEL', 'TASK_TITLE', 'AGENT_ROLE', 'SCENARIOS', 'RULE_LABEL', 'SEVERITY_LABEL',
            'CHECK_STATUS_LABEL', 'ENGINE_LABEL', 'DECISION_LABEL', 'DECISION_HINT', 'ACTION_LABEL', 'TOOL_LABEL',
            'LLM_SOURCE_LABEL', 'errorText', 'scenarioText', 'formatTime', 'overviewCounts']
MUST_TEXT = ['Tổng quan', 'Chạy kịch bản mới', 'Đang làm', 'Chờ làm', 'Chờ duyệt', 'Lỗi', 'Việc của lượt này', 'Mục tiêu kinh doanh',
             'Tình huống thử', 'Kết quả cuối', 'Kiểm tra', 'Token & chi phí', 'Nhật ký', 'Lịch sử', 'Thử lại bước này', 'Duyệt', 'Từ chối',
             'Chi tiết kỹ thuật', 'MOCK ONLY', 'Start Demo', 'Tự xoay', 'Bong bóng', 'Toàn cảnh', 'Tổng quan (2D)'.split(' (')[0]]
MUST_ATTR = ['data-run-status', 'data-decision', 'data-check-status', 'data-task-status', 'data-rule']
MUST_KEEP = ['dock-grip', 'toggle-dock', 'DOCK_KEY', 'setDock', 'start-demo', 'retry-task', 'cancel-run', 'refresh-history', 'approve', 'reject']
HANDLERS = ['onStart', 'onRetry', 'onCancel', 'onApprove', 'onOpenRun', 'onToggle', 'onResetCamera', 'onView', 'onRefreshHistory']
METHODS = ['setAgents', 'render', 'renderHistory', 'selectTask', 'setView', 'showError']


def string_literals(src):
    return re.findall(r"""(?P<q>['"`])((?:\.|(?!(?P=q)).)*)(?P=q)""", src, re.S)


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    js_path, css_path = root / 'app/web/panels.js', root / 'app/web/styles.css'
    if job != 'left-rail-wording':
        errors.append(f'unknown job {job}')
    elif not js_path.is_file() or not css_path.is_file():
        errors.append('missing panels.js or styles.css')
    else:
        js, css = js_path.read_text(encoding='utf-8'), css_path.read_text(encoding='utf-8')
        r = subprocess.run(['node', '--check', str(js_path)], capture_output=True, text=True)
        if r.returncode:
            errors.append('syntax: ' + r.stderr.strip()[:300])
        imports = re.findall(r"^import\s+.*?from\s+['\"]([^'\"]+)['\"]", js, re.M)
        if any(i != './labels.js' for i in imports) or './labels.js' not in imports:
            errors.append(f'only import ./labels.js is allowed (found {imports})')
        for name in MUST_USE:
            if not re.search(rf'\b{name}\b', js):
                errors.append(f'labels.js export {name} is never used')
        for t in MUST_TEXT:
            if t not in js:
                errors.append(f'missing UI text {t!r}')
        for a in MUST_ATTR:
            if a not in js and a.replace('data-', '') not in js:
                errors.append(f'missing hook {a}')
        for k in MUST_KEEP + HANDLERS + METHODS:
            if k not in js:
                errors.append(f'lost required code {k}')
        if re.search(r'https?://', js + css):
            errors.append('external URL')
        if re.search(r'\beval\s*\(|new\s+Function\s*\(|insertAdjacentHTML|document\.write', js):
            errors.append('eval / insertAdjacentHTML forbidden')
        for m in re.finditer(r'\.(innerHTML|outerHTML)\s*=\s*([^;\n]+)', js):
            if m.group(2).strip() not in ("''", '""', '``'):
                errors.append(f'{m.group(1)} assignment with content')
        if any('decision-log' not in f for f in re.findall(r'fetch\s*\(([^)]*)', js)):
            errors.append('only fetch allowed: decision-log')
        if 'prefers-reduced-motion' not in css:
            errors.append('css lost prefers-reduced-motion')
        for q, lit in string_literals(js):
            for bad in FORBIDDEN_TEXT:
                if bad in lit and '${' not in lit[:0]:
                    errors.append(f'forbidden text {bad!r} in literal {lit[:60]!r}')
            if re.search(r'(^|[^A-Za-z_.\-])(' + '|'.join(ENGLISH_STATUS) + r')([^A-Za-z_]|$)', lit) and re.search(r'\s', lit.strip()) \
                    and not re.fullmatch(r'[A-Z_|, ]+', lit.strip()):
                errors.append(f'English status word inside visible-looking text {lit[:60]!r}')
        if re.search(r'textContent:\s*[^,\n]*run_id', js):
            errors.append('run_id shown as text')
        print(f'panels.js {len(js)} B, styles.css {len(css)} B, imports {imports}')
    errors = sorted(set(errors))
    for e in errors[:40]:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
