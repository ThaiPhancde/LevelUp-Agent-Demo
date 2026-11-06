// Office floor plan (Claude + Gemini redesign inspired by khanh020905/my-office).
// Pure data, no three.js. Units: world metres; y is up, the floor is y = 0.
// Spec: docs/DEMO_DASHBOARD_3D.md section 2. Decorations live in office-props.js.

export const ISLAND = { size: 38, height: 1.0, color: '#e2ddd5', grass: '#f5f2eb' };

// Unified Orange & White brand palette across all zones (Chủ đề Cam & Trắng)
export const ZONES = {
  command:     { label: 'Chỉ huy',               color: '#ea580c' },
  market:      { label: 'Thị trường & Sản phẩm', color: '#f97316' },
  strategy:    { label: 'Chiến lược & Giá',      color: '#fb923c' },
  ads:         { label: 'Nội dung & Quảng cáo',  color: '#ea580c' },
  sales:       { label: 'Bán hàng & CSKH',       color: '#f59e0b' },
  analytics:   { label: 'Phân tích & Tài chính', color: '#d97706' },
  supervision: { label: 'Kiểm tra & Giám sát',   color: '#c2410c' },
  gateway:     { label: 'Cổng kiểm soát',        color: '#9a3412' },
};

// Zero-gap contiguous 4×4 perimeter grid inside a unified 22.4m × 20.8m office building:
// - 4 Columns (each w = 5.6m, touching edge-to-edge from x = -11.2 to +11.2):
//     X_COL0 = -8.4, X_COL1 = -2.8, X_COL2 = +2.8, X_COL3 = +8.4
// - 4 Rows (each d = 5.2m, touching edge-to-edge from z = -10.4 to +10.4):
//     Z_ROW0 = -7.8, Z_ROW1 = -2.6, Z_ROW2 = +2.6, Z_ROW3 = +7.8
// - Center Atrium (x = 0.0, z = 0.0): Room 01 (w = 5.6, d = 4.6) inside the 11.2m × 10.4m court
export const ROOMS = [
  { agentId: '01', taskKeys: ['plan', 'summary'], zone: 'command',     x:  0.0, z:  0.0, w: 5.6, d: 4.6, tower: true, labelOffset: [0, 2.30, -0.3] },
  { agentId: '02', taskKeys: ['market'],          zone: 'market',      x: -8.4, z: -7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05, -0.2] },
  { agentId: '03', taskKeys: ['product'],         zone: 'market',      x: -2.8, z: -7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05, -0.2] },
  { agentId: '04', taskKeys: ['offer'],           zone: 'strategy',    x:  2.8, z: -7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05, -0.2] },
  { agentId: '05', taskKeys: ['content'],         zone: 'ads',         x:  8.4, z: -7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05, -0.2] },
  { agentId: '06', taskKeys: ['campaign'],        zone: 'ads',         x:  8.4, z: -2.6, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.0] },
  { agentId: '07', taskKeys: ['leads'],           zone: 'sales',       x:  8.4, z:  2.6, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.0] },
  { agentId: '08', taskKeys: ['care'],            zone: 'sales',       x:  8.4, z:  7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.2] },
  { agentId: '09', taskKeys: ['kpi'],             zone: 'analytics',   x:  2.8, z:  7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.2] },
  { agentId: '10', taskKeys: ['finance'],         zone: 'analytics',   x: -2.8, z:  7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.2] },
  { agentId: '11', taskKeys: ['qa'],              zone: 'supervision', x: -8.4, z: -2.6, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.0] },
  { agentId: '12', taskKeys: ['audit'],           zone: 'supervision', x: -8.4, z:  2.6, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.0] },
  { agentId: '13', taskKeys: ['monitor'],         zone: 'supervision', x: -8.4, z:  7.8, w: 5.6, d: 5.2, labelOffset: [0, 2.05,  0.2] },
];

// East Terrace aligned 1-to-1 with the 4 horizontal rows (z = -7.8, -2.6, +2.6, +7.8):
export const GATEWAY = { x: 14.2, z: -2.6, label: 'Mock Tool Gateway' };
export const MOCK_SYSTEMS = [
  { id: 'meta_ads', label: 'Meta Ads (mock)',    x: 14.2, z: -7.8 },
  { id: 'crm',      label: 'CRM (mock)',         x: 14.2, z:  2.6 },
  { id: 'payment',  label: 'Thanh toán (mock)',  x: 14.2, z:  7.8 },
];

// Task status -> look. Icons are text so meaning never depends on colour alone.
export const STATUS_STYLE = {
  PENDING:   { color: '#94a3b8', icon: '⏸', light: 0.0, opacity: 1.0 },
  RUNNING:   { color: '#ea580c', icon: '⚙', light: 1.0, opacity: 1.0 },
  COMPLETED: { color: '#16a34a', icon: '✓', light: 0.6, opacity: 1.0 },
  FAILED:    { color: '#dc2626', icon: '!', light: 0.8, opacity: 1.0 },
  SKIPPED:   { color: '#94a3b8', icon: '↷', light: 0.0, opacity: 0.45 },
  CANCELLED: { color: '#64748b', icon: '✕', light: 0.0, opacity: 0.35 },
};

export function roomForTask(taskKey) {
  return ROOMS.find((r) => r.taskKeys.includes(taskKey));
}
