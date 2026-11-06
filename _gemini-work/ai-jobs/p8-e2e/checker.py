"""Checker for ai-jobs/p8-e2e. Static only (the browser run is Claude's acceptance).
   python -I checker.py browser-e2e <repo-root>"""
import re
import subprocess
import sys
from pathlib import Path

SCENARIOS = ['load', 'happy-path', 'timeout-then-retry', 'publish-blocked', 'qa-bad-cost', 'overview-2d',
             'history-replay', 'no-console-errors']


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    p = root / 'tests/e2e/browser/dashboard.e2e.mjs'
    if job != 'browser-e2e':
        errors.append(f'unknown job {job}')
    elif not p.is_file():
        errors.append('missing tests/e2e/browser/dashboard.e2e.mjs')
    else:
        src = p.read_text(encoding='utf-8')
        r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
        if r.returncode:
            errors.append('syntax: ' + r.stderr.strip()[:300])
        for m in re.finditer(r"^\s*import\s+.*?from\s+['\"]([^'\"]+)['\"]", src, re.M):
            if m.group(1) != 'playwright' and not m.group(1).startswith('node:'):
                errors.append(f'forbidden import {m.group(1)}')
        for s in SCENARIOS:
            if f"'{s}'" not in src and f'"{s}"' not in src:
                errors.append(f'scenario {s} missing')
        for need in ['E2E_BASE_URL', 'E2E_SHOTS', 'E2E_RESULT', 'swiftshader', 'screenshot', 'process.exit']:
            if need not in src:
                errors.append(f'missing {need}')
        if re.search(r'waitForTimeout\(\s*([2-9]\d{3}|\d{5,})', src):
            errors.append('fixed sleep longer than 1 s')
        if re.search(r"fetch\(|request\.(post|put|delete)\(", src):
            errors.append('do not call the API directly to drive scenarios')
        if 'child_process' in src:
            errors.append('child_process forbidden')
    for e in errors:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
