"""Phase 8 E2E runner (stdlib only, runs on the host). Starts fresh, isolated containers from the demo image,
never touches the main demo container or its data volume.

    python tools/e2e/run_e2e.py            # API scenarios + restart scenario + browser scenarios
    python tools/e2e/run_e2e.py --no-browser

Steps
  1. docker compose build (image levelup-vmm-demo-demo)
  2. container A on 127.0.0.1:8090: Mock Mode, DEEPSEEK_API_KEY="", MOCK_STEP_DELAY_S=0, TASK_TIMEOUT_S=1, DB in /tmp
  3. API scenarios S1-S5 (tests/e2e/test_e2e_api.py) from a second container over HTTP
  4. restart scenario on container B (step delay 1.5 s): restart mid-run, check checkpoint/recovery, retry
  5. browser scenarios (tests/e2e/browser/dashboard.e2e.mjs) in mcr.microsoft.com/playwright against container A
  6. stop containers, print one JSON summary line, exit 0 only if everything passed
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'levelup-vmm-demo-demo'
PW_IMAGE = 'mcr.microsoft.com/playwright:v1.48.2-jammy'
ENV = {**os.environ, 'MSYS_NO_PATHCONV': '1'}
RESULTS = ROOT / 'tests' / 'e2e' / 'results'


def sh(cmd, check=True, **kw):
    p = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding='utf-8', errors='replace', **kw)
    if check and p.returncode:
        raise RuntimeError(f'{" ".join(cmd)} -> {p.returncode}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}')
    return p


def start(name, port, extra_env):
    sh(['docker', 'rm', '-f', name], check=False)
    env = ['-e', 'DEEPSEEK_API_KEY=', '-e', 'DEMO_DB_PATH=/tmp/e2e.sqlite', '-e', 'TASK_TIMEOUT_S=1']
    for k, v in extra_env.items():
        env += ['-e', f'{k}={v}']
    sh(['docker', 'run', '-d', '--name', name, '-p', f'127.0.0.1:{port}:8088', *env, IMAGE])
    wait_health(port)


def wait_health(port, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as r:
                if json.load(r).get('ok'):
                    return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError(f'container on {port} not healthy')


def http(port, path, body=None):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method='POST' if body is not None else 'GET',
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def api_scenarios():
    p = sh(['docker', 'run', '--rm', '-e', 'E2E_BASE_URL=http://host.docker.internal:8090', IMAGE,
            'pytest', '-p', 'no:cacheprovider', '-q', 'tests/e2e/test_e2e_api.py', '-rA'], check=False)
    out = p.stdout + p.stderr
    lines = [ln for ln in out.splitlines() if ln.startswith(('PASSED', 'FAILED', 'ERROR'))]
    return {'ok': p.returncode == 0, 'summary': out.strip().splitlines()[-1] if out.strip() else '', 'cases': lines,
            'log_tail': out[-3000:] if p.returncode else ''}


def restart_scenario():
    """DEMO_ONLY P3: checkpoint and container restart. A task RUNNING at restart becomes FAILED 'interrupted'
    (DEMO_DECISIONS M-16); the run stays readable; retrying that task finishes the run."""
    name, port = 'lu-e2e-restart', 8091
    start(name, port, {'MOCK_STEP_DELAY_S': '1.5'})
    try:
        rid = http(port, '/runs', {})['run_id']
        time.sleep(4.0)                                   # plan done, a later task is RUNNING (delay 1.5 s/task)
        before = {t['task_key']: t['status'] for t in http(port, f'/runs/{rid}')['tasks']}
        sh(['docker', 'restart', name])
        wait_health(port)
        after = http(port, f'/runs/{rid}')
        st = {t['task_key']: t for t in after['tasks']}
        interrupted = [k for k, t in st.items() if t['status'] == 'FAILED' and (t['error'] or '').startswith('interrupted')]
        kept = [k for k, s in before.items() if s == 'COMPLETED' and st[k]['status'] == 'COMPLETED']
        ok = after['run']['status'] == 'FAILED' and len(interrupted) == 1 and kept
        if ok:
            http(port, f'/runs/{rid}/tasks/{interrupted[0]}/retry', {})
            end = time.time() + 60
            while time.time() < end and http(port, f'/runs/{rid}')['run']['status'] in ('PENDING', 'RUNNING'):
                time.sleep(1)
            final = http(port, f'/runs/{rid}')['run']['status']
            ok = final == 'COMPLETED'
        else:
            final = after['run']['status']
        return {'ok': bool(ok), 'running_before_restart': [k for k, s in before.items() if s == 'RUNNING'],
                'completed_kept': kept, 'interrupted': interrupted, 'final_status': final}
    finally:
        sh(['docker', 'rm', '-f', name], check=False)


def browser_scenarios():
    script = ROOT / 'tests' / 'e2e' / 'browser' / 'dashboard.e2e.mjs'
    if not script.is_file():
        return {'ok': False, 'error': 'tests/e2e/browser/dashboard.e2e.mjs missing'}
    shots = RESULTS / 'shots'
    shots.mkdir(parents=True, exist_ok=True)
    cmd = ('mkdir -p /run/pw && cd /run/pw && npm init -y >/dev/null 2>&1 && npm i playwright@1.48.2 >/dev/null 2>&1 '
           '&& cp /e2e/dashboard.e2e.mjs . && node dashboard.e2e.mjs')
    p = sh(['docker', 'run', '--rm', '--ipc=host',
            '-v', f'{script.parent.as_posix()}:/e2e:ro', '-v', f'{shots.as_posix()}:/shots',
            '-e', 'E2E_BASE_URL=http://host.docker.internal:8090', '-e', 'E2E_SHOTS=/shots',
            PW_IMAGE, 'bash', '-c', cmd], check=False, timeout=900)
    out = p.stdout + p.stderr
    line = next((ln for ln in out.splitlines() if ln.startswith('E2E_RESULT ')), None)
    res = json.loads(line[len('E2E_RESULT '):]) if line else {'error': 'no E2E_RESULT line', 'log_tail': out[-3000:]}
    res['ok'] = p.returncode == 0 and bool(line)
    return res


def main():
    browser = '--no-browser' not in sys.argv
    RESULTS.mkdir(parents=True, exist_ok=True)
    sh(['docker', 'compose', 'build', '-q'])
    summary = {}
    try:
        start('lu-e2e', 8090, {'MOCK_STEP_DELAY_S': '0'})
        summary['api'] = api_scenarios()
        summary['restart'] = restart_scenario()
        if browser:
            summary['browser'] = browser_scenarios()
    finally:
        sh(['docker', 'rm', '-f', 'lu-e2e'], check=False)
    summary['ok'] = all(v.get('ok') for v in summary.values() if isinstance(v, dict))
    (RESULTS / 'latest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
    print('E2E_SUMMARY ' + json.dumps(summary, ensure_ascii=False))
    sys.exit(0 if summary['ok'] else 1)


if __name__ == '__main__':
    main()
