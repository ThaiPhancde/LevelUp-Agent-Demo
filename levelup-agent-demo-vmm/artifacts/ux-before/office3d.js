// 3D office scene (Claude). Spec: docs/DEMO_DASHBOARD_3D.md sections 2, 3 and 5.
// Contract with main.js: createOffice(container, {onSelect, autoRotate}) ->
//   { update(run), setOption(name, bool), resetCamera(), setPaused(bool), reset() }
// Built only from primitive shapes (no external assets). Labels and bubbles are real HTML (CSS2DRenderer).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/CSS2DRenderer.js';
import { ISLAND, ZONES, ROOMS, GATEWAY, MOCK_SYSTEMS, STATUS_STYLE, roomForTask } from './office-layout.js';
import { TASK_TITLE, AGENT_ROLE, RULE_LABEL, errorText } from './labels.js';

const CAMERA_HOME = new THREE.Vector3(40, 36, 40);
const SKIN = '#f3d2b5';
const BUBBLE_MS = 7000;
const DOC_SECONDS = 1.3;

// The scene owns the look of its own HTML labels (panels CSS is a separate file).
const SCENE_CSS = `
#office { position: fixed; inset: 0; }
.office-labels .office-label { font: 600 11px/1.2 system-ui, sans-serif; background: rgba(255,255,255,.92); color: #333;
  padding: 3px 8px; border-radius: 999px; box-shadow: 0 1px 4px rgba(0,0,0,.15); white-space: nowrap; cursor: pointer; }
.office-labels .office-label[data-status="RUNNING"] { background: #fff3c4; }
.office-labels .office-label[data-status="FAILED"] { background: #ffd6d6; color: #8b0000; }
.office-labels .office-label[data-status="COMPLETED"] { background: #dff3e1; }
.office-labels .office-label--gateway, .office-labels .office-label--mock { background: #ececec; cursor: default; }
.office-labels .office-bubble { font: 12px/1.35 system-ui, sans-serif; max-width: 220px; background: #fff; color: #222;
  padding: 6px 10px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.18); cursor: pointer; }
.office-labels .office-bubble[data-status="FAILED"], .office-labels .office-bubble--alert { background: #ffe1e1; color: #8b0000; }
.office--no-labels .office-label { display: none; }
`;
document.head.appendChild(Object.assign(document.createElement('style'), { textContent: SCENE_CSS }));

let PROPS = {};
try { ({ PROPS } = await import('./office-props.js')); } catch { PROPS = {}; } // decorations are optional

function std(color, extra = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.75, metalness: 0.05, ...extra });
}

function mesh(geometry, material, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(geometry, material);
  m.position.set(x, y, z);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function lighten(hex, t) {
  return '#' + new THREE.Color(hex).lerp(new THREE.Color('#ffffff'), t).getHexString();
}

function label(text, className) {
  const div = document.createElement('div');
  div.className = className;
  div.textContent = text;
  return div;
}

function propMesh(item) {
  const [a, b, c] = item.size;
  let geo, y = item.pos[1];
  if (item.shape === 'box') { geo = new THREE.BoxGeometry(a, b, c); y += b / 2; }
  else if (item.shape === 'cylinder') { geo = new THREE.CylinderGeometry(a, a, b, 16); y += b / 2; }
  else if (item.shape === 'cone') { geo = new THREE.ConeGeometry(a, b, 16); y += b / 2; }
  else { geo = new THREE.SphereGeometry(a, 16, 12); y += a; }
  return mesh(geo, std(item.color), item.pos[0], y, item.pos[2]);
}

export function createOffice(container, { onSelect = () => {}, autoRotate = true } = {}) {
  // ---- renderer, camera, controls -------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  Object.assign(labels.domElement.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
  labels.domElement.className = 'office-labels';
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#f6f1e7');
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 400);
  camera.position.copy(CAMERA_HOME);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minPolarAngle = 0.45;
  controls.maxPolarAngle = 1.25;
  controls.minDistance = 25;
  controls.maxDistance = 95;
  controls.autoRotate = autoRotate;
  controls.autoRotateSpeed = 0.5;

  scene.add(new THREE.HemisphereLight('#ffffff', '#d8cfb8', 1.0));
  const sun = new THREE.DirectionalLight('#fff6e5', 1.3);
  sun.position.set(18, 30, 12);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 26, bottom: -26 });
  scene.add(sun);

  // ---- island and walkways --------------------------------------------------------------------
  const half = ISLAND.size / 2;
  scene.add(mesh(new THREE.BoxGeometry(ISLAND.size, ISLAND.height, ISLAND.size), std(ISLAND.color), 0, -ISLAND.height / 2, 0));
  scene.add(mesh(new THREE.BoxGeometry(ISLAND.size - 1, 0.06, ISLAND.size - 1), std(ISLAND.grass), 0, 0.03, 0));
  const pathMat = std('#f7efdc');
  for (const r of [...ROOMS.filter((x) => !x.tower), { x: GATEWAY.x, z: GATEWAY.z }]) {
    const len = Math.hypot(r.x, r.z);
    const p = mesh(new THREE.BoxGeometry(0.9, 0.04, len), pathMat, r.x / 2, 0.08, r.z / 2);
    p.rotation.y = Math.atan2(r.x, r.z);
    scene.add(p);
  }

  // ---- rooms ----------------------------------------------------------------------------------
  const clickables = [];
  const rooms = {};
  for (const r of ROOMS) {
    const zone = ZONES[r.zone];
    const g = new THREE.Group();
    g.position.set(r.x, 0, r.z);
    const mats = [];
    const own = (m) => { mats.push(m); return m; };
    const glass = r.zone === 'supervision';
    g.add(mesh(new THREE.BoxGeometry(r.w, 0.16, r.d), own(std(lighten(zone.color, 0.55))), 0, 0.08, 0));
    const wallMat = own(std(glass ? '#cfe8f3' : '#fffaf0', glass ? { transparent: true, opacity: 0.45 } : {}));
    g.add(mesh(new THREE.BoxGeometry(r.w, 1.5, 0.16), wallMat, 0, 0.9, -r.d / 2 + 0.08));
    g.add(mesh(new THREE.BoxGeometry(0.16, 1.5, r.d), wallMat, -r.w / 2 + 0.08, 0.9, 0));
    g.add(mesh(new THREE.BoxGeometry(r.w, 0.22, 0.18), own(std(zone.color)), 0, 1.75, -r.d / 2 + 0.08)); // accent stripe

    if (r.tower) { // Commander: glass tower with a roof and a flag, the plan board, a bell for approvals
      g.add(mesh(new THREE.CylinderGeometry(1.6, 1.8, 4.2, 8), own(std('#e9f2f7', { transparent: true, opacity: 0.6 })), -1.6, 2.2, -1.6));
      g.add(mesh(new THREE.ConeGeometry(2.0, 1.6, 8), own(std(zone.color)), -1.6, 5.1, -1.6));
      g.add(mesh(new THREE.BoxGeometry(2.6, 1.4, 0.12), own(std('#ffffff')), 1.4, 1.2, -3.2));
    }
    const desk = mesh(new THREE.BoxGeometry(1.3, 0.7, 0.7), own(std('#c8a27a')), 0, 0.5, 0.25);
    const screen = mesh(new THREE.BoxGeometry(0.7, 0.45, 0.06), own(std('#2f3b4a', { emissive: '#000000' })), 0, 1.1, 0.12);
    const body = mesh(new THREE.CapsuleGeometry(0.28, 0.45, 4, 12), own(std(zone.color)), 0, 0.75, -0.45);
    const head = mesh(new THREE.SphereGeometry(0.26, 16, 12), own(std(SKIN)), 0, 1.45, -0.45);
    const ring = mesh(new THREE.RingGeometry(0.55, 0.75, 32), own(std(STATUS_STYLE.PENDING.color, { emissive: '#000000', side: THREE.DoubleSide })), 0, 0.18, -0.45);
    ring.rotation.x = -Math.PI / 2;
    ring.castShadow = false;
    g.add(desk, screen, body, head, ring);
    for (const item of PROPS[r.agentId] || []) g.add(propMesh(item));

    const nameEl = label('', 'office-label');
    const name = new CSS2DObject(nameEl);
    name.position.set(0, 2.25, 0);
    const bubbleEl = label('', 'office-bubble');
    bubbleEl.hidden = true;
    const bubble = new CSS2DObject(bubbleEl);
    bubble.position.set(0, 3.1, 0);
    g.add(name, bubble);
    for (const el of [nameEl, bubbleEl]) {
      el.style.pointerEvents = 'auto';
      el.addEventListener('click', () => onSelect(rooms[r.agentId].focusTask));
    }
    g.traverse((o) => { if (o.isMesh) { o.userData.agentId = r.agentId; clickables.push(o); } });
    scene.add(g);
    rooms[r.agentId] = { r, g, mats, screen, body, head, ring, nameEl, bubbleEl, status: 'PENDING',
                         focusTask: r.taskKeys[0], bubbleUntil: 0, baseY: body.position.y };
    nameEl.textContent = `${STATUS_STYLE.PENDING.icon} ${AGENT_ROLE[r.agentId] || r.agentId}`;
  }

  // ---- gateway and mock systems ---------------------------------------------------------------
  const gate = new THREE.Group();
  gate.position.set(GATEWAY.x, 0, GATEWAY.z);
  for (const item of PROPS.gateway || []) gate.add(propMesh(item));
  const gateLight = mesh(new THREE.SphereGeometry(0.35, 16, 12), std('#4caf50', { emissive: '#1b5e20' }), 0, 2.9, 0);
  gate.add(gateLight);
  const gateBubbleEl = label('', 'office-bubble office-bubble--alert');
  gateBubbleEl.hidden = true;
  const gateName = new CSS2DObject(label(GATEWAY.label, 'office-label office-label--gateway'));
  gateName.position.set(0, 3.6, 0);
  const gateBubble = new CSS2DObject(gateBubbleEl);
  gateBubble.position.set(0, 4.6, 0);
  gate.add(gateName, gateBubble);
  scene.add(gate);
  for (const s of MOCK_SYSTEMS) {
    const h = new THREE.Group();
    h.position.set(s.x, 0, s.z);
    h.add(mesh(new THREE.BoxGeometry(2.2, 1.6, 2.2), std('#e6e2da'), 0, 0.8, 0));
    const roof = mesh(new THREE.ConeGeometry(1.8, 1.1, 4), std(ZONES.gateway.color), 0, 2.15, 0);
    roof.rotation.y = Math.PI / 4;
    h.add(roof);
    const t = new CSS2DObject(label(s.label, 'office-label office-label--mock'));
    t.position.set(0, 3.0, 0);
    h.add(t);
    scene.add(h);
  }
  const bell = mesh(new THREE.ConeGeometry(0.45, 0.7, 12), std('#ffca28', { emissive: '#6d4c00' }), -1.6, 6.3, -1.6);
  bell.visible = false;
  rooms['01'].g.add(bell);

  // ---- hand-off documents ---------------------------------------------------------------------
  const docs = [];
  const docGeo = new THREE.BoxGeometry(0.5, 0.06, 0.38);
  function flyDoc(from, to, color) {
    const m = mesh(docGeo, std(color, { emissive: color, emissiveIntensity: 0.25 }));
    m.castShadow = false;
    const a = new THREE.Vector3(from.x, 1.6, from.z);
    const b = new THREE.Vector3(to.x, 1.6, to.z);
    const mid = a.clone().lerp(b, 0.5);
    mid.y = 4 + a.distanceTo(b) * 0.18;
    docs.push({ m, curve: new THREE.QuadraticBezierCurve3(a, mid, b), t: 0 });
    scene.add(m);
  }

  // ---- state -> look --------------------------------------------------------------------------
  let lastStatus = {};
  let lastActions = new Set();
  let showBubbles = true;

  function roomStatus(r, byKey) {
    // Commander room shows the summary once the plan is done and the summary has started
    const keys = r.taskKeys.filter((k) => byKey[k]);
    const active = keys.filter((k) => byKey[k].status !== 'PENDING');
    const key = active.length ? active[active.length - 1] : keys[0];
    return { key, task: byKey[key] };
  }

  function bubbleText(task, byKey) {
    const s = task.status;
    if (s === 'FAILED') return `Lỗi: ${errorText(task.error)}`;
    if (s === 'SKIPPED') return `Bỏ qua: ${errorText(task.error)}`;
    if (s === 'CANCELLED') return 'Đã hủy';
    if (s === 'RUNNING') return `Đang làm: ${TASK_TITLE[task.task_key] || task.task_key}…`;
    if (s === 'COMPLETED') return (task.artifact?.summary || 'Xong').slice(0, 90);
    const waiting = task.depends_on.filter((d) => byKey[d] && byKey[d].status !== 'COMPLETED');
    return waiting.length ? `Chờ: ${waiting.slice(0, 2).map((d) => TASK_TITLE[d] || d).join(', ')}${waiting.length > 2 ? '…' : ''}` : 'Sẵn sàng';
  }

  function paint(room, status) {
    const st = STATUS_STYLE[status] || STATUS_STYLE.PENDING;
    room.ring.material.color.set(st.color);
    room.ring.material.emissive.set(st.color).multiplyScalar(st.light * 0.6);
    room.screen.material.emissive.set(status === 'RUNNING' ? '#5fb3ff' : status === 'FAILED' ? '#ff5252' : '#000000');
    for (const m of room.mats) {
      if (m === room.ring.material) continue;
      const glassy = m.userData.glassOpacity ?? (m.userData.glassOpacity = m.transparent ? m.opacity : 1);
      m.transparent = st.opacity < 1 || glassy < 1;
      m.opacity = Math.min(glassy, st.opacity);
    }
  }

  function update(run) {
    const byKey = Object.fromEntries(run.tasks.map((t) => [t.task_key, t]));
    const now = performance.now();
    for (const room of Object.values(rooms)) {
      const { key, task } = roomStatus(room.r, byKey);
      if (!task) continue;
      room.focusTask = key;
      if (task.status !== room.status) {
        room.status = task.status;
        paint(room, task.status);
        room.bubbleUntil = task.status === 'COMPLETED' ? now + BUBBLE_MS
          : (task.status === 'RUNNING' || task.status === 'FAILED') ? Infinity : 0;
      }
      room.nameEl.textContent = `${STATUS_STYLE[task.status].icon} ${AGENT_ROLE[room.r.agentId] || room.r.agentId}`;
      room.nameEl.dataset.status = task.status;
      room.bubbleEl.textContent = bubbleText(task, byKey);
      room.bubbleEl.dataset.status = task.status;
    }
    // hand-offs: a task that just completed sends its artifact to every task that depends on it
    for (const t of run.tasks) {
      if (t.status === 'COMPLETED' && lastStatus[t.task_key] && lastStatus[t.task_key] !== 'COMPLETED') {
        const from = roomForTask(t.task_key);
        for (const d of run.tasks.filter((x) => x.depends_on.includes(t.task_key))) {
          const to = roomForTask(d.task_key);
          if (to !== from) flyDoc(from, to, ZONES[from.zone].color);
        }
      }
    }
    // gateway: every executed action flies to the gate; blocked ones are red
    let blocked = false;
    for (const t of run.tasks) {
      for (const [i, a] of (t.artifact?.action_results || []).entries()) {
        const id = `${t.task_key}:${t.attempt}:${i}`;
        const isBlock = a.decision === 'BLOCK';
        blocked ||= isBlock;
        if (!lastActions.has(id) && Object.keys(lastStatus).length) {
          flyDoc(roomForTask(t.task_key), GATEWAY, isBlock ? '#e53935' : a.decision === 'NEEDS_APPROVAL' ? '#ffb300' : '#9aa0a6');
        }
        lastActions.add(id);
      }
    }
    gateLight.material.color.set(blocked ? '#e53935' : '#4caf50');
    gateLight.material.emissive.set(blocked ? '#7f0000' : '#1b5e20');
    gateBubbleEl.textContent = blocked ? 'Đã chặn lệnh đăng quảng cáo thật, chiến dịch giữ bản nháp' : '';
    gateBubbleEl.hidden = !blocked || !showBubbles;
    const pending = (run.approvals || []).some((a) => a.status === 'PENDING');
    bell.visible = pending;
    if (pending) {
      rooms['01'].bubbleEl.textContent = 'Chờ người duyệt chiến dịch vượt ngưỡng';
      rooms['01'].bubbleUntil = Infinity;
    }
    const qa = run.engines?.qa;
    if (qa && qa.status === 'FAIL' && rooms['11'].status === 'COMPLETED') {
      const f = qa.findings.find((x) => x.severity === 'FAIL');
      rooms['11'].bubbleEl.textContent = `Không đạt: ${f ? (RULE_LABEL[f.rule] || f.rule) : ''}`.slice(0, 110);
      rooms['11'].bubbleUntil = Infinity;
    }
    lastStatus = Object.fromEntries(run.tasks.map((t) => [t.task_key, t.status]));
  }

  // ---- interaction ----------------------------------------------------------------------------
  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let down = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return; // it was a drag
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    ray.setFromCamera(pointer, camera);
    const hit = ray.intersectObjects(clickables, false)[0];
    if (hit) onSelect(rooms[hit.object.userData.agentId].focusTask);
  });

  function resize() {
    const w = container.clientWidth || window.innerWidth;
    const h = container.clientHeight || window.innerHeight;
    renderer.setSize(w, h);
    labels.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();

  // ---- loop -----------------------------------------------------------------------------------
  let paused = false;
  let last = performance.now();
  let fps = 60;
  function frame(now) {
    requestAnimationFrame(frame);
    if (paused) return;
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    fps = fps * 0.95 + (dt > 0 ? 1 / dt : 60) * 0.05;
    window.__officeFps = Math.round(fps);
    const time = now / 1000;
    for (const room of Object.values(rooms)) {
      const working = room.status === 'RUNNING';
      const bob = working ? Math.abs(Math.sin(time * 6)) * 0.12 : 0;
      room.body.position.y = room.baseY + bob;
      room.head.position.y = room.baseY + 0.7 + bob;
      room.bubbleEl.hidden = !showBubbles || !room.bubbleEl.textContent || now > room.bubbleUntil;
    }
    if (bell.visible) bell.rotation.z = Math.sin(time * 10) * 0.35;
    for (let i = docs.length - 1; i >= 0; i--) {
      const d = docs[i];
      d.t += dt / DOC_SECONDS;
      if (d.t >= 1) { scene.remove(d.m); d.m.material.dispose(); docs.splice(i, 1); continue; }
      d.m.position.copy(d.curve.getPoint(d.t));
      d.m.rotation.y += dt * 4;
    }
    controls.update();
    renderer.render(scene, camera);
    labels.render(scene, camera);
  }
  requestAnimationFrame(frame);

  return {
    update,
    setOption(name, value) {
      if (name === 'rotate') controls.autoRotate = !!value;
      if (name === 'labels') container.classList.toggle('office--no-labels', !value);
      if (name === 'bubbles') showBubbles = !!value;
    },
    resetCamera() { camera.position.copy(CAMERA_HOME); controls.target.set(0, 0, 0); controls.update(); },
    setPaused(v) { paused = !!v; last = performance.now(); },
    reset() {
      lastStatus = {};
      lastActions = new Set();
      for (const room of Object.values(rooms)) { room.status = ''; room.bubbleUntil = 0; }
    },
  };
}
