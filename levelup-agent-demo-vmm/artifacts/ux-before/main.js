// Dashboard wiring (Claude): REST calls, polling, and the link between the 3D office and the panels.
// panels.js (Gemini) owns the DOM controls; office3d.js (Claude) owns the canvas inside #office.
import { createPanels } from './panels.js';

const POLL_MS = 1000;
const ACTIVE = new Set(['PENDING', 'RUNNING']);
let runId = null;
let timer = null;
let office = null;

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { 'content-type': 'application/json' }, ...options });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  return body;
}

function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch { return false; }
}

const params = new URLSearchParams(location.search);
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const want3d = params.get('mode') !== '2d' && webglAvailable();

const panels = createPanels(document.getElementById('app'), {
  async onStart({ objective, mode, inject }) {
    try {
      const body = await api('/runs', { method: 'POST', body: JSON.stringify({ objective, mode, inject }) });
      office?.reset();
      follow(body.run_id);
    } catch (e) { panels.showError(e.message); }
  },
  async onRetry(taskKey) {
    try { await api(`/runs/${runId}/tasks/${taskKey}/retry`, { method: 'POST' }); follow(runId); }
    catch (e) { panels.showError(e.message); }
  },
  async onCancel() {
    try { await api(`/runs/${runId}/cancel`, { method: 'POST' }); follow(runId); }
    catch (e) { panels.showError(e.message); }
  },
  async onApprove(approvalId, decision) {
    try {
      await api(`/runs/${runId}/approvals/${approvalId}`, { method: 'POST', body: JSON.stringify({ decision }) });
      follow(runId);
    } catch (e) { panels.showError(e.message); }
  },
  onOpenRun(id) { office?.reset(); follow(id); },        // replay: read-only GET, no agent runs again
  onToggle(option, value) { office?.setOption(option, value); },
  onResetCamera() { office?.resetCamera(); },
  onView(mode) { document.body.dataset.view = mode; office?.setPaused(mode !== '3d'); },
  async onRefreshHistory() { panels.renderHistory(await api('/runs?limit=30').catch(() => [])); },
});

function follow(id) {
  runId = id;
  clearTimeout(timer);
  const tick = async () => {
    try {
      const run = await api(`/runs/${id}`);
      if (id !== runId) return;                  // user switched run meanwhile
      panels.render(run);
      office?.update(run);
      if (ACTIVE.has(run.run.status)) timer = setTimeout(tick, POLL_MS);
      else panels.renderHistory(await api('/runs?limit=30').catch(() => []));
    } catch (e) {
      panels.showError(e.message);
      timer = setTimeout(tick, POLL_MS * 3);
    }
  };
  tick();
}

async function boot() {
  panels.setAgents(await api('/agents').catch(() => []));
  panels.renderHistory(await api('/runs?limit=30').catch(() => []));
  if (want3d) {
    try {
      const { createOffice } = await import('./office3d.js');
      office = createOffice(document.getElementById('office'), {
        onSelect: (taskKey) => panels.selectTask(taskKey),
        autoRotate: !reducedMotion,
      });
    } catch (e) {
      console.error(e);
      office = null;
    }
  }
  const view = office ? '3d' : '2d';
  document.body.dataset.view = view;
  panels.setView(view);
  if (want3d && !office) panels.showError('Không tải được chế độ 3D, đang dùng chế độ Tổng quan 2D.');
  const latest = (await api('/runs?limit=1').catch(() => []))[0];
  if (latest) follow(latest.run_id);
}

boot();
