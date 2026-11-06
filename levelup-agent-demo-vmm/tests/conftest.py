"""Every test gets its own SQLite file; nothing touches /app/data/demo.sqlite. Retry backoff is zeroed."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix='demo-test-')
os.environ['DEMO_DB_PATH'] = os.path.join(_tmp, 'test.sqlite')
os.environ['DEEPSEEK_BACKOFF_BASE'] = '0'
os.environ['MOCK_STEP_DELAY_S'] = '0'  # dashboard pacing off in tests
os.environ['DEEPSEEK_API_KEY'] = ''  # never a real key in tests (D-06); tests that need one monkeypatch it
