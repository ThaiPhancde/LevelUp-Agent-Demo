// Office floor plan (Claude). Pure data, no three.js. Units: world metres; y is up, the floor is y = 0.
// Spec: docs/DEMO_DASHBOARD_3D.md section 2. Decorations live in office-props.js (Gemini).

export const ISLAND = { size: 38, height: 1.2, color: '#efe6d2', grass: '#bfe3b4' };

export const ZONES = {
  command:    { label: 'Phòng Chỉ huy',          color: '#f2c14e' },
  market:     { label: 'Thị trường & Sản phẩm',  color: '#5b8def' },
  strategy:   { label: 'Chiến lược & Sáng tạo',  color: '#9b6ef3' },
  ads:        { label: 'Quảng cáo',              color: '#f28c38' },
  sales:      { label: 'Bán hàng & CSKH',        color: '#45b36b' },
  analytics:  { label: 'Phân tích & Tài chính',  color: '#2bb3a6' },
  supervision:{ label: 'Phòng Giám sát',         color: '#e8686b' },
  gateway:    { label: 'Cổng Mock',              color: '#9aa0a6' },
};

// One room per agent. x/z = room centre, w/d = footprint. taskKeys map workflow tasks to the room.
export const ROOMS = [
  { agentId: '01', taskKeys: ['plan', 'summary'], zone: 'command',     x: 0,   z: 0,   w: 7, d: 7, tower: true },
  { agentId: '02', taskKeys: ['market'],          zone: 'market',      x: -10, z: -10, w: 5, d: 5 },
  { agentId: '03', taskKeys: ['product'],         zone: 'market',      x: -4,  z: -12, w: 5, d: 5 },
  { agentId: '04', taskKeys: ['offer'],           zone: 'strategy',    x: 3,   z: -12, w: 5, d: 5 },
  { agentId: '05', taskKeys: ['content'],         zone: 'strategy',    x: 10,  z: -10, w: 5, d: 5 },
  { agentId: '06', taskKeys: ['campaign'],        zone: 'ads',         x: 12,  z: -2,  w: 5, d: 5 },
  { agentId: '07', taskKeys: ['leads'],           zone: 'sales',       x: 11,  z: 6,   w: 5, d: 5 },
  { agentId: '08', taskKeys: ['care'],            zone: 'sales',       x: 4,   z: 11,  w: 5, d: 5 },
  { agentId: '09', taskKeys: ['kpi'],             zone: 'analytics',   x: -3,  z: 11,  w: 5, d: 5 },
  { agentId: '10', taskKeys: ['finance'],         zone: 'analytics',   x: -9,  z: 11,  w: 5, d: 5 },
  { agentId: '11', taskKeys: ['qa'],              zone: 'supervision', x: -13, z: -3,  w: 5, d: 4 },
  { agentId: '12', taskKeys: ['audit'],           zone: 'supervision', x: -13, z: 1,   w: 5, d: 4 },
  { agentId: '13', taskKeys: ['monitor'],         zone: 'supervision', x: -13, z: 5,   w: 5, d: 4 },
];

// Edge of the island: every external "Act" passes this gate (core/gateway.py). Not an agent.
export const GATEWAY = { x: 15, z: 13, label: 'Mock Tool Gateway' };
export const MOCK_SYSTEMS = [
  { id: 'meta_ads', label: 'Meta Ads (mock)', x: 17, z: 6 },
  { id: 'crm',      label: 'CRM (mock)',      x: 17, z: 17 },
  { id: 'payment',  label: 'Thanh toán (mock)', x: 10, z: 17 },
];

// Task status -> look. Icons are text so meaning never depends on colour alone.
export const STATUS_STYLE = {
  PENDING:   { color: '#b8bcc4', icon: '⏸', light: 0.0, opacity: 1.0 },
  RUNNING:   { color: '#ffd166', icon: '⚙', light: 1.0, opacity: 1.0 },
  COMPLETED: { color: '#4caf50', icon: '✓', light: 0.6, opacity: 1.0 },
  FAILED:    { color: '#e53935', icon: '!', light: 0.8, opacity: 1.0 },
  SKIPPED:   { color: '#9e9e9e', icon: '↷', light: 0.0, opacity: 0.45 },
  CANCELLED: { color: '#757575', icon: '✕', light: 0.0, opacity: 0.35 },
};

export function roomForTask(taskKey) {
  return ROOMS.find((r) => r.taskKeys.includes(taskKey));
}
