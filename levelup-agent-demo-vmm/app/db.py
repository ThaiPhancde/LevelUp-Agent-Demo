"""SQLite access + idempotent migration. Path is read per call so tests can point DEMO_DB_PATH at a temp file."""
import contextlib
import datetime
import json
import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 3
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

CREATE TABLE IF NOT EXISTS rework_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, round INTEGER NOT NULL, target_task TEXT NOT NULL,
  agent_id TEXT NOT NULL, source_result_ids TEXT NOT NULL, findings TEXT NOT NULL, checks TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OPEN','RESOLVED','EXHAUSTED','NO_CHANGE')), prev_hash TEXT,
  created_at TEXT NOT NULL, resolved_at TEXT, UNIQUE(run_id, round));
CREATE TABLE IF NOT EXISTS rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('rework','risk')),
  topic TEXT NOT NULL, participants TEXT NOT NULL, max_rounds INTEGER NOT NULL, max_messages INTEGER NOT NULL,
  rounds_used INTEGER NOT NULL DEFAULT 0, messages_used INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('DONE','STOPPED','LIMIT')), created_at TEXT NOT NULL, closed_at TEXT);
CREATE TABLE IF NOT EXISTS room_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER NOT NULL, run_id TEXT NOT NULL, round INTEGER NOT NULL,
  agent_id TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('say','pass','skip')), reason TEXT, text TEXT,
  source TEXT CHECK (source IN ('mock','llm','mock_budget')), refs TEXT, number_warn INTEGER NOT NULL DEFAULT 0,
  ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memory_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL, version INTEGER NOT NULL, agent_id TEXT,
  sku TEXT, task_key TEXT, kind TEXT NOT NULL CHECK (kind IN ('check','lesson','preference')),
  tier TEXT NOT NULL CHECK (tier IN ('core','archive')), trust TEXT NOT NULL CHECK (trust IN ('user','derived','external')),
  content TEXT NOT NULL, text TEXT, status TEXT NOT NULL CHECK (status IN ('ACTIVE','RETIRED')),
  proposal_id INTEGER, created_by TEXT, uses INTEGER NOT NULL DEFAULT 0, last_used_run TEXT,
  created_at TEXT NOT NULL, retired_at TEXT,
  CHECK (NOT (kind = 'check' AND trust = 'external')), CHECK (NOT (tier = 'core' AND trust = 'external')),
  UNIQUE(key, version));
CREATE UNIQUE INDEX IF NOT EXISTS ux_memory_items_active_key ON memory_items(key) WHERE status = 'ACTIVE';
CREATE TABLE IF NOT EXISTS learning_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL, kind TEXT NOT NULL, agent_id TEXT, sku TEXT,
  task_key TEXT, content TEXT NOT NULL, text TEXT, evidence TEXT, source_runs TEXT, support INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('PROPOSED','REPLAYED_PASS','REPLAYED_FAIL','APPROVED','REJECTED','EXPIRED')),
  replay TEXT, generator_version TEXT, decided_by TEXT, decided_at TEXT, created_at TEXT NOT NULL,
  created_run_seq INTEGER);
CREATE UNIQUE INDEX IF NOT EXISTS ux_learning_proposals_open_key ON learning_proposals(key)
  WHERE status IN ('PROPOSED','REPLAYED_PASS','REPLAYED_FAIL');
CREATE TABLE IF NOT EXISTS learning_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, learn_seq INTEGER NOT NULL, reasons TEXT,
  proposed INTEGER NOT NULL DEFAULT 0, skipped INTEGER NOT NULL DEFAULT 0, error TEXT, created_at TEXT NOT NULL,
  UNIQUE(run_id, learn_seq));
CREATE TABLE IF NOT EXISTS learning_meta (k TEXT PRIMARY KEY, v INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS channel_inbox (
  channel TEXT NOT NULL, account TEXT NOT NULL, message_id TEXT NOT NULL, chat_id TEXT, sender_id TEXT,
  text TEXT, trust TEXT, decision TEXT, ts TEXT NOT NULL, PRIMARY KEY (channel, account, message_id));
CREATE TABLE IF NOT EXISTS channel_outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT NOT NULL, account TEXT NOT NULL, chat_id TEXT NOT NULL,
  text TEXT NOT NULL, buttons TEXT, ref_kind TEXT, ref_id TEXT, state TEXT NOT NULL CHECK (state IN ('DRAFT','SENT_MOCK')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts <= 3), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS brain_inbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT, by_agent TEXT, text TEXT NOT NULL, source TEXT,
  trust TEXT, status TEXT NOT NULL CHECK (status IN ('NEW','ACCEPTED','REJECTED')), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS system_stop (
  id INTEGER PRIMARY KEY CHECK (id = 1), stopped INTEGER NOT NULL DEFAULT 0, reason TEXT, actor TEXT,
  updated_at TEXT);
CREATE TABLE IF NOT EXISTS system_stop_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, reason TEXT, actor TEXT, ts TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_rework_run ON rework_requests(run_id);
CREATE INDEX IF NOT EXISTS ix_rooms_run ON rooms(run_id);
CREATE INDEX IF NOT EXISTS ix_room_messages_run ON room_messages(run_id);
CREATE INDEX IF NOT EXISTS ix_learning_runs_run ON learning_runs(run_id);
"""

# (table, column, DDL type/default) added onto an existing v2 table. Checked against
# PRAGMA table_info before ALTER so re-running the migration against a v2 volume is a no-op.
_ALTER_COLUMNS = (
    ('runs', 'max_rework', "INTEGER NOT NULL DEFAULT 0"),
    ('runs', 'rooms', "INTEGER NOT NULL DEFAULT 0"),
    ('runs', 'use_memory', "INTEGER NOT NULL DEFAULT 0"),
    ('runs', 'memory_ids', "TEXT NOT NULL DEFAULT '[]'"),
    ('approvals', 'tool', "TEXT"),
    ('approvals', 'decided_by', "TEXT"),
)


def _migrate_alter(c: sqlite3.Connection) -> None:
    for table, column, ddl in _ALTER_COLUMNS:
        cols = {row['name'] for row in c.execute(f'PRAGMA table_info({table})')}
        if column not in cols:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}')


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
        _migrate_alter(c)
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


def get_stop_state() -> dict:
    """Current emergency-stop state. Survives restart and reset (system_stop is never in RESET_TABLES)."""
    with tx() as c:
        row = c.execute('SELECT stopped, reason, actor, updated_at FROM system_stop WHERE id = 1').fetchone()
    if row is None:
        return {'stopped': False, 'reason': None, 'actor': None, 'updated_at': None}
    return {**dict(row), 'stopped': bool(row['stopped'])}


def set_stop(stopped: bool, actor: str, reason: str | None = None) -> dict:
    """Flip the demo-wide emergency stop and append a row to its audit log. Who may call this is enforced by A3."""
    ts = now()
    with tx() as c:
        c.execute(
            'INSERT INTO system_stop(id, stopped, reason, actor, updated_at) VALUES (1,?,?,?,?) '
            'ON CONFLICT(id) DO UPDATE SET stopped=excluded.stopped, reason=excluded.reason, '
            'actor=excluded.actor, updated_at=excluded.updated_at',
            (int(stopped), reason, actor, ts))
        c.execute('INSERT INTO system_stop_log(action, reason, actor, ts) VALUES (?,?,?,?)',
                  ('stop' if stopped else 'resume', reason, actor, ts))
    return get_stop_state()
