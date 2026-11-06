"""SQLite access + idempotent migration. Path is read per call so tests can point DEMO_DB_PATH at a temp file."""
import contextlib
import datetime
import json
import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2
_migrated: set[str] = set()

SCHEMA = """
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
CREATE INDEX IF NOT EXISTS ix_events_run ON events(run_id);
CREATE INDEX IF NOT EXISTS ix_artifacts_run ON artifacts(run_id);
CREATE INDEX IF NOT EXISTS ix_decision_run ON decision_log(run_id);
CREATE INDEX IF NOT EXISTS ix_llm_run ON llm_calls(run_id);
"""


def path() -> Path:
    return Path(os.getenv('DEMO_DB_PATH', '/app/data/demo.sqlite'))


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    if str(p) not in _migrated:
        c.executescript(SCHEMA)
        if c.execute('SELECT COUNT(*) FROM schema_version').fetchone()[0] == 0:
            c.execute('INSERT INTO schema_version(version) VALUES (?)', (SCHEMA_VERSION,))
        else:
            c.execute('UPDATE schema_version SET version = ?', (SCHEMA_VERSION,))
        c.commit()
        _migrated.add(str(p))
    return c


@contextlib.contextmanager
def tx():
    """One short transaction: commit on success, rollback on error, always close."""
    c = connect()
    try:
        with c:
            yield c
    finally:
        c.close()


def log_event(run_id, actor, event, detail):
    with tx() as c:
        c.execute('INSERT INTO events(run_id,ts,actor,event,detail) VALUES (?,?,?,?,?)',
                  (run_id, now(), actor, event, json.dumps(detail, ensure_ascii=False)))
