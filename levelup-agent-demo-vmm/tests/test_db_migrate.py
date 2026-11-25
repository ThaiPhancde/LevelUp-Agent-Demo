"""A2: schema v2 -> v3 migration, memory unique-active-key constraint, reset modes, emergency stop.

Each test points DEMO_DB_PATH at its own temp file (not the shared session DB from conftest.py) so it
can control exactly what schema version the file starts at.
"""
import importlib
import json
import sqlite3
import tempfile
import uuid
from pathlib import Path

import pytest

from app import db
from app.core import workflow as wf

# A pre-A2 (v2) schema snapshot, frozen on purpose: this is what a real v2 volume looks like on disk,
# independent of whatever app/db.py's SCHEMA constant grows into later.
_SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, ts TEXT, actor TEXT, event TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS llm_calls (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, task_id TEXT, model TEXT,
  prompt_tokens INTEGER, completion_tokens INTEGER, finish_reason TEXT, latency_ms INTEGER, status TEXT, cost_est REAL);
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, objective TEXT NOT NULL, mode TEXT NOT NULL CHECK (mode IN ('mock','llm')),
  status TEXT NOT NULL CHECK (status IN ('PENDING','RUNNING','WAITING_APPROVAL','COMPLETED','FAILED','CANCELLED')),
  inject TEXT NOT NULL DEFAULT '[]', token_total INTEGER NOT NULL DEFAULT 0, cost_est REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE IF NOT EXISTS tasks (
  run_id TEXT NOT NULL REFERENCES runs(run_id), task_key TEXT NOT NULL, agent_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','RUNNING','COMPLETED','FAILED','SKIPPED','CANCELLED')),
  depends_on TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0, artifact_id INTEGER, error TEXT,
  started_at TEXT, finished_at TEXT, PRIMARY KEY (run_id, task_key));
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, task_key TEXT NOT NULL, agent_id TEXT NOT NULL,
  type TEXT NOT NULL, attempt INTEGER NOT NULL, payload TEXT NOT NULL, narrative TEXT, valid INTEGER NOT NULL DEFAULT 1,
  validation_errors TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decision_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, task_key TEXT, agent_id TEXT, action TEXT NOT NULL,
  tool TEXT, permission TEXT, allowed INTEGER NOT NULL DEFAULT 1, input_hash TEXT, output_ref TEXT,
  duration_ms INTEGER, tokens INTEGER, detail TEXT, ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, task_key TEXT, reason TEXT, amount REAL,
  status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED')), decided_at TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS engine_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, engine TEXT NOT NULL CHECK (engine IN ('qa','audit','monitor')),
  status TEXT NOT NULL CHECK (status IN ('PASS','FAIL','WARN')), findings TEXT NOT NULL, created_at TEXT NOT NULL);
"""


@pytest.fixture
def v2_db_path(monkeypatch):
    tmp = Path(tempfile.mkdtemp(prefix='demo-test-v2-')) / 'v2.sqlite'
    monkeypatch.setenv('DEMO_DB_PATH', str(tmp))
    monkeypatch.setattr(db, '_migrated', set())  # force connect() to re-check/migrate this fresh path
    yield tmp


def _seed_v2(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA_V2)
    conn.execute("INSERT INTO schema_version(version) VALUES (2)")
    conn.execute(
        "INSERT INTO runs(run_id, objective, mode, status, created_at) VALUES (?,?,?,?,?)",
        ('run-old', 'obj', 'mock', 'COMPLETED', '2026-01-01T00:00:00+00:00'))
    conn.execute(
        "INSERT INTO events(run_id, ts, actor, event, detail) VALUES (?,?,?,?,?)",
        ('run-old', '2026-01-01T00:00:00+00:00', 'system', 'run_created', '{}'))
    conn.execute(
        "INSERT INTO artifacts(run_id, task_key, agent_id, type, attempt, payload, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        ('run-old', 'strategy', 'strategist', 'StrategyOutput', 1, '{}', '2026-01-01T00:00:00+00:00'))
    conn.execute(
        "INSERT INTO approvals(run_id, task_key, reason, amount, status, created_at) VALUES (?,?,?,?,?,?)",
        ('run-old', 'campaign', 'budget', 100.0, 'APPROVED', '2026-01-01T00:00:00+00:00'))
    conn.commit()
    conn.close()


def test_migrate_v2_to_v3_keeps_old_history(v2_db_path):
    _seed_v2(v2_db_path)
    with db.tx() as c:
        run = c.execute('SELECT * FROM runs WHERE run_id=?', ('run-old',)).fetchone()
        events = c.execute('SELECT * FROM events WHERE run_id=?', ('run-old',)).fetchall()
        artifacts = c.execute('SELECT * FROM artifacts WHERE run_id=?', ('run-old',)).fetchall()
        approvals = c.execute('SELECT * FROM approvals WHERE run_id=?', ('run-old',)).fetchall()
        version = c.execute('SELECT version FROM schema_version').fetchone()[0]

    assert run['run_id'] == 'run-old'
    assert len(events) == 1
    assert len(artifacts) == 1
    assert len(approvals) == 1
    assert version == 3
    # new columns got their defaults, not NULL/garbage, for pre-existing rows
    assert run['max_rework'] == 0
    assert run['rooms'] == 0
    assert run['use_memory'] == 0
    assert json.loads(run['memory_ids']) == []
    assert approvals[0]['tool'] is None
    assert approvals[0]['decided_by'] is None


def test_migrate_twice_is_a_noop(v2_db_path):
    _seed_v2(v2_db_path)
    with db.tx():
        pass  # first migration via connect()
    db._migrated.discard(str(v2_db_path))  # force a second independent migration pass on the same file
    with db.tx() as c:  # must not raise ("duplicate column", etc.)
        run = c.execute('SELECT * FROM runs WHERE run_id=?', ('run-old',)).fetchone()
        version = c.execute('SELECT version FROM schema_version').fetchone()[0]
    assert run['run_id'] == 'run-old'
    assert version == 3


def test_memory_items_one_active_per_key(v2_db_path):
    with db.tx() as c:
        c.execute(
            "INSERT INTO memory_items(key, version, kind, tier, trust, content, status, created_at) "
            "VALUES ('k1', 1, 'check', 'core', 'user', '{}', 'ACTIVE', ?)", (db.now(),))
    with pytest.raises(sqlite3.IntegrityError):
        with db.tx() as c:
            c.execute(
                "INSERT INTO memory_items(key, version, kind, tier, trust, content, status, created_at) "
                "VALUES ('k1', 2, 'check', 'core', 'user', '{}', 'ACTIVE', ?)", (db.now(),))
    # a RETIRED row for the same key is fine -- only one ACTIVE row is enforced
    with db.tx() as c:
        c.execute(
            "INSERT INTO memory_items(key, version, kind, tier, trust, content, status, created_at) "
            "VALUES ('k1', 2, 'check', 'core', 'user', '{}', 'RETIRED', ?)", (db.now(),))


def test_reset_default_keeps_memory_expires_open_proposals(v2_db_path):
    with db.tx() as c:
        c.execute(
            "INSERT INTO memory_items(key, version, kind, tier, trust, content, status, created_at) "
            "VALUES ('k1', 1, 'check', 'core', 'user', '{}', 'ACTIVE', ?)", (db.now(),))
        c.execute(
            "INSERT INTO learning_proposals(key, kind, content, status, created_at) "
            "VALUES ('k2', 'check', '{}', 'PROPOSED', ?)", (db.now(),))
        c.execute("INSERT INTO learning_meta(k, v) VALUES ('run_seq', 7)")

    wf.reset_demo(include_memory=False)

    with db.tx() as c:
        mem = c.execute("SELECT * FROM memory_items WHERE key='k1'").fetchone()
        prop = c.execute("SELECT * FROM learning_proposals WHERE key='k2'").fetchone()
        meta = c.execute("SELECT v FROM learning_meta WHERE k='run_seq'").fetchone()[0]
    assert mem is not None
    assert prop['status'] == 'EXPIRED'
    assert meta == 7


def test_reset_include_memory_deletes_memory_on_test_db(v2_db_path):
    with db.tx() as c:
        c.execute(
            "INSERT INTO memory_items(key, version, kind, tier, trust, content, status, created_at) "
            "VALUES ('k1', 1, 'check', 'core', 'user', '{}', 'ACTIVE', ?)", (db.now(),))
        c.execute(
            "INSERT INTO learning_proposals(key, kind, content, status, created_at) "
            "VALUES ('k2', 'check', '{}', 'PROPOSED', ?)", (db.now(),))

    wf.reset_demo(include_memory=True)

    with db.tx() as c:
        mem = c.execute("SELECT * FROM memory_items").fetchall()
        prop = c.execute("SELECT * FROM learning_proposals").fetchall()
    assert mem == []
    assert prop == []


def test_stop_survives_reset_and_reconnect(v2_db_path):
    db.set_stop(True, actor='jarvis', reason='pause demo')
    wf.reset_demo(include_memory=True)  # neither reset mode may touch system_stop/system_stop_log
    state = db.get_stop_state()
    assert state['stopped'] is True
    assert state['actor'] == 'jarvis'

    with db.tx() as c:  # simulate a restart: close and reopen the connection
        c.execute('SELECT 1')
    state_after_reconnect = db.get_stop_state()
    assert state_after_reconnect['stopped'] is True

    db.set_stop(False, actor='jarvis', reason='resume')
    assert db.get_stop_state()['stopped'] is False
    with db.tx() as c:
        log_rows = c.execute('SELECT action FROM system_stop_log ORDER BY id').fetchall()
    assert [r['action'] for r in log_rows] == ['stop', 'resume']
