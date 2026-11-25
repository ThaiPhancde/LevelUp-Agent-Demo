"""Checker for ai-jobs/oa-a3. Stdlib only.   python -I checker.py <job-id> <repo-root>"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'p3-workflow'))
from checker import check_test_file  # noqa: E402

JOBS = {'attempt-tests': ('tests/test_gateway_attempt_table.py', 'app.core.gateway', 30)}


def main():
    job, root = sys.argv[1], Path(sys.argv[2])
    errors = []
    if job in JOBS:
        check_test_file(root, *JOBS[job], errors)
    else:
        errors.append(f'unknown job {job}')
    for e in errors:
        print('ERROR', e)
    print('OK' if not errors else f'FAIL ({len(errors)} errors)')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
