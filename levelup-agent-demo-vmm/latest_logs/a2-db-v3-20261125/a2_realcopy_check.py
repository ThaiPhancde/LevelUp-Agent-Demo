import os, shutil, sqlite3, json
os.environ['DEMO_DB_PATH'] = '/tmp/work.sqlite'
shutil.copy('/tmp/bak.sqlite', '/tmp/work.sqlite')
T = ['runs','tasks','events','artifacts','decision_log','approvals','llm_calls','engine_results']
def snap(p):
    c = sqlite3.connect(p); r = {t: c.execute(f'select * from {t} order by rowid').fetchall() for t in T}
    v = c.execute('select * from schema_version').fetchone(); c.close(); return r, v
before, v0 = snap('/tmp/work.sqlite')
from app import db
db.connect().close()
db._migrated.clear(); db.connect().close()
after, v1 = snap('/tmp/work.sqlite')
def same(b, a): return len(b) == len(a) and all(x[:len(y)] == y for y, x in zip(b, a))
res = {t: {'rows': len(before[t]), 'same': same(before[t], after[t])} for t in T}
c = sqlite3.connect('/tmp/work.sqlite')
newcols = c.execute('select max_rework, rooms, use_memory, memory_ids from runs limit 1').fetchone()
stop = db.get_stop_state()
shutil.copy('/tmp/bak.sqlite', '/tmp/restored.sqlite')
r = sqlite3.connect('/tmp/restored.sqlite')
ctrl = r.execute('select run_id, status from runs order by rowid limit 1').fetchone()
rv = r.execute('select * from schema_version').fetchone()
print(json.dumps({'schema_before': v0, 'schema_after': v1, 'tables': res, 'run_new_cols_default': newcols,
  'stop_state': stop, 'restored_schema': rv, 'restored_control_run': ctrl,
  'ok': all(x['same'] for x in res.values()) and v1[0] == 3 and rv[0] == 2 and ctrl is not None}, ensure_ascii=False, indent=1, default=str))
