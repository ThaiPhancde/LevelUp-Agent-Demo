// 3D office scene (Claude + Gemini redesign inspired by khanh020905/my-office).
// Unified zero-gap rectangular office floorplate + Orange & White theme + City street crosswalk backdrop.
// Contract with main.js: createOffice(container, {onSelect, autoRotate}) ->
//   { update(run), setOption(name, bool), resetCamera(), setPaused(bool), reset() }
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/CSS2DRenderer.js';
import { ISLAND, ZONES, ROOMS, GATEWAY, MOCK_SYSTEMS, STATUS_STYLE, roomForTask } from './office-layout.js';
import { TASK_TITLE, AGENT_ROLE, RULE_LABEL, errorText } from './labels.js';

// Isometric diagonal camera angle inspired by khanh020905/my-office
const CAMERA_HOME = new THREE.Vector3(23.5, 32.5, 29.5);
const CAMERA_TARGET = new THREE.Vector3(0.8, 0.0, 0.0);
const SKIN = '#f4d1b4';
const BUBBLE_MS = 5500;
const DOC_SECONDS = 1.3;

// Orange & White primary architectural palette (Chủ đề Cam & Trắng)
const BRAND_ORANGE = '#f97316';
const BRAND_ORANGE_DARK = '#ea580c';
const WALL_WHITE = '#ffffff';
const WALL_CAP = '#ea580c';
const WALL_SKIRT = '#fed7aa';
const MULLION_DARK = '#272b33';
const HAIR_PALETTE = ['#231b18', '#4a2e1b', '#1e242b', '#5c3820', '#2c221e', '#693220', '#1b2028'];

// The scene owns the look of its own HTML labels (panels CSS is a separate file).
const SCENE_CSS = `
#office { position: fixed; }
.office-labels .office-label {
  font: 600 10.5px/1.2 "Segoe UI", system-ui, sans-serif;
  background: rgba(255, 255, 255, 0.97);
  color: #1c1917;
  padding: 3px 9px;
  border-radius: 999px;
  border: 1.5px solid #fdba74;
  border-left: 4px solid #ea580c;
  box-shadow: 0 3px 10px rgba(234, 88, 12, 0.16);
  white-space: nowrap;
  cursor: pointer;
  letter-spacing: -0.01em;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}
.office-labels .office-label[data-status="RUNNING"] {
  background: #ea580c;
  color: #ffffff;
  border-color: #fff7ed;
  box-shadow: 0 4px 12px rgba(234, 88, 12, 0.42);
}
.office-labels .office-label[data-status="FAILED"] {
  background: #fef2f2;
  color: #991b1b;
  border-color: #ef4444;
  box-shadow: 0 3px 10px rgba(239, 68, 68, 0.28);
}
.office-labels .office-label[data-status="COMPLETED"] {
  background: #fff7ed;
  color: #c2410c;
  border-color: #f97316;
}
.office-labels .office-label--gateway, .office-labels .office-label--mock {
  font-size: 10px;
  background: #18181b;
  color: #ffffff;
  border-color: #f97316;
  border-left: 3px solid #ea580c;
  cursor: default;
}
.office-labels .office-bubble {
  font: 500 11.5px/1.35 "Segoe UI", system-ui, sans-serif;
  max-width: 215px;
  background: rgba(255, 255, 255, 0.98);
  color: #1c1917;
  padding: 5px 9px;
  border-radius: 10px;
  border: 1.5px solid #ea580c;
  box-shadow: 0 6px 16px rgba(234, 88, 12, 0.20);
  cursor: pointer;
}
.office-labels .office-bubble[data-status="FAILED"], .office-labels .office-bubble--alert {
  background: #fef2f2;
  color: #991b1b;
  border-color: #ef4444;
}
.office--no-labels .office-label { display: none; }
`;
document.head.appendChild(Object.assign(document.createElement('style'), { textContent: SCENE_CSS }));

let PROPS = {};
try { ({ PROPS } = await import('./office-props.js')); } catch { PROPS = {}; } // decorations are optional

function std(color, extra = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.06, ...extra });
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

// ---- Procedural Canvas Textures (inspired by khanh020905/my-office/src/office/scene/blocks.js) ----
function canvasTex(draw, w = 256, h = 256, rx = 1, ry = 1) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const ctx = c.getContext && c.getContext('2d');
  if (ctx) draw(ctx, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (rx > 1 || ry > 1) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(rx, ry);
  }
  return t;
}

function gridTex(bg, line, step = 32, rx = 6, ry = 6, checker = null) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);
    if (checker) {
      for (let x = 0; x < w; x += step) {
        for (let y = 0; y < h; y += step) {
          if (((x + y) / step) % 2 === 1) {
            ctx.fillStyle = checker;
            ctx.fillRect(x, y, step, step);
          }
        }
      }
    }
    ctx.strokeStyle = line;
    ctx.lineWidth = 2;
    for (let x = 0; x <= w; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y <= h; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }
  }, 256, 256, rx, ry);
}

function plankTex(base, line, rx = 6, ry = 6) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = line;
    ctx.lineWidth = 2;
    const rows = 8;
    const rh = h / rows;
    for (let i = 0; i <= rows; i++) {
      const y = i * rh;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
      const jointX = ((i * 97) % (w - 40)) + 20;
      ctx.beginPath(); ctx.moveTo(jointX, y); ctx.lineTo(jointX, Math.min(h, y + rh)); ctx.stroke();
    }
  }, 256, 256, rx, ry);
}

function speckTex(base, s1, s2, rx = 3, ry = 3) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < 220; i++) {
      ctx.fillStyle = i % 2 === 0 ? s1 : s2;
      const x = (i * 73) % w;
      const y = (i * 139) % h;
      ctx.fillRect(x, y, 3, 3);
    }
  }, 256, 256, rx, ry);
}

function sprintBoardTex(zoneColor, agentId) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = BRAND_ORANGE_DARK;
    ctx.fillRect(0, 0, w, 24);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 14px "Segoe UI", sans-serif';
    ctx.fillText(`SPRINT BOARD · P.${agentId}`, 12, 17);
    ctx.strokeStyle = '#ffedd5';
    ctx.lineWidth = 2;
    for (let c = 1; c < 3; c++) {
      ctx.beginPath(); ctx.moveTo((w / 3) * c, 28); ctx.lineTo((w / 3) * c, h - 8); ctx.stroke();
    }
    const notes = ['#fed7aa', '#ffedd5', '#fdba74', '#fb923c', '#fde68a', '#fff7ed'];
    for (let c = 0; c < 3; c++) {
      for (let r = 0; r < 2; r++) {
        ctx.fillStyle = notes[(c * 2 + r + Number(agentId)) % notes.length];
        const nx = c * (w / 3) + 12 + (r * 7);
        const ny = 36 + r * 40;
        ctx.fillRect(nx, ny, 56, 30);
        ctx.fillStyle = 'rgba(234, 88, 12, 0.35)';
        ctx.fillRect(nx + 6, ny + 8, 42, 3);
        ctx.fillRect(nx + 6, ny + 16, 30, 3);
      }
    }
    void zoneColor;
  }, 256, 128);
}

function doorPlaqueTex(agentId, roleTitle, zoneColor) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = '#18181b';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = zoneColor || BRAND_ORANGE_DARK;
    ctx.fillRect(0, 0, 22, h);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 24px "Segoe UI", sans-serif';
    ctx.fillText(`P.${agentId}`, 34, 34);
    ctx.fillStyle = '#fdba74';
    ctx.font = '600 15px "Segoe UI", sans-serif';
    ctx.fillText(String(roleTitle || '').slice(0, 18), 34, 58);
  }, 256, 76);
}

function monitorScreenTex(zoneColor) {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = '#18181b';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = BRAND_ORANGE_DARK;
    ctx.fillRect(0, 0, w, 16);
    ctx.fillStyle = '#27272a';
    ctx.fillRect(10, 24, 96, 44);
    ctx.fillRect(114, 24, 132, 44);
    const bars = ['#ea580c', '#f97316', '#fb923c', '#fdba74', zoneColor || '#ea580c'];
    for (let i = 0; i < 5; i++) {
      ctx.fillStyle = bars[i];
      const bh = 22 + ((i * 17) % 36);
      ctx.fillRect(16 + i * 44, 118 - bh, 30, bh);
    }
  }, 256, 128);
}

function brandSignTex() {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = '#18181b';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = BRAND_ORANGE_DARK;
    ctx.fillRect(0, 0, 18, h);
    ctx.fillStyle = BRAND_ORANGE_DARK;
    ctx.fillRect(38, 26, 44, 44);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 30px "Segoe UI", sans-serif';
    ctx.fillText('LU', 43, 59);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 40px "Segoe UI", sans-serif';
    ctx.fillText('LEVEL UP OFFICE', 100, 56);
    ctx.fillStyle = '#fdba74';
    ctx.font = '600 18px "Segoe UI", sans-serif';
    ctx.fillText('13 AI AGENTS · PURCHASING & GROWTH', 102, 82);
  }, 512, 104);
}

function statusWallTex() {
  return canvasTex((ctx, w, h) => {
    ctx.fillStyle = '#18181b';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = BRAND_ORANGE_DARK;
    ctx.fillRect(0, 0, w, 12);
    ctx.fillStyle = '#f97316';
    ctx.font = 'bold 44px "Segoe UI", sans-serif';
    ctx.fillText('13/13', 24, 72);
    ctx.fillStyle = '#ffffff';
    ctx.font = '600 20px "Segoe UI", sans-serif';
    ctx.fillText('AI AGENTS READY · MOCK SAFE', 160, 52);
    ctx.fillStyle = '#3f3f46';
    ctx.fillRect(160, 68, 310, 16);
    ctx.fillStyle = '#ea580c';
    ctx.fillRect(160, 68, 285, 16);
    for (let i = 0; i < 8; i++) {
      ctx.fillStyle = i % 2 === 0 ? '#ea580c' : '#fb923c';
      const bh = 24 + ((i * 19) % 42);
      ctx.fillRect(28 + i * 56, 152 - bh, 36, bh);
    }
  }, 512, 176);
}

function propMesh(item, baseY = 0.2, own = (m) => m) {
  const [a, b, c] = item.size;
  let geo, y = item.pos[1] + baseY;
  if (item.shape === 'box') { geo = new THREE.BoxGeometry(a, b, c); y += b / 2; }
  else if (item.shape === 'cylinder') { geo = new THREE.CylinderGeometry(a, a, b, 16); y += b / 2; }
  else if (item.shape === 'cone') { geo = new THREE.ConeGeometry(a, b, 16); y += b / 2; }
  else { geo = new THREE.SphereGeometry(a, 16, 12); y += a; }
  return mesh(geo, own(std(item.color)), item.pos[0], y, item.pos[2]);
}

// ---- Architectural Wall, Plant, Chair & Chibi Helpers (Orange & White theme) ----
function addCutawayWall(g, own, w, h, d, x, y, z, accentColor = BRAND_ORANGE_DARK) {
  g.add(mesh(new THREE.BoxGeometry(w, h, d), own(std(WALL_WHITE, { roughness: 0.72 })), x, y, z));
  // Orange architectural section cut-cap on top
  g.add(mesh(new THREE.BoxGeometry(w + 0.01, 0.055, d + 0.01), own(std(accentColor, { roughness: 0.45 })), x, y + h / 2 + 0.025, z));
  // Warm orange baseboard skirting
  g.add(mesh(new THREE.BoxGeometry(w + 0.015, 0.07, d + 0.015), own(std(WALL_SKIRT, { roughness: 0.70 })), x, y - h / 2 + 0.035, z));
}

function addFramedGlassWall(g, own, len, h, x, y, z, alongZ = true) {
  const w = alongZ ? 0.05 : len;
  const d = alongZ ? len : 0.05;
  const glassMat = own(std('#fff7ed', { transparent: true, opacity: 0.25, roughness: 0.12, metalness: 0.10 }));
  const frostMat = own(std('#ffffff', { transparent: true, opacity: 0.52, roughness: 0.35 }));
  const frameMat = own(std(MULLION_DARK, { roughness: 0.42, metalness: 0.35 }));
  const orangeRailMat = own(std(BRAND_ORANGE_DARK, { roughness: 0.40 }));
  g.add(mesh(new THREE.BoxGeometry(w, h, d), glassMat, x, y, z));
  g.add(mesh(new THREE.BoxGeometry(alongZ ? 0.056 : len, h * 0.24, alongZ ? len : 0.056), frostMat, x, y - h * 0.32, z));
  // Top orange rail & bottom dark rail
  g.add(mesh(new THREE.BoxGeometry(alongZ ? 0.08 : len + 0.04, 0.055, alongZ ? len + 0.04 : 0.08), orangeRailMat, x, y + h / 2 + 0.02, z));
  g.add(mesh(new THREE.BoxGeometry(alongZ ? 0.08 : len + 0.04, 0.05, alongZ ? len + 0.04 : 0.08), frameMat, x, y - h / 2 + 0.025, z));
  // Vertical mullions
  for (const t of [-0.48, 0, 0.48]) {
    const mx = alongZ ? x : x + len * t;
    const mz = alongZ ? z + len * t : z;
    g.add(mesh(new THREE.BoxGeometry(0.06, h + 0.04, 0.06), frameMat, mx, y, mz));
  }
}

function addPotPlant(g, own, x, y, z, kind = 'monstera') {
  const potMat = own(std('#ffffff', { roughness: 0.50 }));
  const rimMat = own(std(BRAND_ORANGE_DARK, { roughness: 0.50 }));
  const soilMat = own(std('#4a3b2c', { roughness: 0.9 }));
  const leafDark = own(std('#2d6a4f', { roughness: 0.6 }));
  const leafMid = own(std('#40916c', { roughness: 0.55 }));
  const leafLight = own(std('#52b788', { roughness: 0.55 }));

  g.add(mesh(new THREE.CylinderGeometry(0.18, 0.14, 0.28, 12), potMat, x, y + 0.14, z));
  g.add(mesh(new THREE.CylinderGeometry(0.19, 0.19, 0.04, 12), rimMat, x, y + 0.27, z));
  g.add(mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.03, 10), soilMat, x, y + 0.28, z));

  if (kind === 'snake') {
    for (let i = 0; i < 5; i++) {
      const ang = (i / 5) * Math.PI * 2;
      const blade = mesh(new THREE.BoxGeometry(0.06, 0.46 + (i % 2) * 0.12, 0.02), i % 2 ? leafDark : leafLight,
        x + Math.cos(ang) * 0.06, y + 0.48, z + Math.sin(ang) * 0.06);
      blade.rotation.y = ang;
      blade.rotation.z = 0.08;
      g.add(blade);
    }
  } else if (kind === 'bush') {
    g.add(mesh(new THREE.SphereGeometry(0.21, 10, 8), leafDark, x, y + 0.44, z));
    g.add(mesh(new THREE.SphereGeometry(0.15, 10, 8), leafMid, x + 0.08, y + 0.54, z + 0.05));
    g.add(mesh(new THREE.SphereGeometry(0.14, 10, 8), leafLight, x - 0.07, y + 0.52, z - 0.05));
  } else {
    for (let i = 0; i < 5; i++) {
      const ang = (i / 5) * Math.PI * 2 + 0.3;
      const leaf = mesh(new THREE.BoxGeometry(0.19, 0.03, 0.25), i % 2 ? leafMid : leafDark,
        x + Math.cos(ang) * 0.11, y + 0.42 + (i % 3) * 0.06, z + Math.sin(ang) * 0.11);
      leaf.rotation.y = ang;
      leaf.rotation.x = 0.32;
      g.add(leaf);
    }
  }
}

function addSwivelChair(g, own, x, baseY, z, jacketColor) {
  const frameMat = own(std('#22262c', { roughness: 0.45, metalness: 0.35 }));
  const cushionMat = own(std('#ffffff', { roughness: 0.65 }));
  const jacketMat = own(std(jacketColor || BRAND_ORANGE_DARK, { roughness: 0.65 }));

  for (let i = 0; i < 5; i++) {
    const a = (i * Math.PI * 2) / 5;
    const leg = mesh(new THREE.BoxGeometry(0.24, 0.025, 0.035), frameMat,
      x + Math.cos(a) * 0.11, baseY + 0.03, z + Math.sin(a) * 0.11);
    leg.rotation.y = -a;
    g.add(leg);
  }
  g.add(mesh(new THREE.CylinderGeometry(0.03, 0.035, 0.22, 10), frameMat, x, baseY + 0.14, z));
  g.add(mesh(new THREE.BoxGeometry(0.46, 0.065, 0.44), jacketMat, x, baseY + 0.26, z));
  g.add(mesh(new THREE.BoxGeometry(0.44, 0.48, 0.065), cushionMat, x, baseY + 0.52, z - 0.20));
  g.add(mesh(new THREE.BoxGeometry(0.06, 0.34, 0.04), frameMat, x, baseY + 0.38, z - 0.235));
  g.add(mesh(new THREE.BoxGeometry(0.045, 0.03, 0.26), frameMat, x - 0.24, baseY + 0.40, z - 0.04));
  g.add(mesh(new THREE.BoxGeometry(0.045, 0.03, 0.26), frameMat, x + 0.24, baseY + 0.40, z - 0.04));
  g.add(mesh(new THREE.BoxGeometry(0.45, 0.22, 0.08), jacketMat, x, baseY + 0.56, z - 0.215));
}

function buildChibiAgent(own, zoneColor, idx) {
  const isWhiteShirt = idx % 2 === 1;
  const suitMat = own(std(isWhiteShirt ? '#ffffff' : BRAND_ORANGE_DARK, { roughness: 0.60 }));
  const accentMat = own(std(isWhiteShirt ? BRAND_ORANGE_DARK : '#ffffff', { roughness: 0.55 }));
  const skinMat = own(std(SKIN, { roughness: 0.62 }));
  const hairColor = HAIR_PALETTE[idx % HAIR_PALETTE.length];
  const hairMat = own(std(hairColor, { roughness: 0.75 }));
  const darkMat = own(std('#1e242b', { roughness: 0.4 }));
  const blushMat = own(std('#f4978e', { roughness: 0.7 }));
  void zoneColor;

  // Torso mesh (kept as room.body at y=0.78, z=-0.42)
  const body = mesh(new THREE.CapsuleGeometry(0.24, 0.40, 6, 14), suitMat, 0, 0.78, -0.42);
  body.add(mesh(new THREE.BoxGeometry(0.18, 0.12, 0.06), accentMat, 0, 0.16, 0.21));
  body.add(mesh(new THREE.BoxGeometry(0.06, 0.20, 0.065), own(std(BRAND_ORANGE)), 0, 0.06, 0.22));
  body.add(mesh(new THREE.BoxGeometry(0.14, 0.12, 0.32), darkMat, -0.10, -0.22, 0.14));
  body.add(mesh(new THREE.BoxGeometry(0.14, 0.12, 0.32), darkMat, 0.10, -0.22, 0.14));

  const armL = mesh(new THREE.BoxGeometry(0.11, 0.11, 0.38), suitMat, -0.26, 0.05, 0.16);
  const armR = mesh(new THREE.BoxGeometry(0.11, 0.11, 0.38), suitMat, 0.26, 0.05, 0.16);
  armL.add(mesh(new THREE.SphereGeometry(0.06, 8, 8), skinMat, 0, -0.01, 0.20));
  armR.add(mesh(new THREE.SphereGeometry(0.06, 8, 8), skinMat, 0, -0.01, 0.20));
  body.add(armL, armR);

  // Head mesh (kept as room.head at y=1.48, z=-0.42)
  const head = mesh(new THREE.SphereGeometry(0.245, 18, 14), skinMat, 0, 1.48, -0.42);
  const hairDome = mesh(new THREE.SphereGeometry(0.258, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.62), hairMat, 0, 0.03, -0.01);
  const hairBack = mesh(new THREE.BoxGeometry(0.44, 0.24, 0.18), hairMat, 0, -0.02, -0.14);
  const hairBangs = mesh(new THREE.BoxGeometry(0.38, 0.10, 0.14), hairMat, 0, 0.12, 0.17);
  head.add(hairDome, hairBack, hairBangs);

  if (idx % 3 === 1) {
    head.add(mesh(new THREE.SphereGeometry(0.095, 10, 10), hairMat, 0, 0.24, -0.14));
  } else if (idx % 3 === 2) {
    head.add(mesh(new THREE.BoxGeometry(0.12, 0.22, 0.12), hairMat, 0, -0.06, -0.24));
  }

  head.add(mesh(new THREE.SphereGeometry(0.032, 8, 8), darkMat, -0.085, 0.01, 0.225));
  head.add(mesh(new THREE.SphereGeometry(0.032, 8, 8), darkMat, 0.085, 0.01, 0.225));
  head.add(mesh(new THREE.BoxGeometry(0.065, 0.018, 0.02), hairMat, -0.085, 0.075, 0.225));
  head.add(mesh(new THREE.BoxGeometry(0.065, 0.018, 0.02), hairMat, 0.085, 0.075, 0.225));
  head.add(mesh(new THREE.SphereGeometry(0.034, 8, 8), blushMat, -0.135, -0.04, 0.20));
  head.add(mesh(new THREE.SphereGeometry(0.034, 8, 8), blushMat, 0.135, -0.04, 0.20));

  if ([0, 1, 8, 9, 10, 11, 12].includes(idx)) {
    head.add(mesh(new THREE.BoxGeometry(0.24, 0.045, 0.03), own(std(BRAND_ORANGE_DARK)), 0, 0.015, 0.235));
  }
  if ([6, 7].includes(idx)) {
    head.add(mesh(new THREE.BoxGeometry(0.52, 0.04, 0.06), own(std(BRAND_ORANGE_DARK)), 0, 0.04, 0));
    head.add(mesh(new THREE.BoxGeometry(0.03, 0.03, 0.18), darkMat, 0.23, -0.05, 0.10));
  }

  return { body, head, armL, armR };
}

// Helper to add a low-poly city car on the surrounding street (my-office backdrop style)
function addStreetCar(scene, x, z, rotY, bodyColor = BRAND_ORANGE_DARK) {
  const g = new THREE.Group();
  g.position.set(x, 0.04, z);
  g.rotation.y = rotY;
  g.add(mesh(new THREE.BoxGeometry(1.9, 0.42, 0.96), std(bodyColor, { roughness: 0.40 }), 0, 0.28, 0));
  g.add(mesh(new THREE.BoxGeometry(1.05, 0.34, 0.84), std('#ffffff', { roughness: 0.30 }), -0.08, 0.62, 0));
  g.add(mesh(new THREE.BoxGeometry(1.08, 0.26, 0.86), std('#1e293b', { roughness: 0.2 }), -0.08, 0.60, 0));
  const wheelMat = std('#18181b');
  for (const [wx, wz] of [[-0.58, -0.48], [0.58, -0.48], [-0.58, 0.48], [0.58, 0.48]]) {
    const w = mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.12, 12), wheelMat, wx, 0.18, wz);
    w.rotation.x = Math.PI / 2;
    g.add(w);
  }
  scene.add(g);
}

export function createOffice(container, { onSelect = () => {}, autoRotate = false } = {}) {
  // ---- renderer, camera, controls -------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  Object.assign(labels.domElement.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
  labels.domElement.className = 'office-labels';
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#e5e7eb');
  const camera = new THREE.PerspectiveCamera(25.5, 1, 1, 400);
  camera.position.copy(CAMERA_HOME);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(CAMERA_TARGET);
  controls.enableDamping = true;
  controls.minPolarAngle = 0.40;
  controls.maxPolarAngle = 1.25;
  controls.minDistance = 24;
  controls.maxDistance = 95;
  controls.autoRotate = false;
  controls.autoRotateSpeed = 0.45;
  void autoRotate;

  // Warm daylight + soft skylight inspired by khanh020905/my-office
  scene.add(new THREE.HemisphereLight('#fffaf2', '#fed7aa', 1.24));
  const sun = new THREE.DirectionalLight('#fff5e6', 1.42);
  sun.position.set(22, 34, 20);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.0003;
  Object.assign(sun.shadow.camera, { left: -24, right: 24, top: 24, bottom: -24 });
  scene.add(sun);
  const fillLight = new THREE.DirectionalLight('#ffedd5', 0.38);
  fillLight.position.set(-16, 18, -14);
  scene.add(fillLight);

  // ---- 1. City Street Backdrop with Zebra Crosswalks (inspired by khanh020905/my-office) ------
  const asphaltMat = std('#69707a', { roughness: 0.90 });
  const sidewalkMat = std('#e5e7eb', { roughness: 0.80 });
  const stripeMat = std('#ffffff', { roughness: 0.60 });
  const terraceTileTex = gridTex('#27272a', '#18181b', 32, 10, 10);
  const terraceMat = std('#ffffff', { map: terraceTileTex, roughness: 0.80 });

  // Outer urban block base (asphalt road perimeter)
  scene.add(mesh(new THREE.BoxGeometry(46, ISLAND.height, 42), std('#272b33'), 1.5, -ISLAND.height / 2 - 0.04, 0));
  scene.add(mesh(new THREE.BoxGeometry(45.6, 0.08, 41.6), asphaltMat, 1.5, 0.0, 0));

  // Zebra crosswalks on the surrounding streets (North, South, West, East intersections)
  for (let i = -3; i <= 3; i++) {
    scene.add(mesh(new THREE.BoxGeometry(0.44, 0.016, 2.5), stripeMat, 0.0 + i * 0.86, 0.048, -15.4));
    scene.add(mesh(new THREE.BoxGeometry(0.44, 0.016, 2.5), stripeMat, 0.0 + i * 0.86, 0.048,  15.4));
    scene.add(mesh(new THREE.BoxGeometry(2.5, 0.016, 0.44), stripeMat, -15.8, 0.048, i * 0.86));
    scene.add(mesh(new THREE.BoxGeometry(2.5, 0.016, 0.44), stripeMat,  19.2, 0.048, i * 0.86));
  }
  // Dashed road center lines
  for (let x = -14; x <= 16; x += 3.6) {
    scene.add(mesh(new THREE.BoxGeometry(1.6, 0.012, 0.18), stripeMat, x, 0.046, -17.6));
    scene.add(mesh(new THREE.BoxGeometry(1.6, 0.012, 0.18), stripeMat, x, 0.046,  17.6));
  }
  // Parked orange & white city cars along the street
  addStreetCar(scene, -7.8, -16.8, 0, BRAND_ORANGE_DARK);
  addStreetCar(scene,  7.8,  16.8, Math.PI, '#ffffff');
  addStreetCar(scene, -17.6,  5.5, Math.PI / 2, BRAND_ORANGE);

  // Sidewalk curb + dark stone terrace platform supporting the unified office building
  scene.add(mesh(new THREE.BoxGeometry(32.2, 0.12, 25.2), sidewalkMat, 1.8, 0.06, 0));
  scene.add(mesh(new THREE.BoxGeometry(30.4, 0.14, 23.4), terraceMat, 1.8, 0.12, 0));

  // ---- 2. Unified Zero-Gap Office Building Shell & Floorplate (22.4m × 20.8m) -----------------
  // Main building spans x: [-11.2, +11.2] (width 22.4m), z: [-10.4, +10.4] (depth 20.8m), center = (0.0, 0.0)
  const oakCorridorTex = plankTex('#f5e5ce', '#e2c7a3', 8, 8);
  const corridorFloorMat = std('#ffffff', { map: oakCorridorTex, roughness: 0.68 });
  const pantryCheckerTex = gridTex('#ffffff', '#fed7aa', 64, 4, 4, '#ffedd5');

  // Continuous building interior floor slab with orange podium border
  scene.add(mesh(new THREE.BoxGeometry(22.7, 0.09, 21.1), std(BRAND_ORANGE_DARK), 0.0, 0.16, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(22.4, 0.04, 20.8), corridorFloorMat, 0.0, 0.20, 0.0));
  // Checkerboard pantry/lounge floor zones in the central atrium flanking Room 01
  scene.add(mesh(new THREE.BoxGeometry(2.5, 0.045, 4.6), std('#ffffff', { map: pantryCheckerTex }), -4.2, 0.205, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(2.5, 0.045, 4.6), std('#ffffff', { map: pantryCheckerTex }),  4.2, 0.205, 0.0));

  // Tall architectural outer shell walls flush against North (z = -10.50) and West (x = -11.30) like my-office
  const outerWallMat = std(WALL_WHITE, { roughness: 0.72 });
  const orangeBeltMat = std(BRAND_ORANGE_DARK, { roughness: 0.40 });
  const darkTrimMat = std('#18181b', { roughness: 0.45 });

  // North outer wall (x: -11.30 .. +11.30, z = -10.50)
  scene.add(mesh(new THREE.BoxGeometry(22.64, 2.65, 0.22), outerWallMat, 0.0, 1.48, -10.50));
  scene.add(mesh(new THREE.BoxGeometry(22.70, 0.14, 0.26), orangeBeltMat, 0.0, 2.84, -10.50));
  scene.add(mesh(new THREE.BoxGeometry(22.68, 0.08, 0.24), darkTrimMat, 0.0, 2.72, -10.50));

  // West outer wall (x = -11.30, z: -10.50 .. +10.50)
  scene.add(mesh(new THREE.BoxGeometry(0.22, 2.65, 21.04), outerWallMat, -11.30, 1.48, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.26, 0.14, 21.10), orangeBeltMat, -11.30, 2.84, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.24, 0.08, 21.08), darkTrimMat, -11.30, 2.72, 0.0));

  // Illuminated "LEVEL UP OFFICE" sign & System Status screen on the outer walls (my-office signature)
  const logoMat = std('#ffffff', { map: brandSignTex(), roughness: 0.3 });
  scene.add(mesh(new THREE.BoxGeometry(0.08, 0.90, 4.4), std('#18181b'), -11.16, 2.18, -2.6));
  scene.add(mesh(new THREE.BoxGeometry(0.04, 0.82, 4.28), logoMat, -11.11, 2.18, -2.6));

  const statusMat = std('#ffffff', { map: statusWallTex(), roughness: 0.3 });
  scene.add(mesh(new THREE.BoxGeometry(4.0, 1.20, 0.08), std('#18181b'), -2.8, 2.14, -10.36));
  scene.add(mesh(new THREE.BoxGeometry(3.88, 1.10, 0.04), statusMat, -2.8, 2.14, -10.32));

  // Framed windows along the North and West outer walls aligned with room centers
  const winGlassMat = std('#ffedd5', { transparent: true, opacity: 0.55, roughness: 0.15 });
  for (const wx of [-8.4, 2.8, 8.4]) {
    scene.add(mesh(new THREE.BoxGeometry(2.6, 0.92, 0.08), std(MULLION_DARK), wx, 2.08, -10.37));
    scene.add(mesh(new THREE.BoxGeometry(2.44, 0.78, 0.09), winGlassMat, wx, 2.08, -10.37));
  }
  for (const wz of [-7.8, 2.6, 7.8]) {
    scene.add(mesh(new THREE.BoxGeometry(0.08, 0.92, 2.4), std(MULLION_DARK), -11.17, 2.08, wz));
    scene.add(mesh(new THREE.BoxGeometry(0.09, 0.78, 2.24), winGlassMat, -11.17, 2.08, wz));
  }

  // Low perimeter cutaway curb along South (z = +10.48) and East Terrace glass railing (x = +16.4)
  scene.add(mesh(new THREE.BoxGeometry(22.64, 0.34, 0.16), outerWallMat, 0.0, 0.35, 10.48));
  scene.add(mesh(new THREE.BoxGeometry(22.68, 0.06, 0.18), orangeBeltMat, 0.0, 0.54, 10.48));

  const railGlassMat = std('#fff7ed', { transparent: true, opacity: 0.28, roughness: 0.15 });
  const railPostMat = std(MULLION_DARK, { roughness: 0.45, metalness: 0.3 });
  scene.add(mesh(new THREE.BoxGeometry(0.05, 0.65, 22.4), railGlassMat, 16.4, 0.52, 0));
  scene.add(mesh(new THREE.BoxGeometry(0.08, 0.05, 22.5), orangeBeltMat, 16.4, 0.86, 0));
  for (let rz = -10.5; rz <= 10.5; rz += 3.5) {
    scene.add(mesh(new THREE.BoxGeometry(0.07, 0.72, 0.07), railPostMat, 16.4, 0.52, rz));
  }

  // Street trees in crisp White & Orange planters around the sidewalk perimeter
  const planterPotMat = std('#ffffff');
  const planterRimMat = std(BRAND_ORANGE_DARK);
  const foliageDarkMat = std('#2d6a4f');
  const foliageLightMat = std('#52b788');
  const streetTrees = [
    [-12.8, -11.0], [-12.8, 11.0], [16.0, -11.0], [16.0, 11.0],
    [-5.6, 11.6], [5.6, 11.6],
  ];
  for (const [tx, tz] of streetTrees) {
    scene.add(mesh(new THREE.BoxGeometry(0.96, 0.34, 0.96), planterPotMat, tx, 0.28, tz));
    scene.add(mesh(new THREE.BoxGeometry(1.04, 0.06, 1.04), planterRimMat, tx, 0.46, tz));
    scene.add(mesh(new THREE.CylinderGeometry(0.10, 0.13, 0.60, 8), std('#6b4423'), tx, 0.66, tz));
    scene.add(mesh(new THREE.SphereGeometry(0.48, 12, 10), foliageDarkMat, tx, 1.12, tz));
    scene.add(mesh(new THREE.SphereGeometry(0.34, 10, 8), foliageLightMat, tx + 0.14, 1.38, tz - 0.10));
  }

  // Shared Atrium Lounge & Coffee Bar flanking Room 01 (at x = -4.2 and x = +4.2)
  // Left Atrium Lounge: orange & white sofa + coffee table
  scene.add(mesh(new THREE.BoxGeometry(0.76, 0.42, 1.95), std(BRAND_ORANGE_DARK), -4.3, 0.42, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.22, 0.38, 1.95), std('#ffffff'), -4.58, 0.68, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.52, 0.28, 1.05), std('#ffffff'), -3.52, 0.35, 0.0));
  // Right Atrium Coffee Pantry: white & orange counter + espresso machine
  scene.add(mesh(new THREE.BoxGeometry(0.74, 0.74, 2.2), std('#ffffff'), 4.2, 0.57, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.78, 0.07, 2.26), std(BRAND_ORANGE_DARK), 4.2, 0.96, 0.0));
  scene.add(mesh(new THREE.BoxGeometry(0.38, 0.36, 0.42), std('#18181b'), 4.2, 1.16, -0.45));

  // ---- 3. Zero-Gap Contiguous 4×4 Perimeter Rooms + Central Command (13 Agent Rooms) ----------
  const clickables = [];
  const rooms = {};
  const whiteDeskMat = std('#ffffff', { roughness: 0.35 });
  const orangeEdgeMat = std(BRAND_ORANGE_DARK, { roughness: 0.40 });
  const darkSlateMat = std('#272b33', { roughness: 0.50, metalness: 0.2 });
  const midSlateMat = std('#475569');
  const woodFloorTex = plankTex('#fffaf2', '#f3dfc1', 3, 3);

  for (const [idx, r] of ROOMS.entries()) {
    const zone = ZONES[r.zone];
    const g = new THREE.Group();
    g.position.set(r.x, 0, r.z);
    const mats = [];
    const own = (m) => { mats.push(m); return m; };
    const carpetTex = speckTex('#ffffff', '#fff7ed', '#ffedd5', 3, 3);

    // Flush room floor tile + orange & white rug under workstation (0 gap between neighboring rooms!)
    g.add(mesh(
      new THREE.BoxGeometry(r.w - 0.02, 0.03, r.d - 0.02),
      own(std('#ffffff', { map: r.tower ? woodFloorTex : carpetTex, roughness: 0.68 })),
      0, 0.215, 0
    ));
    g.add(mesh(new THREE.BoxGeometry(2.45, 0.016, 1.95), own(std(zone.color, { roughness: 0.75 })), 0, 0.232, -0.05));
    g.add(mesh(new THREE.BoxGeometry(2.24, 0.020, 1.74), own(std('#ffffff', { roughness: 0.80 })), 0, 0.236, -0.05));

    // Flush shared partition walls along the exact room boundaries (±r.w/2, ±r.d/2)
    addCutawayWall(g, own, r.w, 1.30, 0.10, 0, 0.86, -r.d / 2 + 0.05, zone.color);
    addCutawayWall(g, own, 0.10, 1.30, r.d * 0.50, -r.w / 2 + 0.05, 0.86, -r.d * 0.25, zone.color);
    addFramedGlassWall(g, own, r.d * 0.50, 1.26, -r.w / 2 + 0.05, 0.84, r.d * 0.25, true);
    // Right low cutaway partition wall (+X) + front glass partition & door plaque
    addCutawayWall(g, own, 0.10, 0.56, r.d * 0.60, r.w / 2 - 0.05, 0.50, -r.d * 0.20, zone.color);
    addFramedGlassWall(g, own, r.w * 0.42, 1.24, -r.w * 0.29, 0.84, r.d / 2 - 0.05, false);
    addCutawayWall(g, own, 0.42, 1.24, 0.12, r.w / 2 - 0.21, 0.84, r.d / 2 - 0.06, zone.color);

    const plaqueTex = doorPlaqueTex(r.agentId, AGENT_ROLE[r.agentId] || r.agentId, zone.color);
    g.add(mesh(new THREE.BoxGeometry(0.78, 0.24, 0.04), own(std('#ffffff', { map: plaqueTex, roughness: 0.4 })),
      r.w / 2 - 0.44, 1.14, r.d / 2 - 0.035));

    // Wall-mounted Sprint Kanban whiteboard on back wall
    const sbTex = sprintBoardTex(zone.color, r.agentId);
    if (r.tower) {
      // Executive Command Center: glass atrium canopy with orange fascia + panoramic 14-step command board
      g.add(mesh(new THREE.BoxGeometry(0.16, 1.88, 0.16), own(std(MULLION_DARK)), -2.65, 1.16, -2.05));
      g.add(mesh(new THREE.BoxGeometry(0.16, 1.88, 0.16), own(std(MULLION_DARK)),  2.65, 1.16, -2.05));
      g.add(mesh(new THREE.BoxGeometry(5.5, 0.12, 1.45), own(std('#ffffff')), 0, 2.12, -1.7));
      g.add(mesh(new THREE.BoxGeometry(5.58, 0.08, 1.52), own(std(BRAND_ORANGE_DARK)), 0, 2.22, -1.7));
      g.add(mesh(new THREE.BoxGeometry(2.68, 1.08, 0.08), own(std(BRAND_ORANGE_DARK)), 0.2, 1.22, -r.d / 2 + 0.14));
      g.add(mesh(new THREE.BoxGeometry(2.54, 0.94, 0.04), own(std('#ffffff', { map: sbTex, roughness: 0.4 })), 0.2, 1.22, -r.d / 2 + 0.17));
    } else {
      g.add(mesh(new THREE.BoxGeometry(1.42, 0.72, 0.05), own(std(BRAND_ORANGE_DARK)), 0.18, 1.12, -r.d / 2 + 0.14));
      g.add(mesh(new THREE.BoxGeometry(1.34, 0.64, 0.03), own(std('#ffffff', { map: sbTex, roughness: 0.4 })), 0.18, 1.12, -r.d / 2 + 0.165));
    }

    // Workstation: crisp White desk with Orange trim, dual screens, orange mug, white lamp
    const desk = mesh(new THREE.BoxGeometry(1.48, 0.065, 0.72), own(whiteDeskMat.clone()), 0, 0.72, 0.28);
    const deskEdge = mesh(new THREE.BoxGeometry(1.50, 0.072, 0.04), own(orangeEdgeMat.clone()), 0, 0.72, 0.63);
    const legL = mesh(new THREE.BoxGeometry(0.065, 0.50, 0.64), own(darkSlateMat.clone()), -0.65, 0.44, 0.28);
    const legR = mesh(new THREE.BoxGeometry(0.065, 0.50, 0.64), own(darkSlateMat.clone()),  0.65, 0.44, 0.28);
    const modesty = mesh(new THREE.BoxGeometry(1.22, 0.26, 0.03), own(std(BRAND_ORANGE_DARK)), 0, 0.56, 0.56);
    const deskMat = mesh(new THREE.BoxGeometry(0.74, 0.012, 0.32), own(std('#fff7ed')), 0, 0.758, 0.16);
    const keyboard = mesh(new THREE.BoxGeometry(0.32, 0.02, 0.11), own(std('#18181b')), -0.04, 0.77, 0.14);
    const mouse = mesh(new THREE.BoxGeometry(0.06, 0.018, 0.09), own(std(BRAND_ORANGE_DARK)), 0.22, 0.77, 0.14);
    const stand = mesh(new THREE.BoxGeometry(0.12, 0.22, 0.08), own(midSlateMat.clone()), 0, 0.85, 0.42);
    const scrTex = monitorScreenTex(zone.color);
    const screen = mesh(
      new THREE.BoxGeometry(0.80, 0.46, 0.05),
      own(std('#ffffff', { map: scrTex, emissive: '#000000', roughness: 0.35 })),
      0, 1.09, 0.36
    );
    const laptopBase = mesh(new THREE.BoxGeometry(0.26, 0.016, 0.19), own(std('#ffffff')), -0.46, 0.765, 0.24);
    laptopBase.rotation.y = 0.32;
    const laptopLid = mesh(new THREE.BoxGeometry(0.26, 0.17, 0.016), own(std(BRAND_ORANGE_DARK)), -0.48, 0.85, 0.31);
    laptopLid.rotation.y = 0.32;
    laptopLid.rotation.x = -0.22;
    const mug = mesh(new THREE.CylinderGeometry(0.042, 0.038, 0.09, 12), own(std(BRAND_ORANGE_DARK)), 0.48, 0.80, 0.16);
    const lampArm = mesh(new THREE.CylinderGeometry(0.02, 0.025, 0.32, 8), own(darkSlateMat.clone()), 0.54, 0.91, 0.42);
    const lampShade = mesh(new THREE.ConeGeometry(0.08, 0.12, 10), own(std(BRAND_ORANGE)), 0.48, 1.06, 0.36);
    lampShade.rotation.z = 0.45;
    const bag = mesh(new THREE.BoxGeometry(0.20, 0.28, 0.15), own(std(BRAND_ORANGE_DARK)), 0.82, 0.35, 0.22);

    g.add(desk, deskEdge, legL, legR, modesty, deskMat, keyboard, mouse, stand, screen, laptopBase, laptopLid, mug, lampArm, lampShade, bag);

    addSwivelChair(g, own, 0, 0.20, -0.48, zone.color);
    const plantKinds = ['monstera', 'snake', 'bush'];
    addPotPlant(g, own, -r.w / 2 + 0.46, 0.20, r.d / 2 - 0.46, plantKinds[idx % 3]);

    const { body, head, armL, armR } = buildChibiAgent(own, zone.color, idx);
    const ring = mesh(
      new THREE.RingGeometry(0.54, 0.72, 32),
      own(std(STATUS_STYLE.PENDING.color, { emissive: '#000000', side: THREE.DoubleSide })),
      0, 0.24, -0.42
    );
    ring.rotation.x = -Math.PI / 2;
    ring.castShadow = false;
    g.add(body, head, ring);

    for (const item of PROPS[r.agentId] || []) g.add(propMesh(item, 0.22, own));

    const [lx, ly, lz] = r.labelOffset || [0, 2.05, 0];
    const nameEl = label('', 'office-label');
    const name = new CSS2DObject(nameEl);
    name.position.set(lx, ly, lz);
    const bubbleEl = label('', 'office-bubble');
    bubbleEl.hidden = true;
    const bubble = new CSS2DObject(bubbleEl);
    bubble.position.set(lx, ly + 0.85, lz);
    g.add(name, bubble);
    for (const el of [nameEl, bubbleEl]) {
      el.style.pointerEvents = 'auto';
      el.addEventListener('click', () => onSelect(rooms[r.agentId].focusTask));
    }
    g.traverse((o) => { if (o.isMesh) { o.userData.agentId = r.agentId; clickables.push(o); } });
    scene.add(g);
    rooms[r.agentId] = {
      r, g, mats, screen, body, head, armL, armR, ring, nameEl, bubbleEl,
      status: 'PENDING', focusTask: r.taskKeys[0], bubbleUntil: 0, baseY: body.position.y, idx,
    };
    nameEl.textContent = `${STATUS_STYLE.PENDING.icon} ${AGENT_ROLE[r.agentId] || r.agentId}`;
  }

  // ---- 4. Aligned East Terrace: Mock Tool Gateway & Mock Systems (x = 14.2) -------------------
  const gate = new THREE.Group();
  gate.position.set(GATEWAY.x, 0, GATEWAY.z);
  gate.add(mesh(new THREE.BoxGeometry(3.2, 0.12, 3.2), std('#ffffff'), 0, 0.20, 0));
  gate.add(mesh(new THREE.BoxGeometry(3.26, 0.05, 3.26), std(BRAND_ORANGE_DARK), 0, 0.265, 0));
  for (const item of PROPS.gateway || []) gate.add(propMesh(item, 0.22));
  const gateLight = mesh(new THREE.SphereGeometry(0.28, 16, 12), std('#16a34a', { emissive: '#15803d' }), 0, 2.2, 0);
  gate.add(gateLight);
  const gateBubbleEl = label('', 'office-bubble office-bubble--alert');
  gateBubbleEl.hidden = true;
  const gateNameEl = label(GATEWAY.label, 'office-label office-label--gateway');
  const gateName = new CSS2DObject(gateNameEl);
  gateName.position.set(0, 2.45, 0);
  const gateBubble = new CSS2DObject(gateBubbleEl);
  gateBubble.position.set(0, 3.3, 0);
  gate.add(gateName, gateBubble);
  scene.add(gate);

  const mockLabelEls = [gateNameEl];
  for (const s of MOCK_SYSTEMS) {
    const h = new THREE.Group();
    h.position.set(s.x, 0, s.z);
    h.add(mesh(new THREE.BoxGeometry(2.8, 0.12, 2.8), std('#ffffff'), 0, 0.20, 0));
    h.add(mesh(new THREE.BoxGeometry(2.4, 1.32, 2.2), std(WALL_WHITE), 0, 0.88, 0));
    h.add(mesh(new THREE.BoxGeometry(1.6, 0.88, 0.06), std('#18181b', { emissive: '#ea580c', emissiveIntensity: 0.25 }), 0, 0.88, 1.1));
    h.add(mesh(new THREE.BoxGeometry(2.5, 0.10, 2.3), std('#18181b'), 0, 1.58, 0));
    h.add(mesh(new THREE.BoxGeometry(2.54, 0.08, 2.34), std(BRAND_ORANGE_DARK), 0, 1.66, 0));
    const mockEl = label(s.label, 'office-label office-label--mock');
    mockLabelEls.push(mockEl);
    const t = new CSS2DObject(mockEl);
    t.position.set(0, 2.1, 0);
    h.add(t);
    scene.add(h);
  }
  const bell = mesh(new THREE.ConeGeometry(0.36, 0.55, 12), std(BRAND_ORANGE_DARK, { emissive: '#9a3412' }), 1.95, 1.55, -1.55);
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
    room.screen.material.emissive.set(status === 'RUNNING' ? '#ea580c' : status === 'FAILED' ? '#ef4444' : '#000000');
    room.screen.material.emissiveIntensity = (status === 'RUNNING' || status === 'FAILED') ? 0.45 : 0.0;
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
    const isLiveTransition = Object.keys(lastStatus).length > 0;
    for (const room of Object.values(rooms)) {
      const { key, task } = roomStatus(room.r, byKey);
      if (!task) continue;
      room.focusTask = key;
      if (task.status !== room.status) {
        room.status = task.status;
        paint(room, task.status);
        room.bubbleUntil = (task.status === 'RUNNING' || task.status === 'FAILED') ? Infinity
          : (task.status === 'COMPLETED' && isLiveTransition) ? now + BUBBLE_MS : 0;
      }
      room.nameEl.textContent = `${STATUS_STYLE[task.status].icon} ${AGENT_ROLE[room.r.agentId] || room.r.agentId}`;
      room.nameEl.dataset.status = task.status;
      room.bubbleEl.textContent = bubbleText(task, byKey);
      room.bubbleEl.dataset.status = task.status;
    }
    for (const t of run.tasks) {
      if (t.status === 'COMPLETED' && lastStatus[t.task_key] && lastStatus[t.task_key] !== 'COMPLETED') {
        const from = roomForTask(t.task_key);
        for (const d of run.tasks.filter((x) => x.depends_on.includes(t.task_key))) {
          const to = roomForTask(d.task_key);
          if (to !== from) flyDoc(from, to, ZONES[from.zone].color);
        }
      }
    }
    let blocked = false;
    for (const t of run.tasks) {
      for (const [i, a] of (t.artifact?.action_results || []).entries()) {
        const id = `${t.task_key}:${t.attempt}:${i}`;
        const isBlock = a.decision === 'BLOCK';
        blocked ||= isBlock;
        if (!lastActions.has(id) && Object.keys(lastStatus).length) {
          flyDoc(roomForTask(t.task_key), GATEWAY, isBlock ? '#ef4444' : a.decision === 'NEEDS_APPROVAL' ? '#ea580c' : '#f97316');
        }
        lastActions.add(id);
      }
    }
    gateLight.material.color.set(blocked ? '#ef4444' : '#16a34a');
    gateLight.material.emissive.set(blocked ? '#7f1d1d' : '#15803d');
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
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    ray.setFromCamera(pointer, camera);
    const hit = ray.intersectObjects(clickables, false)[0];
    if (hit) onSelect(rooms[hit.object.userData.agentId].focusTask);
  });

  function syncStageBounds() {
    let top = '0px', left = '0px', right = '0px', bottom = '0px';
    if (window.innerWidth > 1100) {
      const topBar = document.querySelector('.top-bar');
      const leftRail = document.querySelector('.left-rail');
      const bottomDock = document.querySelector('.bottom-dock');
      const t = topBar ? Math.max(48, Math.ceil(topBar.getBoundingClientRect().bottom + 6)) : 56;
      const l = leftRail ? Math.max(280, Math.ceil(leftRail.getBoundingClientRect().right + 8)) : 332;
      const b = bottomDock ? Math.max(48, Math.ceil(window.innerHeight - bottomDock.getBoundingClientRect().top + 6)) : 200;
      top = `${t}px`;
      left = `${l}px`;
      right = '12px';
      bottom = `${b}px`;
    }
    if (container.style.top !== top) container.style.top = top;
    if (container.style.left !== left) container.style.left = left;
    if (container.style.right !== right) container.style.right = right;
    if (container.style.bottom !== bottom) container.style.bottom = bottom;
  }

  function resize() {
    syncStageBounds();
    const w = Math.max(320, container.clientWidth || window.innerWidth);
    const h = Math.max(240, container.clientHeight || window.innerHeight);
    renderer.setSize(w, h);
    labels.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize);
  ro.observe(container);
  for (const sel of ['.top-bar', '.left-rail', '.bottom-dock']) {
    const el = document.querySelector(sel);
    if (el) ro.observe(el);
  }
  window.addEventListener('resize', resize);
  resize();

  // ---- Screen-space label & bubble declutter (stable, non-oscillating) -------------------------
  function declutterLabels() {
    if (container.classList.contains('office--no-labels')) return;
    const placed = [];
    const items = [];
    for (const room of Object.values(rooms)) {
      const prio = room.status === 'FAILED' ? 3 : room.status === 'RUNNING' ? 2 : 1;
      room.nameEl.style.zIndex = String(10 + prio);
      items.push({ el: room.nameEl, prio, id: `name_${room.r.agentId}` });
      if (!room.bubbleEl.hidden) {
        room.bubbleEl.style.zIndex = String(20 + prio);
        items.push({ el: room.bubbleEl, prio: prio + 2, id: `bubble_${room.r.agentId}` });
      }
    }
    for (const [idx, el] of mockLabelEls.entries()) {
      items.push({ el, prio: 0, id: `mock_${idx}` });
    }

    // Measure true unshifted anchor rectangles by subtracting each element's currently applied shift
    const measured = [];
    for (const it of items) {
      const r = it.el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const prevShift = it.el._appliedShift || 0;
      measured.push({
        ...it,
        prevShift,
        left: r.left,
        right: r.right,
        baseTop: r.top - prevShift,
        baseBottom: r.bottom - prevShift,
      });
    }

    // Stable sort: higher priority first, then top-to-bottom by unshifted baseTop
    measured.sort((a, b) => (b.prio - a.prio) || (a.baseTop - b.baseTop) || a.id.localeCompare(b.id));

    for (const it of measured) {
      let targetShift = 0;
      for (let pass = 0; pass < 4; pass++) {
        let moved = false;
        for (const p of placed) {
          const overlapX = Math.min(it.right, p.right) - Math.max(it.left, p.left);
          const overlapY = Math.min(it.baseBottom + targetShift, p.bottom) - Math.max(it.baseTop + targetShift, p.top);
          if (overlapX > 6 && overlapY > 2) {
            targetShift = (p.top - it.baseBottom) - 5;
            moved = true;
          }
        }
        if (!moved) break;
      }
      targetShift = Math.max(-42, Math.min(0, targetShift));

      // Smoothly damp towards targetShift without any CSS transition oscillation
      const diff = targetShift - it.prevShift;
      const nextShift = Math.abs(diff) <= 1.2 ? targetShift : Math.round(it.prevShift + diff * 0.35);
      if (nextShift !== it.prevShift) {
        it.el._appliedShift = nextShift;
        it.el.style.marginTop = `${nextShift}px`;
      }
      placed.push({
        left: it.left,
        right: it.right,
        top: it.baseTop + targetShift,
        bottom: it.baseBottom + targetShift,
      });
    }
  }

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
      const bob = working ? Math.abs(Math.sin(time * 6)) * 0.11 : Math.sin(time * 1.8 + room.idx) * 0.012;
      room.body.position.y = room.baseY + bob;
      room.head.position.y = room.baseY + 0.7 + bob;
      room.head.rotation.y = working ? Math.sin(time * 3.8 + room.idx) * 0.15 : Math.sin(time * 0.8 + room.idx) * 0.05;
      if (room.armL && room.armR) {
        room.armL.rotation.x = working ? Math.sin(time * 15) * 0.22 : 0;
        room.armR.rotation.x = working ? -Math.sin(time * 15) * 0.22 : 0;
      }
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
    declutterLabels();
  }
  requestAnimationFrame(frame);

  return {
    update,
    setOption(name, value) {
      if (name === 'rotate') controls.autoRotate = !!value;
      if (name === 'labels') container.classList.toggle('office--no-labels', !value);
      if (name === 'bubbles') showBubbles = !!value;
    },
    resetCamera() { camera.position.copy(CAMERA_HOME); controls.target.copy(CAMERA_TARGET); controls.autoRotate = false; controls.update(); },
    setPaused(v) { paused = !!v; last = performance.now(); },
    reset() {
      lastStatus = {};
      lastActions = new Set();
      for (const room of Object.values(rooms)) { room.status = ''; room.bubbleUntil = 0; }
    },
  };
}
