// ARIS adapter spike (Phase 7). Runs ARIS's real Commander dispatch code (`planCards`, `dispatch` from
// packages/aris-commander/src/dispatch.ts, MIT) against a LevelUp TeamPort whose "teammates" are our demo
// agents calling our Mock API. No LLM: the deciding Commander is a deterministic loop here, ARIS only plans
// cards and dispatches. If ARIS cannot be loaded or dispatch fails, we fall back to the internal runtime.
//
//   docker run --rm -v <aris>:/aris:ro -v <this dir>:/spike:ro -e DEMO_URL=http://host.docker.internal:8088 \
//     node:22-bookworm node /spike/spike.mjs
const DEMO = process.env.DEMO_URL || 'http://127.0.0.1:8088';
const ARIS = process.env.ARIS_DISPATCH || '/aris/packages/aris-commander/src/dispatch.ts';
const trace = [];
const log = (event, data = {}) => { trace.push({ t: new Date().toISOString(), event, ...data }); };

async function http(path, init) {
  const r = await fetch(DEMO + path, { headers: { 'content-type': 'application/json' }, ...init });
  if (!r.ok) throw new Error(`${path} -> HTTP ${r.status}`);
  return r.json();
}

// Our registry is the bot roster; a bot "works" by calling the READ tools the registry gives it.
const TOOL_PATH = { 'mock.market': '/mock/market', 'mock.meta_ads': '/mock/meta-ads', 'mock.leads': '/mock/leads',
  'mock.orders': '/mock/orders', 'mock.products': '/mock/products', 'mock.suppliers': '/mock/suppliers',
  'mock.logistics': '/mock/logistics', 'mock.finance': '/mock/finance', 'mock.campaigns': '/mock/campaigns',
  'mock.customer_conversations': '/mock/customer-conversations' };

class LevelUpTeamPort {
  constructor(agents) { this.agents = agents; this.tasks = new Map(); this.members = []; this.seq = 0; this.work = []; }
  listMembers() { return this.members; }
  async spawnTeammate(_agent, req) {
    const member = { id: `m-${req.name}`, name: req.name, status: 'running' };
    this.members.push(member);
    // start only after dispatch() has assigned the card, like a dsh teammate picking up its turn
    this.work.push(() => this.runBot(member, req.prompt.map((p) => p.text).join('\n')));
    return { member: { id: member.id } };
  }
  async sendMessage(_agent, req) { log('send_message', { target: req.target }); }
  async createTask(_agent, req) {
    const id = `task-${++this.seq}`;
    this.tasks.set(id, { id, revision: 1, subject: req.subject, status: 'pending', owner: null, blockedBy: req.blockedBy || [] });
    return { id, revision: 1 };
  }
  getTask(_agent, id) {
    const t = this.tasks.get(id);
    if (!t) throw new Error('no task');
    return { id, revision: t.revision, subject: t.subject, status: t.status,
             ready: t.blockedBy.every((b) => this.tasks.get(b)?.status === 'completed') };
  }
  async updateTask(_agent, req) {
    const t = this.tasks.get(req.taskId);
    if (!t || t.revision !== req.expectedRevision) throw new Error('revision conflict');
    if (req.action === 'reassign') { t.owner = req.owner; t.status = 'in_progress'; }
    if (req.action === 'complete') t.status = 'completed';
    t.revision += 1;
  }
  async runBot(member, brief) {
    const agent = this.agents.find((a) => a.tasks.includes(member.name));
    const reads = agent.tools.filter((tool) => TOOL_PATH[tool]);
    const data = {};
    for (const tool of reads) data[tool] = (await http(TOOL_PATH[tool])).data;   // mock tools only
    log('bot_worked', { bot: member.name, agent_id: agent.id, tools: reads, brief_chars: brief.length });
    member.status = 'idle';
    const t = [...this.tasks.values()].find((x) => x.owner === member.name && x.status === 'in_progress');
    if (t) await this.updateTask(null, { taskId: t.id, expectedRevision: t.revision, action: 'complete' });
    return { bot: member.name, tools: reads.length };
  }
}

async function arisWorkflow(aris) {
  const agents = await http('/agents');
  const team = new LevelUpTeamPort(agents);
  const commander = { session: { id: 'levelup-commander' } };
  const bots = Object.fromEntries(agents.filter((a) => a.id !== '01').map((a) => [a.tasks[0],
    { id: a.id, handle: a.tasks[0], name: a.name, kind: 'member' }]));
  const deps = {
    team,
    botOf: (sid) => (sid === commander.session.id ? { id: '01', handle: 'commander', name: 'Commander', kind: 'commander' } : bots[sid]),
    byHandle: (h) => bots[h],
    busyBots: () => team.members.filter((m) => m.status === 'running').length,
    record: (entry) => log('aris_dispatch_record', { bot: entry.handle, title: entry.title, taskId: entry.taskId }),
  };
  // ARIS `tao_the`: cards with dependencies (the order mirrors our task graph).
  const cards = await aris.planCards(team, commander, [
    { title: 'Phân tích thị trường PH', description: 'Đọc mock market/ads/leads/orders' },
    { title: 'Chọn sản phẩm', after: ['Phân tích thị trường PH'] },
    { title: 'Tính giá và hòa vốn', after: ['Chọn sản phẩm'] },
    { title: 'Kiểm tra QA', after: ['Tính giá và hòa vốn'] },
  ]);
  log('aris_plan_cards', { cards: cards.map((c) => ({ id: c.id, title: c.title, after: c.after })) });
  const owner = { 'Phân tích thị trường PH': 'market', 'Chọn sản phẩm': 'product', 'Tính giá và hòa vốn': 'offer', 'Kiểm tra QA': 'qa' };
  // ARIS guardrail check: a card whose dependency is not done must be refused before any bot is messaged
  const early = await aris.dispatch(deps, commander, [{ bot: 'product', task: 'Chọn sản phẩm', reason: 'thử giao sớm', card: cards[1].id }],
    new AbortController().signal);
  log('aris_guard_premature', { ok: early[0].ok, error: early[0].error, members_spawned: team.members.length });
  if (early[0].ok) throw new Error('ARIS accepted a card that was not ready');
  // deterministic Commander loop: dispatch every ready card through ARIS, wait, repeat
  for (let round = 1; round <= cards.length; round++) {
    const ready = cards.filter((c) => { const t = team.getTask(commander, c.id); return t.status === 'pending' && t.ready; });
    if (!ready.length) break;
    const results = await aris.dispatch(deps, commander, ready.map((c) => ({
      bot: owner[c.title], task: c.title, reason: `Vai trò ${owner[c.title]} trong registry LevelUp`, card: c.id })),
      new AbortController().signal);
    log('aris_dispatch', { round, results: results.map((r) => ({ handle: r.handle, ok: r.ok, taskId: r.taskId, error: r.error })) });
    if (results.some((r) => !r.ok)) throw new Error('ARIS dispatch rejected: ' + JSON.stringify(results));
    await Promise.all(team.work.splice(0).map((start) => start()));
  }
  return [...team.tasks.values()].map((t) => ({ id: t.id, subject: t.subject, owner: t.owner, status: t.status }));
}

let mode = 'aris';
let outcome;
try {
  const aris = await import(ARIS);
  log('aris_loaded', { exports: Object.keys(aris).sort() });
  outcome = await arisWorkflow(aris);
} catch (e) {
  mode = 'fallback_internal_runtime';
  log('aris_failed', { error: String(e && e.message || e) });
  const run = await http('/runs?wait=true', { method: 'POST', body: JSON.stringify({}) });
  outcome = { run_id: run.run.run_id, status: run.run.status };
}
console.log(JSON.stringify({ mode, node: process.version, platform: process.platform, outcome, trace }, null, 1));
