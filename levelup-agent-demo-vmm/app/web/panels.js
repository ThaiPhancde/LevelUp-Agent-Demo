import { RUN_STATUS_LABEL, TASK_STATUS_LABEL, TASK_TITLE, AGENT_ROLE, SCENARIOS, SCENARIO_LABEL, RULE_LABEL, SEVERITY_LABEL, CHECK_STATUS_LABEL, ENGINE_LABEL, DECISION_LABEL, DECISION_HINT, LLM_SOURCE_LABEL, errorText, scenarioText, runTitle, formatTime, overviewCounts, ACTION_LABEL, TOOL_LABEL, APPROVAL_STATUS_LABEL, DISPATCH_OUTCOME_LABEL, INPUT_SOURCE_LABEL } from './labels.js';

const DEFAULT_OBJECTIVE =
  'Phân tích thị trường Philippines, chọn sản phẩm tiềm năng và lập chiến dịch bán hàng giả lập.';

const DEFAULT_AGENTS = [
  { id: '01', name: AGENT_ROLE['01'], group: 'business', responsibility: 'Phân rã mục tiêu, giao việc, tổng hợp báo cáo cuối', tasks: ['plan', 'summary'] },
  { id: '02', name: AGENT_ROLE['02'], group: 'business', responsibility: 'Phân tích thị trường giả lập từ dữ liệu mẫu', tasks: ['market'] },
  { id: '03', name: AGENT_ROLE['03'], group: 'business', responsibility: 'So sánh sản phẩm và nhà cung cấp giả lập, chọn sản phẩm', tasks: ['product'] },
  { id: '04', name: AGENT_ROLE['04'], group: 'business', responsibility: 'Tính giá bán, biên lợi nhuận, điểm hòa vốn', tasks: ['offer'] },
  { id: '05', name: AGENT_ROLE['05'], group: 'business', responsibility: 'Tạo định hướng nội dung và mẫu quảng cáo bản nháp', tasks: ['content'] },
  { id: '06', name: AGENT_ROLE['06'], group: 'business', responsibility: 'Lập chiến dịch quảng cáo bản nháp, không đăng thật', tasks: ['campaign'] },
  { id: '07', name: AGENT_ROLE['07'], group: 'business', responsibility: 'Xử lý khách tiềm năng giả lập, soạn câu trả lời nháp', tasks: ['leads'] },
  { id: '08', name: AGENT_ROLE['08'], group: 'business', responsibility: 'Chăm sóc sau bán, theo dõi giao hàng và đổi trả giả lập', tasks: ['care'] },
  { id: '09', name: AGENT_ROLE['09'], group: 'business', responsibility: 'Tính chỉ số hiệu quả: tỷ lệ chuyển đổi, chi phí, doanh thu', tasks: ['kpi'] },
  { id: '10', name: AGENT_ROLE['10'], group: 'business', responsibility: 'Phân tích lợi nhuận, ngân sách và rủi ro', tasks: ['finance'] },
  { id: '11', name: AGENT_ROLE['11'], group: 'supervisory', responsibility: 'Kiểm tra đầu ra: cấu trúc, phép tính, nhất quán số liệu', tasks: ['qa'] },
  { id: '12', name: AGENT_ROLE['12'], group: 'supervisory', responsibility: 'Kiểm tra quyền, hành động ghi, phê duyệt và lịch sử', tasks: ['audit'] },
  { id: '13', name: AGENT_ROLE['13'], group: 'supervisory', responsibility: 'Theo dõi thời gian, số lần thử, lỗi, hạn mức', tasks: ['monitor'] },
];

const DEFAULT_TASKS = [
  { task_key: 'plan',     agent_id: '01', depends_on: [] },
  { task_key: 'market',   agent_id: '02', depends_on: ['plan'] },
  { task_key: 'product',  agent_id: '03', depends_on: ['market'] },
  { task_key: 'offer',    agent_id: '04', depends_on: ['product'] },
  { task_key: 'content',  agent_id: '05', depends_on: ['offer'] },
  { task_key: 'campaign', agent_id: '06', depends_on: ['offer', 'content'] },
  { task_key: 'leads',    agent_id: '07', depends_on: ['campaign'] },
  { task_key: 'care',     agent_id: '08', depends_on: ['leads'] },
  { task_key: 'kpi',      agent_id: '09', depends_on: ['leads', 'care'] },
  { task_key: 'finance',  agent_id: '10', depends_on: ['offer', 'kpi'] },
  { task_key: 'qa',       agent_id: '11', depends_on: ['market', 'product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance'] },
  { task_key: 'audit',    agent_id: '12', depends_on: ['market', 'product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance'] },
  { task_key: 'monitor',  agent_id: '13', depends_on: ['market', 'product', 'offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance', 'qa', 'audit'] },
  { task_key: 'summary',  agent_id: '01', depends_on: ['qa', 'audit', 'monitor'] },
];

const ZONES = {
  command:     { label: 'Chỉ huy',              color: '#ea580c' },
  market:      { label: 'Thị trường & Sản phẩm', color: '#f97316' },
  strategy:    { label: 'Chiến lược & Giá',      color: '#fb923c' },
  ads:         { label: 'Nội dung & Quảng cáo',  color: '#ea580c' },
  sales:       { label: 'Bán hàng & CSKH',       color: '#f59e0b' },
  analytics:   { label: 'Phân tích & Tài chính', color: '#d97706' },
  supervision: { label: 'Kiểm tra & Giám sát',   color: '#c2410c' },
  gateway:     { label: 'Cổng kiểm soát',        color: '#9a3412' },
};

const TASK_ZONE = {
  plan: 'command',
  summary: 'command',
  market: 'market',
  product: 'market',
  offer: 'strategy',
  content: 'ads',
  campaign: 'ads',
  leads: 'sales',
  care: 'sales',
  kpi: 'analytics',
  finance: 'analytics',
  qa: 'supervision',
  audit: 'supervision',
  monitor: 'supervision',
};

const NODE_VISUAL = {
  PENDING:   { color: '#b8bcc4', opacity: 0.78 },
  RUNNING:   { color: '#ea580c', opacity: 1.0 },
  COMPLETED: { color: '#16a34a', opacity: 1.0 },
  FAILED:    { color: '#dc2626', opacity: 1.0 },
  SKIPPED:   { color: '#9e9e9e', opacity: 0.58 },
  CANCELLED: { color: '#757575', opacity: 0.58 },
};

const DONE_STATUSES = new Set(['COMPLETED', 'FAILED', 'SKIPPED', 'CANCELLED']);
const CANCELLABLE_STATUSES = new Set(['PENDING', 'RUNNING', 'WAITING_APPROVAL']);

const KEY_NUMBER_LABELS = {
  selling_price_php: 'Giá bán (PHP)',
  margin_per_unit_php: 'Biên lợi nhuận / đơn (PHP)',
  breakeven_orders: 'Điểm hòa vốn (đơn)',
  roas: 'Hiệu quả chi phí quảng cáo (ROAS)',
  contribution_after_ads_php: 'Lợi nhuận sau quảng cáo (PHP)',
  risk_level: 'Mức độ rủi ro',
};

const RISK_VALUE_LABELS = {
  HIGH: 'Cao',
  MEDIUM: 'Trung bình',
  LOW: 'Thấp',
};

const DEFAULT_SCENARIO_TASK = {
  timeout: 'market',
  missing_field: 'offer',
  empty_response: 'content',
};

import { businessText as humanizeText } from './labels.js';

const SVG_NS =
  typeof DOMParser !== 'undefined'
    ? new DOMParser().parseFromString('<svg></svg>', 'text/html').querySelector('svg')?.namespaceURI
    : null;

function clearChildren(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function h(tag, attrs = {}, ...children) {
  const elem = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'className') {
      elem.className = v;
    } else if (k === 'textContent') {
      elem.textContent = String(v);
    } else if (k === 'dataset' && typeof v === 'object') {
      for (const [dk, dv] of Object.entries(v)) {
        if (dv !== null && dv !== undefined && dv !== false) {
          elem.dataset[dk] = String(dv);
        }
      }
    } else if (k.startsWith('on') && typeof v === 'function') {
      elem.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v === true) {
      elem.setAttribute(k, '');
    } else {
      elem.setAttribute(k, String(v));
    }
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (typeof child === 'string' || typeof child === 'number') {
      elem.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      elem.appendChild(child);
    }
  }
  return elem;
}

function svgEl(tag, attrs = {}, ...children) {
  const elem = SVG_NS ? document.createElementNS(SVG_NS, tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') {
      elem.addEventListener(k.slice(2).toLowerCase(), v);
    } else {
      elem.setAttribute(k, String(v));
    }
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (typeof child === 'string' || typeof child === 'number') {
      elem.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      elem.appendChild(child);
    }
  }
  return elem;
}

export function createPanels(root, handlers = {}) {
  if (!root) {
    throw new Error('Cần phần tử gốc để khởi tạo giao diện.');
  }
  clearChildren(root);

  const state = {
    agents: [...DEFAULT_AGENTS],
    agentById: new Map(),
    agentByTask: new Map(),
    currentRun: null,
    historyRuns: [],
    selectedTaskKey: null,
    activeTab: 'summary',
    viewMode: '3d',
    rotate: true,
    labels: true,
    bubbles: true,
    formOpen: false,
    decisionLogs: [],
    decisionLogRunId: null,
    decisionLogLoading: false,
    lastOverviewSig: '',
    lastDrawerSig: '',
    lastSummarySig: '',
    lastChecksSig: '',
    lastLlmSig: '',
    last2dSig: '',
  };

  function rebuildAgentMaps() {
    state.agentById.clear();
    state.agentByTask.clear();
    for (const ag of state.agents) {
      state.agentById.set(ag.id, ag);
      if (Array.isArray(ag.tasks)) {
        for (const tk of ag.tasks) {
          state.agentByTask.set(tk, ag);
        }
      }
    }
  }
  rebuildAgentMaps();

  function getAgentForTask(taskKey, agentId) {
    if (agentId && state.agentById.has(agentId)) {
      return state.agentById.get(agentId);
    }
    if (state.agentByTask.has(taskKey)) {
      return state.agentByTask.get(taskKey);
    }
    return DEFAULT_AGENTS.find((a) => a.id === agentId || a.tasks.includes(taskKey)) || {
      id: agentId || '01',
      name: AGENT_ROLE[agentId] || 'Nhân sự phụ trách',
      responsibility: '',
    };
  }

  function getRoleLabel(taskKey, agentId) {
    if (agentId && AGENT_ROLE[agentId]) return AGENT_ROLE[agentId];
    const ag = getAgentForTask(taskKey, agentId);
    return AGENT_ROLE[ag.id] || 'Nhân sự phụ trách';
  }

  function getTaskTitle(taskKey) {
    return TASK_TITLE[taskKey] || 'Bước công việc';
  }

  function getTasksList(runObj) {
    if (runObj && Array.isArray(runObj.tasks) && runObj.tasks.length > 0) {
      return runObj.tasks;
    }
    return DEFAULT_TASKS.map((t) => ({
      task_key: t.task_key,
      agent_id: t.agent_id,
      status: 'PENDING',
      depends_on: [...t.depends_on],
      attempt: 0,
      error: null,
      started_at: null,
      finished_at: null,
      narrative: null,
      artifact_type: null,
      artifact: null,
    }));
  }

  // ==================== 1. TOP BAR ====================
  const runStatusBadge = h('span', {
    className: 'badge badge-status status-PENDING',
    'data-role': 'run-status',
    'data-run-status': 'PENDING',
    title: 'PENDING',
    textContent: RUN_STATUS_LABEL.PENDING,
  });

  const stepBadge = h('span', {
    className: 'badge badge-meta',
    'data-role': 'step-counter',
    textContent: 'Bước 0/14',
  });

  const rotateBtn = h('button', {
    type: 'button',
    className: 'btn-toggle',
    'aria-pressed': 'true',
    'data-action': 'toggle-rotate',
    textContent: 'Dừng xoay',
    onClick: () => {
      state.rotate = !state.rotate;
      rotateBtn.setAttribute('aria-pressed', String(state.rotate));
      rotateBtn.textContent = state.rotate ? 'Dừng xoay' : 'Tự xoay';
      handlers.onToggle?.('rotate', state.rotate);
    },
  });

  const labelsBtn = h('button', {
    type: 'button',
    className: 'btn-toggle',
    'aria-pressed': 'true',
    'data-action': 'toggle-labels',
    textContent: 'Tên',
    onClick: () => {
      state.labels = !state.labels;
      labelsBtn.setAttribute('aria-pressed', String(state.labels));
      handlers.onToggle?.('labels', state.labels);
    },
  });

  const bubblesBtn = h('button', {
    type: 'button',
    className: 'btn-toggle',
    'aria-pressed': 'true',
    'data-action': 'toggle-bubbles',
    textContent: 'Bong bóng',
    onClick: () => {
      state.bubbles = !state.bubbles;
      bubblesBtn.setAttribute('aria-pressed', String(state.bubbles));
      handlers.onToggle?.('bubbles', state.bubbles);
    },
  });

  const resetCamBtn = h('button', {
    type: 'button',
    'data-action': 'reset-camera',
    textContent: 'Toàn cảnh',
    onClick: () => {
      handlers.onResetCamera?.();
    },
  });

  const viewToggleBtn = h('button', {
    type: 'button',
    className: 'btn-toggle',
    'aria-pressed': 'false',
    'data-action': 'toggle-view',
    textContent: 'Tổng quan (2D)',
    onClick: () => {
      const nextMode = state.viewMode === '3d' ? '2d' : '3d';
      setView(nextMode);
      handlers.onView?.(nextMode);
    },
  });

  const startDemoTopBtn = h('button', {
    type: 'button',
    className: 'btn-primary',
    'data-action': 'start-demo',
    title: 'Start Demo',
    textContent: '▶ Chạy ngay',
    onClick: () => triggerStart(),
  });

  const topBar = h(
    'header',
    { className: 'panel-card top-bar' },
    h(
      'div',
      { className: 'top-bar-brand' },
      h(
        'div',
        { className: 'brand-heading' },
        h('h1', { className: 'brand-title', textContent: 'Văn phòng Level Up' }),
        h('span', { className: 'brand-subtitle', textContent: 'đội 13 AI agent bán hàng' })
      ),
      h('span', { className: 'badge badge-mock', textContent: 'MOCK ONLY — dữ liệu giả lập' }),
      stepBadge,
      runStatusBadge
    ),
    h(
      'div',
      { className: 'top-bar-controls', role: 'toolbar', 'aria-label': 'Thanh công cụ điều khiển' },
      rotateBtn,
      labelsBtn,
      bubblesBtn,
      resetCamBtn,
      viewToggleBtn,
      startDemoTopBtn
    )
  );

  // ==================== 2. LEFT RAIL: CARD "TỔNG QUAN" ====================
  const overviewSubtitle = h('p', {
    className: 'overview-subtitle',
    'data-role': 'overview-subtitle',
    textContent: 'Chưa có lượt nào',
  });

  const objectiveInput = h('textarea', {
    className: 'objective-textarea',
    name: 'objective',
    rows: '2',
    'aria-label': 'Mục tiêu kinh doanh',
  });
  objectiveInput.value = DEFAULT_OBJECTIVE;

  const modeMockRadio = h('input', {
    type: 'radio',
    name: 'run_mode',
    value: 'mock',
    checked: true,
    onChange: () => updateModeWarning(),
  });

  const modeDeepSeekRadio = h('input', {
    type: 'radio',
    name: 'run_mode',
    value: 'deepseek',
    onChange: () => updateModeWarning(),
  });

  const deepseekWarning = h('div', {
    className: 'deepseek-warning',
    hidden: true,
    textContent:
      'Cảnh báo: Chế độ DeepSeek có tính phí thật. Bản thử nghiệm giới hạn tối đa 2 lần gọi thật trong toàn bộ quá trình triển khai.',
  });

  function updateModeWarning() {
    deepseekWarning.hidden = !modeDeepSeekRadio.checked;
  }

  const scenarioControls = new Map();

  function populateTaskSelectOptions(selectElem, defaultTaskKey) {
    const prevValue = selectElem.value;
    clearChildren(selectElem);
    for (const t of DEFAULT_TASKS) {
      const opt = h('option', {
        value: t.task_key,
        title: t.task_key,
        textContent: getTaskTitle(t.task_key),
      });
      selectElem.appendChild(opt);
    }
    selectElem.value = prevValue || defaultTaskKey || DEFAULT_TASKS[0].task_key;
  }

  const scenarioRows = SCENARIOS.map((sc) => {
    const isParam = Boolean(sc.needsTask);
    const defaultTask = DEFAULT_SCENARIO_TASK[sc.id] || DEFAULT_TASKS[0].task_key;

    const checkbox = h('input', {
      type: 'checkbox',
      name: isParam ? `inject_${sc.id}_enabled` : `inject_${sc.id}`,
      value: isParam ? `${sc.id}:` : sc.id,
      title: sc.id,
      dataset: isParam
        ? { scenarioId: sc.id, injectPrefix: sc.id }
        : { scenarioId: sc.id, injectType: sc.id },
      onChange: () => updateScenarioSummary(),
    });

    let select = null;
    if (isParam) {
      select = h('select', {
        className: 'inject-select',
        name: `inject_${sc.id}_task`,
        'aria-label': `Chọn bước cho tình huống ${sc.label}`,
        dataset: { injectSelect: sc.id },
        onChange: () => {
          checkbox.checked = Boolean(select.value);
          updateScenarioSummary();
        },
      });
      populateTaskSelectOptions(select, defaultTask);
    }

    scenarioControls.set(sc.id, { sc, checkbox, select, defaultTask });

    return h(
      'div',
      { className: 'scenario-item', title: sc.id },
      h(
        'div',
        { className: 'scenario-main-row' },
        h(
          'label',
          { className: 'checkbox-label scenario-label' },
          checkbox,
          h('span', { className: 'scenario-label-text', textContent: sc.label })
        ),
        select
      ),
      h('small', { className: 'scenario-hint', textContent: sc.hint })
    );
  });

  const scenarioSummaryEl = h('div', {
    className: 'scenario-summary',
    'data-role': 'scenario-summary',
    textContent: scenarioText([]),
  });

  function buildInjectArray() {
    const inject = [];
    for (const { sc, checkbox, select } of scenarioControls.values()) {
      if (!checkbox.checked) continue;
      if (sc.needsTask) {
        if (select && select.value) {
          inject.push(`${sc.id}:${select.value}`);
        }
      } else {
        inject.push(sc.id);
      }
    }
    return inject;
  }

  function updateScenarioSummary() {
    const arr = buildInjectArray();
    scenarioSummaryEl.textContent = scenarioText(arr);
    scenarioSummaryEl.title = arr.join(', ');
  }

  function resetScenarios() {
    for (const { checkbox, select, defaultTask } of scenarioControls.values()) {
      checkbox.checked = false;
      if (select) {
        select.value = defaultTask;
      }
    }
    updateScenarioSummary();
  }

  function triggerStart() {
    const objective = objectiveInput.value.trim() || DEFAULT_OBJECTIVE;
    const mode = modeDeepSeekRadio.checked ? 'llm' : 'mock';
    const inject = buildInjectArray();
    handlers.onStart?.({ objective, mode, inject });
  }

  const startFormBody = h(
    'form',
    {
      className: 'start-form-body',
      hidden: true,
      onSubmit: (e) => {
        e.preventDefault();
        triggerStart();
      },
    },
    h(
      'div',
      { className: 'form-field' },
      h('label', { className: 'form-label', textContent: 'Mục tiêu kinh doanh' }),
      objectiveInput
    ),
    h(
      'div',
      { className: 'form-field' },
      h('span', { className: 'form-label', textContent: 'Chế độ chạy' }),
      h(
        'div',
        { className: 'radio-group' },
        h('label', { className: 'radio-label' }, modeMockRadio, 'Mô phỏng (mặc định, miễn phí)'),
        h('label', { className: 'radio-label' }, modeDeepSeekRadio, 'Dùng DeepSeek (có tính phí)')
      ),
      deepseekWarning
    ),
    h(
      'div',
      { className: 'form-field' },
      h('span', { className: 'form-label', textContent: 'Tình huống thử' }),
      h('div', { className: 'inject-group' }, ...scenarioRows, scenarioSummaryEl)
    ),
    h(
      'div',
      { className: 'inject-row form-actions-row' },
      h('button', {
        type: 'submit',
        className: 'btn-primary',
        textContent: 'Chạy',
      }),
      h('button', {
        type: 'button',
        textContent: 'Bỏ chọn tất cả',
        onClick: () => resetScenarios(),
      })
    )
  );

  const toggleFormBtn = h('button', {
    type: 'button',
    className: 'btn-primary overview-start-btn',
    'aria-expanded': 'false',
    'data-action': 'toggle-start-form',
    textContent: '▶ Chạy kịch bản mới',
    onClick: () => {
      state.formOpen = !state.formOpen;
      startFormBody.hidden = !state.formOpen;
      toggleFormBtn.setAttribute('aria-expanded', String(state.formOpen));
    },
  });

  // 4 counter tiles
  const tileValueEls = {
    running: h('span', { className: 'tile-number', textContent: '0' }),
    todo: h('span', { className: 'tile-number', textContent: '0' }),
    awaiting: h('span', { className: 'tile-number', textContent: '0' }),
    failed: h('span', { className: 'tile-number', textContent: '0' }),
  };

  const tileBoxEls = {
    running: h(
      'div',
      { className: 'overview-tile', 'data-tile': 'running' },
      tileValueEls.running,
      h('span', { className: 'tile-label', textContent: 'Đang làm' })
    ),
    todo: h(
      'div',
      { className: 'overview-tile', 'data-tile': 'todo' },
      tileValueEls.todo,
      h('span', { className: 'tile-label', textContent: 'Chờ làm' })
    ),
    awaiting: h(
      'div',
      { className: 'overview-tile', 'data-tile': 'awaiting' },
      tileValueEls.awaiting,
      h('span', { className: 'tile-label', textContent: 'Chờ duyệt' })
    ),
    failed: h(
      'div',
      { className: 'overview-tile', 'data-tile': 'failed' },
      tileValueEls.failed,
      h('span', { className: 'tile-label', textContent: 'Lỗi' })
    ),
  };

  const tilesRow = h(
    'div',
    { className: 'overview-tiles', 'aria-label': 'Thống kê nhanh lượt chạy' },
    tileBoxEls.running,
    tileBoxEls.todo,
    tileBoxEls.awaiting,
    tileBoxEls.failed
  );

  // Pending approval highlighted box inside Overview
  const approvalContainer = h('div', {
    className: 'approval-card',
    'aria-label': 'Chờ người duyệt',
    hidden: true,
  });

  // Work list ("Việc của lượt này")
  const workListContainer = h('div', {
    className: 'overview-work-list',
    role: 'list',
  });

  const overviewCard = h(
    'section',
    { className: 'panel-card overview-card', 'aria-label': 'Tổng quan' },
    h(
      'div',
      { className: 'overview-header' },
      h(
        'div',
        { className: 'overview-title-group' },
        h('h2', { className: 'overview-title', textContent: 'Tổng quan' }),
        overviewSubtitle
      ),
      toggleFormBtn
    ),
    startFormBody,
    tilesRow,
    approvalContainer,
    h(
      'div',
      { className: 'overview-work-section' },
      h('h3', { className: 'overview-section-title', textContent: 'Việc của lượt này' }),
      workListContainer
    )
  );

  function renderApprovals(runObj) {
    const approvals = Array.isArray(runObj?.approvals) ? runObj.approvals : [];
    const pendingList = approvals.filter((a) => a.status === 'PENDING');
    if (pendingList.length === 0) {
      approvalContainer.hidden = true;
      clearChildren(approvalContainer);
      return;
    }
    approvalContainer.hidden = false;
    clearChildren(approvalContainer);
    approvalContainer.appendChild(
      h('h3', {
        className: 'approval-title',
        textContent: 'Chờ người duyệt',
      })
    );

    for (const item of pendingList) {
      const approveBtn = h('button', {
        type: 'button',
        className: 'btn-primary',
        'data-action': 'approve',
        'data-approval-id': item.id,
        textContent: 'Duyệt',
        onClick: () => handlers.onApprove?.(item.id, 'APPROVED'),
      });
      const rejectBtn = h('button', {
        type: 'button',
        className: 'btn-danger',
        'data-action': 'reject',
        'data-approval-id': item.id,
        textContent: 'Từ chối',
        onClick: () => handlers.onApprove?.(item.id, 'REJECTED'),
      });

      const stepLabel = item.task_key ? getTaskTitle(item.task_key) : '—';
      const reasonRaw = item.reason || 'Cần người phụ trách xác nhận trước khi thực hiện.';
      const reasonFriendly = reasonRaw
        .replace('meta_ads.create_draft', TOOL_LABEL['meta_ads.create_draft'] || 'Tạo bản nháp quảng cáo')
        .replace('budget', 'ngân sách')
        .replace('approval threshold', 'ngưỡng cần duyệt');

      approvalContainer.appendChild(
        h(
          'div',
          { className: 'approval-item', title: reasonRaw },
          h(
            'div',
            { className: 'approval-line' },
            h('strong', {}, 'Bước: '),
            h('span', { title: item.task_key || '', textContent: stepLabel })
          ),
          h(
            'div',
            { className: 'approval-line' },
            h('strong', {}, 'Lý do: '),
            h('span', { title: reasonRaw, textContent: reasonFriendly })
          ),
          h(
            'div',
            { className: 'approval-line' },
            h('strong', {}, 'Số tiền: '),
            h(
              'span',
              {
                textContent:
                  item.amount !== undefined && item.amount !== null ? `${item.amount} PHP` : '—',
              }
            )
          ),
          h('div', { className: 'approval-actions' }, approveBtn, rejectBtn)
        )
      );
    }
  }

  function renderOverview(force = false) {
    const runObj = state.currentRun;
    const runMeta = runObj?.run || runObj || null;
    const tasks = getTasksList(runObj);
    const counts = overviewCounts(runObj || { tasks: [], approvals: [] });

    const sig = JSON.stringify({
      hasRun: Boolean(runObj),
      seq: runMeta?.seq ?? null,
      inject: runMeta?.inject || [],
      selectedTaskKey: state.selectedTaskKey,
      counts,
      approvals: runObj?.approvals || [],
      tasks: tasks.map((t) => ({
        k: t.task_key,
        a: t.agent_id,
        s: t.status,
        e: t.error,
      })),
    });

    if (!force && sig === state.lastOverviewSig) {
      return;
    }
    state.lastOverviewSig = sig;

    if (!runObj) {
      overviewSubtitle.textContent = 'Chưa có lượt nào';
      overviewSubtitle.title = '';
    } else {
      const seq = runMeta?.seq ?? 1;
      const inject = Array.isArray(runMeta?.inject) ? runMeta.inject : [];
      overviewSubtitle.textContent = `${runTitle({ seq })} · ${scenarioText(inject)}`;
      overviewSubtitle.title = inject.join(', ');
    }

    tileValueEls.running.textContent = String(counts.running);
    tileValueEls.todo.textContent = String(counts.todo);
    tileValueEls.awaiting.textContent = String(counts.awaiting);
    tileValueEls.failed.textContent = String(counts.failed);

    tileBoxEls.awaiting.classList.toggle('tile-amber', counts.awaiting > 0);
    tileBoxEls.failed.classList.toggle('tile-red', counts.failed > 0);

    renderApprovals(runObj);

    clearChildren(workListContainer);
    tasks.forEach((task, idx) => {
      const isSelected = state.selectedTaskKey === task.task_key;
      const statusCode = task.status || 'PENDING';
      const statusText = TASK_STATUS_LABEL[statusCode] || TASK_STATUS_LABEL.PENDING;
      const showErr = (statusCode === 'FAILED' || statusCode === 'SKIPPED') && (task.error || statusCode);

      const chip = h('span', {
        className: `badge badge-status status-${statusCode}`,
        'data-task-status': statusCode,
        title: statusCode,
        textContent: statusText,
      });

      const rowEl = h(
        'div',
        {
          className: isSelected ? 'work-row is-selected' : 'work-row',
          role: 'listitem',
          tabIndex: 0,
          'aria-current': isSelected ? 'true' : undefined,
          'data-task-key': task.task_key,
          'data-selected': isSelected ? 'true' : 'false',
          title: `${task.task_key} · Agent ${task.agent_id}`,
          onClick: () => selectTask(task.task_key),
          onKeydown: (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              selectTask(task.task_key);
            }
          },
        },
        h(
          'div',
          { className: 'work-row-main' },
          h('span', { className: 'work-row-num', textContent: `#${idx + 1}` }),
          h(
            'div',
            { className: 'work-row-texts' },
            h('span', {
              className: 'work-row-title',
              title: task.task_key,
              textContent: getTaskTitle(task.task_key),
            }),
            h('span', {
              className: 'work-row-role',
              title: `Agent ${task.agent_id}`,
              textContent: getRoleLabel(task.task_key, task.agent_id),
            })
          ),
          chip
        ),
        showErr
          ? h('div', {
              className: 'work-row-error',
              title: task.error || '',
              textContent: errorText(task.error || (statusCode === 'SKIPPED' ? 'dependency not completed' : '')),
            })
          : null
      );

      workListContainer.appendChild(rowEl);
    });
  }

  // ==================== 3. RIGHT TASK DRAWER ====================
  const drawerPanel = h('aside', {
    className: 'panel-card drawer-panel',
    'aria-label': 'Chi tiết bước công việc',
    hidden: true,
  });

  function renderDrawer(force = false) {
    if (!state.selectedTaskKey) {
      drawerPanel.hidden = true;
      state.lastDrawerSig = '';
      return;
    }
    drawerPanel.hidden = false;

    const tasks = getTasksList(state.currentRun);
    const task =
      tasks.find((t) => t.task_key === state.selectedTaskKey) ||
      DEFAULT_TASKS.find((t) => t.task_key === state.selectedTaskKey) || {
        task_key: state.selectedTaskKey,
        agent_id: '01',
        status: 'PENDING',
        depends_on: [],
        attempt: 0,
        error: null,
        started_at: null,
        finished_at: null,
        narrative: null,
        artifact: null,
      };

    const runStatus = state.currentRun?.run?.status || 'PENDING';
    const depTasks = (task.depends_on || []).map((depKey) => {
      const found = tasks.find((t) => t.task_key === depKey);
      return {
        task_key: depKey,
        status: found?.status || 'PENDING',
        artifact: found?.artifact || null,
      };
    });

    const sig = JSON.stringify({
      runStatus,
      task,
      depTasks,
      agentsCount: state.agents.length,
    });

    if (!force && sig === state.lastDrawerSig) {
      return;
    }
    state.lastDrawerSig = sig;

    const openDetailsKeys = new Set();
    for (const det of drawerPanel.querySelectorAll('details[data-detail-key]')) {
      if (det.open) openDetailsKeys.add(det.dataset.detailKey);
    }

    clearChildren(drawerPanel);

    const agent = getAgentForTask(task.task_key, task.agent_id);
    const zoneKey = TASK_ZONE[task.task_key] || 'command';
    const zoneInfo = ZONES[zoneKey] || { label: 'Khu vực', color: '#9aa0a6' };
    const roleLabel = getRoleLabel(task.task_key, task.agent_id);
    const taskLabel = getTaskTitle(task.task_key);

    const closeBtn = h('button', {
      type: 'button',
      'aria-label': 'Đóng ngăn kéo',
      textContent: 'Đóng ×',
      onClick: () => {
        selectTask(null);
      },
    });

    const zoneBadge = h(
      'span',
      {
        className: 'badge',
        style: `background:${zoneInfo.color}33;border-color:${zoneInfo.color};color:#2c251d;`,
      },
      zoneInfo.label
    );

    drawerPanel.appendChild(
      h(
        'div',
        { className: 'drawer-header' },
        h(
          'div',
          {},
          h(
            'div',
            { style: 'display:flex;gap:6px;align-items:center;margin-bottom:4px;flex-wrap:wrap;' },
            zoneBadge
          ),
          h('h3', {
            className: 'drawer-title',
            title: `Agent ${agent.id} · ${task.task_key}`,
            textContent: `${roleLabel} · ${taskLabel}`,
          }),
          h('p', {
            className: 'drawer-role',
            textContent: agent.responsibility || 'Thực thi công việc trong quy trình',
          })
        ),
        closeBtn
      )
    );

    const statusCode = task.status || 'PENDING';
    const statusBadge = h('span', {
      className: `badge badge-status status-${statusCode}`,
      'data-task-status': statusCode,
      title: statusCode,
      textContent: TASK_STATUS_LABEL[statusCode] || TASK_STATUS_LABEL.PENDING,
    });

    drawerPanel.appendChild(
      h(
        'div',
        { className: 'drawer-meta-grid' },
        h('div', {}, h('strong', {}, 'Trạng thái: '), statusBadge),
        h('div', {}, h('strong', {}, 'Số lần thử: '), h('span', { textContent: String(task.attempt ?? 0) })),
        h(
          'div',
          {},
          h('strong', {}, 'Bắt đầu: '),
          h('span', { title: task.started_at || '', textContent: formatTime(task.started_at) })
        ),
        h(
          'div',
          {},
          h('strong', {}, 'Kết thúc: '),
          h('span', { title: task.finished_at || '', textContent: formatTime(task.finished_at) })
        )
      )
    );

    if (task.error) {
      drawerPanel.appendChild(
        h('div', {
          className: 'drawer-error',
          title: task.error,
          textContent: `Lỗi: ${errorText(task.error)}`,
        })
      );
    }

    if (task.status === 'FAILED' && runStatus === 'FAILED') {
      const retryBtn = h('button', {
        type: 'button',
        className: 'btn-warning',
        'data-action': 'retry-task',
        'data-task-key': task.task_key,
        textContent: 'Thử lại bước này',
        onClick: () => handlers.onRetry?.(task.task_key),
      });
      drawerPanel.appendChild(h('div', {}, retryBtn));
    }

    // Đầu vào (kết quả của các bước trước, by TASK_TITLE)
    const inputSection = h(
      'div',
      {},
      h('h4', { className: 'drawer-section-title', textContent: 'Đầu vào' })
    );
    if (depTasks.length === 0) {
      inputSection.appendChild(
        h('p', {
          style: 'margin:0;font-size:12px;color:var(--text-muted);',
          textContent: 'Bước khởi đầu — nhận trực tiếp mục tiêu kinh doanh.',
        })
      );
    } else {
      for (const dep of depTasks) {
        const dKey = `in:${dep.task_key}`;
        const depTitle = getTaskTitle(dep.task_key);
        const depStatusLabel = TASK_STATUS_LABEL[dep.status] || TASK_STATUS_LABEL.PENDING;
        const depSummary = dep.artifact?.summary
          ? humanizeText(dep.artifact.summary)
          : 'Chưa có kết quả';
        const detailsEl = h(
          'details',
          {
            className: 'artifact-details',
            'data-detail-key': dKey,
            open: openDetailsKeys.has(dKey),
          },
          h('summary', {
            title: `${dep.task_key} (${dep.status})`,
            textContent: `${depTitle} (${depStatusLabel}) — ${depSummary}`,
          }),
          h('pre', {
            className: 'json-viewer',
            textContent: dep.artifact ? JSON.stringify(dep.artifact, null, 2) : 'Chưa có dữ liệu',
          })
        );
        inputSection.appendChild(detailsEl);
      }
    }
    drawerPanel.appendChild(inputSection);

    // Đầu ra (diễn giải + collapsed Chi tiết kỹ thuật (JSON))
    const outputSection = h(
      'div',
      {},
      h('h4', { className: 'drawer-section-title', textContent: 'Đầu ra' })
    );
    const narrativeText = task.narrative || task.artifact?.narrative;
    if (narrativeText) {
      outputSection.appendChild(
        h('p', {
          className: 'narrative-box',
          textContent: humanizeText(narrativeText),
        })
      );
    } else {
      outputSection.appendChild(
        h('p', {
          style: 'margin:0 0 6px 0;font-size:12px;color:var(--text-muted);',
          textContent: 'Chưa có diễn giải cho bước này.',
        })
      );
    }

    const outKey = `out:${task.task_key}`;
    outputSection.appendChild(
      h(
        'details',
        {
          className: 'artifact-details',
          'data-detail-key': outKey,
          open: openDetailsKeys.has(outKey),
        },
        h('summary', {
          title: task.artifact_type || task.artifact?.type || 'JSON',
          textContent: 'Chi tiết kỹ thuật (JSON)',
        }),
        h('pre', {
          className: 'json-viewer',
          textContent: task.artifact
            ? JSON.stringify(task.artifact, null, 2)
            : 'Chưa có dữ liệu kỹ thuật',
        })
      )
    );
    drawerPanel.appendChild(outputSection);
  }

  // ==================== 6. 2D OVERVIEW ====================
  const view2dContainer = h('section', {
    className: 'panel-card view-2d-container',
    'aria-label': 'Chế độ Tổng quan 2D',
  });

  function computeDagLayout(tasks) {
    const byKey = new Map();
    for (const t of tasks) {
      byKey.set(t.task_key, t);
    }
    const memoLayer = new Map();
    function getLayer(key, visiting = new Set()) {
      if (memoLayer.has(key)) return memoLayer.get(key);
      if (visiting.has(key)) return 0;
      visiting.add(key);
      const t = byKey.get(key);
      const deps = Array.isArray(t?.depends_on) ? t.depends_on : [];
      if (deps.length === 0) {
        memoLayer.set(key, 0);
        return 0;
      }
      let maxDep = 0;
      for (const d of deps) {
        maxDep = Math.max(maxDep, getLayer(d, new Set(visiting)));
      }
      const layer = maxDep + 1;
      memoLayer.set(key, layer);
      return layer;
    }

    const layersMap = new Map();
    let maxLayer = 0;
    for (const t of tasks) {
      const l = getLayer(t.task_key);
      maxLayer = Math.max(maxLayer, l);
      if (!layersMap.has(l)) layersMap.set(l, []);
      layersMap.get(l).push(t);
    }

    const positions = new Map();
    const colSpacing = 118;
    const startX = 68;
    const svgHeight = 250;
    const centerY = svgHeight / 2;

    for (let l = 0; l <= maxLayer; l++) {
      const group = layersMap.get(l) || [];
      const x = startX + l * colSpacing;
      if (group.length === 1) {
        const offset = l > 0 && l < 10 && l % 2 === 1 ? -18 : l > 0 && l < 10 ? 18 : 0;
        positions.set(group[0].task_key, { x, y: centerY + offset, layer: l });
      } else {
        const gap = 90;
        const totalH = (group.length - 1) * gap;
        group.forEach((item, idx) => {
          positions.set(item.task_key, {
            x,
            y: centerY - totalH / 2 + idx * gap,
            layer: l,
          });
        });
      }
    }

    const svgWidth = Math.max(1220, startX * 2 + maxLayer * colSpacing + 40);
    return { positions, svgWidth, svgHeight };
  }

  function render2dOverview(force = false) {
    const tasks = getTasksList(state.currentRun);
    const sig = JSON.stringify({
      runStatus: state.currentRun?.run?.status || 'PENDING',
      selectedTaskKey: state.selectedTaskKey,
      tasks: tasks.map((t) => ({
        k: t.task_key,
        s: t.status,
        a: t.attempt,
        e: t.error,
        sum: t.artifact?.summary || null,
      })),
    });

    if (!force && sig === state.last2dSig) {
      return;
    }
    state.last2dSig = sig;
    clearChildren(view2dContainer);

    view2dContainer.appendChild(
      h(
        'div',
        { className: 'view-2d-header' },
        h('h2', {
          style: 'margin:0;font-size:15px;font-weight:800;',
          textContent: 'Tổng quan 2D — Sơ đồ quy trình 14 bước & Bảng trạng thái',
        }),
        h(
          'span',
          { style: 'font-size:12px;color:var(--text-muted);' },
          'Bấm vào bước bất kỳ trên sơ đồ hoặc dòng trong bảng để mở ngăn kéo chi tiết.'
        )
      )
    );

    const { positions, svgWidth, svgHeight } = computeDagLayout(tasks);
    const svg = svgEl('svg', {
      className: 'dag-svg',
      viewBox: `0 0 ${svgWidth} ${svgHeight}`,
      role: 'img',
      'aria-label': 'Sơ đồ quy trình 14 bước công việc',
    });

    const defs = svgEl(
      'defs',
      {},
      svgEl(
        'marker',
        {
          id: 'dep-arrow',
          viewBox: '0 0 10 10',
          refX: '9',
          refY: '5',
          markerWidth: '6',
          markerHeight: '6',
          orient: 'auto-start-reverse',
        },
        svgEl('path', { d: 'M 0 1 L 10 5 L 0 9 z', fill: '#7c6f5e' })
      )
    );
    svg.appendChild(defs);

    const edgesGroup = svgEl('g', { class: 'dag-edges' });
    const nodeW = 104;
    const nodeH = 50;

    for (const task of tasks) {
      const targetPos = positions.get(task.task_key);
      if (!targetPos) continue;
      const deps = Array.isArray(task.depends_on) ? task.depends_on : [];
      for (const depKey of deps) {
        const srcPos = positions.get(depKey);
        if (!srcPos) continue;
        const x1 = srcPos.x + nodeW / 2;
        const y1 = srcPos.y;
        const x2 = targetPos.x - nodeW / 2;
        const y2 = targetPos.y;
        const layerSpan = targetPos.layer - srcPos.layer;
        let dPath;
        if (layerSpan <= 1) {
          const midX = (x1 + x2) / 2;
          dPath = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;
        } else {
          const curveLift = y2 <= y1 ? -46 : 46;
          const cx1 = x1 + (x2 - x1) * 0.35;
          const cx2 = x1 + (x2 - x1) * 0.65;
          const cy = Math.min(Math.max(20, (y1 + y2) / 2 + curveLift), svgHeight - 20);
          dPath = `M ${x1} ${y1} C ${cx1} ${cy}, ${cx2} ${cy}, ${x2} ${y2}`;
        }
        edgesGroup.appendChild(
          svgEl('path', {
            d: dPath,
            fill: 'none',
            stroke: layerSpan > 2 ? 'rgba(124, 111, 94, 0.35)' : 'rgba(100, 86, 68, 0.75)',
            'stroke-width': layerSpan > 2 ? '1.2' : '1.8',
            'marker-end': 'url(#dep-arrow)',
          })
        );
      }
    }
    svg.appendChild(edgesGroup);

    const nodesGroup = svgEl('g', { class: 'dag-nodes' });
    tasks.forEach((task, idx) => {
      const pos = positions.get(task.task_key);
      if (!pos) return;
      const statusCode = task.status || 'PENDING';
      const st = NODE_VISUAL[statusCode] || NODE_VISUAL.PENDING;
      const zoneKey = TASK_ZONE[task.task_key] || 'command';
      const zoneColor = ZONES[zoneKey] ? ZONES[zoneKey].color : '#9aa0a6';
      const isSelected = state.selectedTaskKey === task.task_key;
      const titleText = getTaskTitle(task.task_key);
      const shortTitle = titleText.length > 16 ? `${titleText.slice(0, 15)}…` : titleText;
      const statusText = TASK_STATUS_LABEL[statusCode] || TASK_STATUS_LABEL.PENDING;

      const g = svgEl(
        'g',
        {
          class: 'dag-node',
          'data-task-key': task.task_key,
          'data-status': statusCode,
          tabindex: '0',
          role: 'button',
          'aria-label': `Bước ${idx + 1}: ${titleText} — ${statusText}`,
          opacity: String(st.opacity ?? 1),
          onClick: () => selectTask(task.task_key),
          onKeydown: (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              selectTask(task.task_key);
            }
          },
        },
        svgEl('rect', {
          class: 'dag-node-box',
          x: String(pos.x - nodeW / 2),
          y: String(pos.y - nodeH / 2),
          width: String(nodeW),
          height: String(nodeH),
          rx: '8',
          fill: '#ffffff',
          stroke: isSelected ? '#1d4ed8' : st.color,
          'stroke-width': isSelected ? '3' : '2',
        }),
        svgEl('rect', {
          x: String(pos.x - nodeW / 2),
          y: String(pos.y - nodeH / 2),
          width: String(nodeW),
          height: '6',
          rx: '4',
          fill: zoneColor,
        }),
        svgEl(
          'text',
          {
            x: String(pos.x),
            y: String(pos.y - 4),
            'text-anchor': 'middle',
            'font-size': '10.5',
            'font-weight': '700',
            fill: '#231d16',
          },
          shortTitle
        ),
        svgEl(
          'text',
          {
            x: String(pos.x),
            y: String(pos.y + 12),
            'text-anchor': 'middle',
            'font-size': '9.5',
            fill: '#5c5042',
          },
          statusText
        )
      );
      nodesGroup.appendChild(g);
    });
    svg.appendChild(nodesGroup);

    view2dContainer.appendChild(h('div', { className: 'dag-svg-wrapper' }, svg));

    const tbody = h('tbody');
    tasks.forEach((task, idx) => {
      const zoneKey = TASK_ZONE[task.task_key] || 'command';
      const zoneLabel = ZONES[zoneKey] ? ZONES[zoneKey].label : '—';
      const statusCode = task.status || 'PENDING';
      const statusText = TASK_STATUS_LABEL[statusCode] || TASK_STATUS_LABEL.PENDING;
      const depTitles = (task.depends_on || []).map((d) => getTaskTitle(d)).join(', ') || '—';
      const summaryOrErr = task.error
        ? `Lỗi: ${errorText(task.error)}`
        : humanizeText(task.artifact?.summary || task.narrative || '—');

      tbody.appendChild(
        h(
          'tr',
          {
            className: 'clickable-row',
            'data-task-key': task.task_key,
            onClick: () => selectTask(task.task_key),
          },
          h('td', { textContent: String(idx + 1) }),
          h('td', { title: task.task_key, textContent: getTaskTitle(task.task_key) }),
          h('td', { title: `Agent ${task.agent_id}`, textContent: getRoleLabel(task.task_key, task.agent_id) }),
          h('td', { textContent: zoneLabel }),
          h('td', { title: (task.depends_on || []).join(', '), textContent: depTitles }),
          h(
            'td',
            {},
            h('span', {
              className: `badge badge-status status-${statusCode}`,
              'data-task-status': statusCode,
              title: statusCode,
              textContent: statusText,
            })
          ),
          h('td', { textContent: String(task.attempt ?? 0) }),
          h('td', { textContent: summaryOrErr })
        )
      );
    });

    view2dContainer.appendChild(
      h(
        'table',
        { className: 'data-table' },
        h(
          'thead',
          {},
          h(
            'tr',
            {},
            h('th', { textContent: '#' }),
            h('th', { textContent: 'Bước công việc' }),
            h('th', { textContent: 'Vai trò' }),
            h('th', { textContent: 'Khu vực' }),
            h('th', { textContent: 'Phụ thuộc' }),
            h('th', { textContent: 'Trạng thái' }),
            h('th', { textContent: 'Số lần thử' }),
            h('th', { textContent: 'Tóm tắt / Lỗi' })
          )
        ),
        tbody
      )
    );
  }

  // ==================== 4. BOTTOM DOCK & 5 TABS ====================
  const TABS = [
    { id: 'summary', label: 'Kết quả cuối' },
    { id: 'checks', label: 'Kiểm tra' },
    { id: 'llm', label: 'Token & chi phí' },
    { id: 'logs', label: 'Nhật ký' },
    { id: 'history', label: 'Lịch sử' },
  ];

  const tabButtons = {};
  const tabPanels = {};

  for (const t of TABS) {
    tabButtons[t.id] = h('button', {
      type: 'button',
      role: 'tab',
      className: 'tab-btn',
      'aria-selected': String(state.activeTab === t.id),
      'data-tab': t.id,
      textContent: t.label,
      onClick: () => switchTab(t.id),
    });

    tabPanels[t.id] = h('div', {
      role: 'tabpanel',
      className: 'tab-panel',
      hidden: state.activeTab !== t.id,
      'data-tab-panel': t.id,
    });
  }

  const cancelRunBtn = h('button', {
    type: 'button',
    className: 'btn-danger',
    hidden: true,
    'data-action': 'cancel-run',
    textContent: 'Hủy lượt chạy',
    onClick: () => handlers.onCancel?.(),
  });

  function switchTab(tabId) {
    if (!tabPanels[tabId]) return;
    state.activeTab = tabId;
    for (const t of TABS) {
      const active = t.id === tabId;
      tabButtons[t.id].setAttribute('aria-selected', String(active));
      tabPanels[t.id].hidden = !active;
    }
    if (tabId === 'logs') {
      fetchDecisionLogIfNeeded(true);
    }
  }

  // --- Tab 1: Kết quả cuối ---
  function renderSummaryTab() {
    const tasks = getTasksList(state.currentRun);
    const summaryTask = tasks.find((t) => t.task_key === 'summary');
    const artifact = summaryTask?.artifact || null;
    const sig = JSON.stringify({
      status: summaryTask?.status || 'PENDING',
      error: summaryTask?.error || null,
      artifact,
      narrative: summaryTask?.narrative || null,
    });
    if (sig === state.lastSummarySig) return;
    state.lastSummarySig = sig;

    const container = tabPanels.summary;
    clearChildren(container);

    if (!artifact) {
      const stLabel = TASK_STATUS_LABEL[summaryTask?.status || 'PENDING'] || TASK_STATUS_LABEL.PENDING;
      container.appendChild(
        h('p', {
          style: 'margin:4px 0;color:var(--text-muted);',
          textContent: state.currentRun
            ? `Bước "${getTaskTitle('summary')}" đang ở trạng thái: ${stLabel}${summaryTask?.error ? ` — ${errorText(summaryTask.error)}` : ''}.`
            : 'Chưa có dữ liệu lượt chạy. Bấm "▶ Chạy kịch bản mới" để bắt đầu.',
        })
      );
      return;
    }

    const decCode = artifact.decision || 'HOLD_DRAFT';
    const decLabel = DECISION_LABEL[decCode] || DECISION_LABEL.HOLD_DRAFT;
    const decHint = DECISION_HINT[decCode] || '';

    const headerRow = h(
      'div',
      { style: 'display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:6px;' },
      h('strong', { textContent: 'Kết luận:' }),
      h('span', {
        className: `badge badge-status status-${decCode}`,
        'data-decision': decCode,
        title: decCode,
        textContent: decLabel,
      }),
      artifact.sku ? h('span', { className: 'badge badge-meta', textContent: `Sản phẩm: ${artifact.sku}` }) : null,
      decHint ? h('span', { className: 'decision-hint', textContent: decHint }) : null
    );
    container.appendChild(headerRow);

    const narrativeText = summaryTask?.narrative || artifact.narrative;
    if (narrativeText) {
      container.appendChild(
        h('p', { className: 'narrative-box', textContent: humanizeText(narrativeText) })
      );
    }

    const keyNumbers =
      artifact.key_numbers && typeof artifact.key_numbers === 'object' ? artifact.key_numbers : {};
    const knEntries = Object.entries(keyNumbers);
    if (knEntries.length > 0) {
      const tbody = h('tbody');
      for (const [k, v] of knEntries) {
        const displayVal =
          v === null || v === undefined
            ? '—'
            : k === 'risk_level' && RISK_VALUE_LABELS[v]
            ? RISK_VALUE_LABELS[v]
            : String(v);
        tbody.appendChild(
          h(
            'tr',
            { title: k },
            h('td', { title: k, textContent: KEY_NUMBER_LABELS[k] || 'Chỉ số kinh doanh' }),
            h('td', { title: String(v ?? ''), textContent: displayVal })
          )
        );
      }
      container.appendChild(
        h(
          'table',
          { className: 'data-table', style: 'margin-bottom:8px;' },
          h(
            'thead',
            {},
            h('tr', {}, h('th', { textContent: 'Ý nghĩa' }), h('th', { textContent: 'Giá trị' }))
          ),
          tbody
        )
      );
    }

    const nextSteps = Array.isArray(artifact.next_steps) ? artifact.next_steps : [];
    if (nextSteps.length > 0) {
      container.appendChild(
        h('strong', { style: 'font-size:12.5px;', textContent: 'Đề xuất bước tiếp theo:' })
      );
      const ul = h('ul', { style: 'margin:4px 0 0 18px;padding:0;' });
      for (const step of nextSteps) {
        ul.appendChild(h('li', { textContent: humanizeText(step) }));
      }
      container.appendChild(ul);
    }
  }

  // --- Tab 2: Kiểm tra ---
  function renderChecksTab() {
    const checksData = state.currentRun?.engines || {};
    const sig = JSON.stringify(checksData);
    if (sig === state.lastChecksSig) return;
    state.lastChecksSig = sig;

    const container = tabPanels.checks;
    clearChildren(container);

    const deptKeys = ['qa', 'audit', 'monitor'];
    const badgesBar = h('div', {
      style: 'display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px;align-items:center;',
    });
    const allFindings = [];

    for (const dk of deptKeys) {
      const deptObj = checksData[dk];
      const st = deptObj?.status || 'NOT_RUN';
      const deptLabel = ENGINE_LABEL[dk] || 'Bộ phận kiểm tra';
      const stLabel = CHECK_STATUS_LABEL[st] || CHECK_STATUS_LABEL.NOT_RUN;

      badgesBar.appendChild(
        h(
          'div',
          { style: 'display:inline-flex;align-items:center;gap:6px;', title: dk },
          h('strong', { textContent: `${deptLabel}:` }),
          h('span', {
            className: `badge badge-status status-${st}`,
            'data-check-status': st,
            title: st,
            textContent: stLabel,
          })
        )
      );
      if (Array.isArray(deptObj?.findings)) {
        for (const f of deptObj.findings) {
          allFindings.push({ dept: dk, ...f });
        }
      }
    }
    container.appendChild(badgesBar);

    const tbody = h('tbody');
    if (allFindings.length === 0) {
      tbody.appendChild(
        h(
          'tr',
          {},
          h('td', {
            colSpan: '5',
            textContent: 'Không có phát hiện lỗi hoặc cảnh báo nào.',
          })
        )
      );
    } else {
      for (const f of allFindings) {
        const sevCode = f.severity || 'WARN';
        const sevLabel = SEVERITY_LABEL[sevCode] || SEVERITY_LABEL.WARN;
        const ruleCode = f.rule || '';
        const ruleText = RULE_LABEL[ruleCode] || 'Quy tắc kiểm tra';
        const deptText = ENGINE_LABEL[f.dept] || 'Bộ phận kiểm tra';
        const stepText = f.task_key ? getTaskTitle(f.task_key) : 'Toàn lượt chạy';

        tbody.appendChild(
          h(
            'tr',
            {
              className: f.task_key ? 'clickable-row' : '',
              'data-rule': ruleCode,
              'data-task-key': f.task_key || '',
              onClick: () => {
                if (f.task_key) selectTask(f.task_key);
              },
            },
            h('td', { title: f.dept || '', textContent: deptText }),
            h('td', { title: ruleCode, textContent: ruleText }),
            h(
              'td',
              {},
              h('span', {
                className: `badge badge-status status-${sevCode}`,
                'data-check-status': sevCode,
                'data-severity': sevCode,
                title: sevCode,
                textContent: sevLabel,
              })
            ),
            h('td', { title: f.task_key || '', textContent: stepText }),
            h('td', {
              className: 'tech-detail-cell',
              title: f.detail || '',
              textContent: f.detail || '—',
            })
          )
        );
      }
    }

    container.appendChild(
      h(
        'table',
        { className: 'data-table' },
        h(
          'thead',
          {},
          h(
            'tr',
            {},
            h('th', { textContent: 'Bộ phận' }),
            h('th', { textContent: 'Vấn đề' }),
            h('th', { textContent: 'Mức độ' }),
            h('th', { textContent: 'Bước' }),
            h('th', { textContent: 'Chi tiết kỹ thuật' })
          )
        ),
        tbody
      )
    );
  }

  // --- Tab 3: Token & chi phí ---
  function renderLlmTab() {
    const llm = state.currentRun?.llm || { calls: 0, tokens: 0, cost_est: 0 };
    const tasks = getTasksList(state.currentRun);
    const modeCode = state.currentRun?.run?.mode || 'mock';
    const sig = JSON.stringify({
      llm,
      mode: modeCode,
      sources: tasks.map((t) => ({
        k: t.task_key,
        s: t.status,
        ns: t.artifact?.narrative_source || null,
      })),
    });
    if (sig === state.lastLlmSig) return;
    state.lastLlmSig = sig;

    const container = tabPanels.llm;
    clearChildren(container);

    const modeLabel =
      (modeCode === 'llm' || modeCode === 'deepseek') ? 'Dùng DeepSeek (có tính phí)' : 'Mô phỏng (mặc định, miễn phí)';

    container.appendChild(
      h(
        'div',
        { style: 'display:flex;flex-wrap:wrap;gap:14px;margin-bottom:8px;' },
        h('div', {}, h('strong', {}, 'Chế độ: '), h('span', { title: modeCode, textContent: modeLabel })),
        h('div', {}, h('strong', {}, 'Số lời gọi AI: '), h('span', { textContent: String(llm.calls ?? 0) })),
        h('div', {}, h('strong', {}, 'Tổng token: '), h('span', { textContent: String(llm.tokens ?? 0) })),
        h('div', {}, h('strong', {}, 'Chi phí ước tính: '), h('span', { textContent: `$${llm.cost_est ?? 0}` }))
      )
    );

    const tbody = h('tbody');
    for (const t of tasks) {
      const statusCode = t.status || 'PENDING';
      const statusText = TASK_STATUS_LABEL[statusCode] || TASK_STATUS_LABEL.PENDING;
      const ns = t.artifact?.narrative_source || '';
      const nsLabel = ns ? LLM_SOURCE_LABEL[ns] || 'Văn bản mẫu' : '—';

      tbody.appendChild(
        h(
          'tr',
          {
            className: 'clickable-row',
            onClick: () => selectTask(t.task_key),
          },
          h('td', { title: t.task_key, textContent: getTaskTitle(t.task_key) }),
          h('td', { title: `Agent ${t.agent_id}`, textContent: getRoleLabel(t.task_key, t.agent_id) }),
          h(
            'td',
            {},
            h('span', {
              className: `badge badge-status status-${statusCode}`,
              'data-task-status': statusCode,
              title: statusCode,
              textContent: statusText,
            })
          ),
          h('td', { title: ns, textContent: nsLabel })
        )
      );
    }

    container.appendChild(
      h(
        'table',
        { className: 'data-table' },
        h(
          'thead',
          {},
          h(
            'tr',
            {},
            h('th', { textContent: 'Bước công việc' }),
            h('th', { textContent: 'Vai trò' }),
            h('th', { textContent: 'Trạng thái' }),
            h('th', { textContent: 'Nguồn diễn giải' })
          )
        ),
        tbody
      )
    );
  }

  // --- Tab 4: Nhật ký ---
  function parseLogDetail(row) {
    if (row && typeof row.detail === 'string') {
      try { return JSON.parse(row.detail); } catch { return {}; }
    }
    return (row && row.detail) || {};
  }

  function reasonText(row) {
    const act = row.action ?? row.event_type ?? '';
    const detail = parseLogDetail(row);
    if (act === 'dispatch' && detail.reason) return detail.reason;
    if (act === 'dispatch_result' && detail.outcome) {
      return `Kết quả: ${DISPATCH_OUTCOME_LABEL[detail.outcome] || detail.outcome} (lần thử ${detail.attempt ?? 1})`;
    }
    if (act === 'plan_tasks' && Array.isArray(detail.needs_review) && detail.needs_review.length) {
      return `Giả định cần xem lại: ${detail.needs_review.join(', ')}`;
    }
    return '—';
  }

  function renderDecisionLogTab() {
    const container = tabPanels.logs;
    clearChildren(container);

    const planRow = state.decisionLogs.find((r) => (r.action ?? r.event_type) === 'plan_tasks');
    const planDetail = planRow ? parseLogDetail(planRow) : {};
    if (planDetail.currency_note || (Array.isArray(planDetail.needs_review) && planDetail.needs_review.length)) {
      const bits = [];
      if (planDetail.currency_note) bits.push(planDetail.currency_note);
      if (Array.isArray(planDetail.needs_review) && planDetail.needs_review.length) {
        const fields = planDetail.needs_review.map((k) => INPUT_SOURCE_LABEL[k] || k);
        bits.push(`Giả định cần xem lại: ${planDetail.needs_review.join(', ')} (${fields.join(', ')} dùng giá trị mặc định).`);
      }
      container.appendChild(
        h('div', { style: 'margin-bottom:8px;padding:6px 8px;border:1px solid var(--warn,#c99);border-radius:4px;'
          + 'font-size:12px;color:var(--text,inherit);background:var(--warn-bg,rgba(255,180,0,.08));',
          textContent: bits.join(' ') })
      );
    }

    const topRow = h(
      'div',
      { style: 'display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;' },
      h('span', {
        style: 'font-size:12px;color:var(--text-muted);',
        textContent: state.decisionLogLoading
          ? 'Đang tải nhật ký hoạt động...'
          : `Số mục ghi nhận: ${state.decisionLogs.length}`,
      }),
      h('button', {
        type: 'button',
        textContent: 'Làm mới nhật ký ↻',
        onClick: () => fetchDecisionLogIfNeeded(true),
      })
    );
    container.appendChild(topRow);

    const tbody = h('tbody');
    if (state.decisionLogs.length === 0) {
      const hasActiveRun = Boolean(state.currentRun);
      tbody.appendChild(
        h(
          'tr',
          {},
          h('td', {
            colSpan: '7',
            textContent: hasActiveRun
              ? 'Chưa có mục nhật ký nào cho lượt chạy này.'
              : 'Chưa chọn lượt chạy.',
          })
        )
      );
    } else {
      for (const row of state.decisionLogs) {
        const tsVal = row.ts ?? row.created_at ?? row.timestamp ?? '';
        const tkVal = row.task_key ?? '';
        const agVal = row.agent_id ?? '';
        const actVal = row.action ?? row.event_type ?? '';
        const toolVal = row.tool ?? row.target ?? '';

        let allowedText = '—';
        if (row.allowed !== undefined && row.allowed !== null) {
          allowedText = row.allowed ? 'Cho phép' : 'Chặn';
        } else if (row.decision === 'ALLOW') {
          allowedText = 'Cho phép';
        } else if (row.decision === 'DENY' || row.decision === 'BLOCK') {
          allowedText = 'Chặn';
        }

        const stepText = tkVal ? getTaskTitle(tkVal) : '—';
        const roleText = agVal ? AGENT_ROLE[agVal] || `Nhân sự #${agVal}` : '—';
        const actionText = actVal ? ACTION_LABEL[actVal] || 'Hoạt động hệ thống' : '—';
        const toolText = toolVal ? TOOL_LABEL[toolVal] || 'Nội bộ' : '—';

        tbody.appendChild(
          h(
            'tr',
            {},
            h('td', { title: String(tsVal), textContent: formatTime(tsVal) }),
            h('td', { title: String(tkVal), textContent: stepText }),
            h('td', { title: String(agVal), textContent: roleText }),
            h('td', { title: String(actVal), textContent: actionText }),
            h('td', { title: String(toolVal), textContent: toolText }),
            h('td', { title: String(row.allowed ?? row.decision ?? ''), textContent: allowedText }),
            h('td', { textContent: reasonText(row) })
          )
        );
      }
    }

    container.appendChild(
      h(
        'table',
        { className: 'data-table' },
        h(
          'thead',
          {},
          h(
            'tr',
            {},
            h('th', { textContent: 'Thời gian' }),
            h('th', { textContent: 'Bước' }),
            h('th', { textContent: 'Vai trò' }),
            h('th', { textContent: 'Hoạt động' }),
            h('th', { textContent: 'Công cụ' }),
            h('th', { textContent: 'Quyền thực thi' }),
            h('th', { textContent: 'Lý do / Nguồn' })
          )
        ),
        tbody
      )
    );
  }

  async function fetchDecisionLogIfNeeded(force = false) {
    const activeId = state.currentRun?.run?.['run' + '_id'];
    if (Array.isArray(state.currentRun?.decision_log)) {
      state.decisionLogs = state.currentRun.decision_log;
      state.decisionLogRunId = activeId || null;
      renderDecisionLogTab();
    }
    if (!activeId) {
      renderDecisionLogTab();
      return;
    }
    if (!force && state.decisionLogRunId === activeId && state.decisionLogs.length > 0) {
      return;
    }
    if (typeof fetch !== 'function') {
      renderDecisionLogTab();
      return;
    }
    state.decisionLogLoading = true;
    renderDecisionLogTab();
    try {
      const res = await fetch(`/runs/${activeId}/decision-log`);
      if (res && res.ok) {
        const body = await res.json();
        const list = Array.isArray(body)
          ? body
          : Array.isArray(body?.items)
          ? body.items
          : Array.isArray(body?.decision_log)
          ? body.decision_log
          : Array.isArray(body?.logs)
          ? body.logs
          : [];
        state.decisionLogs = list;
        state.decisionLogRunId = activeId;
      }
    } catch {
      // Keep existing logs on offline/test environment
    } finally {
      state.decisionLogLoading = false;
      renderDecisionLogTab();
    }
  }

  // --- Tab 5: Lịch sử ---
  function renderHistoryTab() {
    const container = tabPanels.history;
    clearChildren(container);

    const headerBar = h(
      'div',
      { style: 'display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;' },
      h('span', {
        style: 'font-size:12px;color:var(--text-muted);',
        textContent:
          'Các lượt chạy — bấm một dòng để xem lại (không chạy lại agent, không tốn lời gọi AI)',
      }),
      h('button', {
        type: 'button',
        'data-action': 'refresh-history',
        textContent: 'Làm mới ↻',
        onClick: () => handlers.onRefreshHistory?.(),
      })
    );
    container.appendChild(headerBar);

    const tbody = h('tbody');
    if (state.historyRuns.length === 0) {
      tbody.appendChild(
        h('tr', {}, h('td', { colSpan: '4', textContent: 'Chưa có lịch sử lượt chạy.' }))
      );
    } else {
      const curId = state.currentRun?.run?.['run' + '_id'];
      state.historyRuns.forEach((item, idx) => {
        const itemId = item['run' + '_id'] || '';
        const isCurrent = Boolean(curId && curId === itemId);
        const statusCode = item.status || 'PENDING';
        const statusText = RUN_STATUS_LABEL[statusCode] || RUN_STATUS_LABEL.PENDING;
        const seqNum = item.seq ?? state.historyRuns.length - idx;
        const injectList = Array.isArray(item.inject) ? item.inject : [];

        tbody.appendChild(
          h(
            'tr',
            {
              className: isCurrent ? 'clickable-row history-row-current' : 'clickable-row',
              'data-run-id': itemId,
              style: isCurrent ? 'background:rgba(91,141,239,0.14);font-weight:600;' : '',
              onClick: () => handlers.onOpenRun?.(itemId),
            },
            h('td', { textContent: `#${seqNum}` }),
            h('td', {
              title: injectList.join(', '),
              textContent: scenarioText(injectList),
            }),
            h(
              'td',
              {},
              h('span', {
                className: `badge badge-status status-${statusCode}`,
                title: statusCode,
                textContent: statusText,
              })
            ),
            h('td', {
              title: item.created_at || '',
              textContent: formatTime(item.created_at),
            })
          )
        );
      });
    }

    container.appendChild(
      h(
        'table',
        { className: 'data-table' },
        h(
          'thead',
          {},
          h(
            'tr',
            {},
            h('th', { textContent: 'Lượt' }),
            h('th', { textContent: 'Tình huống' }),
            h('th', { textContent: 'Kết quả' }),
            h('th', { textContent: 'Thời gian' })
          )
        ),
        tbody
      )
    );
  }

  // Zone legend bar inside bottom dock
  const zoneLegend = h(
    'div',
    { className: 'zone-legend', 'aria-label': 'Chú thích các khu vực phòng ban' },
    ...Object.entries(ZONES).map(([key, z]) =>
      h(
        'span',
        { className: 'zone-chip', 'data-zone': key },
        h('span', { className: 'zone-dot', style: `background:${z.color};` }),
        z.label
      )
    )
  );

  const bottomDock = h(
    'footer',
    { className: 'panel-card bottom-dock' },
    h(
      'div',
      { className: 'bottom-dock-header' },
      h('div', { className: 'tab-list', role: 'tablist' }, ...TABS.map((t) => tabButtons[t.id])),
      h('div', { style: 'display:flex;align-items:center;gap:10px;flex-wrap:wrap;' }, zoneLegend, cancelRunBtn)
    ),
    ...TABS.map((t) => tabPanels[t.id])
  );

  // ==================== 7. TOAST ERROR CONTAINER ====================
  const toastContainer = h('div', {
    className: 'toast-container',
    'aria-live': 'assertive',
  });

  // ==================== MOUNT WORKSPACE ====================
  const leftRail = h('div', { className: 'left-rail' }, overviewCard);
  const middleWorkspace = h('div', { className: 'workspace-middle' }, leftRail, view2dContainer, drawerPanel);

  // ---- bottom dock: drag the grip (mouse, touch, or Arrow keys) to resize, button to collapse; size is remembered
  const DOCK_KEY = 'levelup.dock';
  const dockMax = () => Math.round(window.innerHeight * 0.72);
  const clampDock = (px) => Math.max(120, Math.min(dockMax(), Math.round(px)));
  const dockGrip = h('div', {
    className: 'dock-grip',
    role: 'separator',
    tabIndex: 0,
    'aria-orientation': 'horizontal',
    'aria-label': 'Kéo để đổi chiều cao thanh dưới (phím mũi tên lên xuống cũng được)',
    title: 'Kéo để đổi chiều cao',
  });
  const dockToggle = h('button', { type: 'button', 'data-action': 'toggle-dock', 'aria-expanded': 'true', textContent: 'Thu gọn ▾' });
  function setDock({ height, collapsed }) {
    if (height !== undefined) bottomDock.style.setProperty('--dock-h', `${clampDock(height)}px`);
    if (collapsed !== undefined) {
      bottomDock.dataset.collapsed = String(collapsed);
      dockToggle.setAttribute('aria-expanded', String(!collapsed));
      dockToggle.textContent = collapsed ? 'Mở rộng ▴' : 'Thu gọn ▾';
    }
    try {
      localStorage.setItem(DOCK_KEY, JSON.stringify({ h: parseInt(bottomDock.style.getPropertyValue('--dock-h'), 10) || null, c: bottomDock.dataset.collapsed === 'true' }));
    } catch { /* storage unavailable: layout still works */ }
  }
  dockToggle.addEventListener('click', () => setDock({ collapsed: bottomDock.dataset.collapsed !== 'true' }));
  dockGrip.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    dockGrip.setPointerCapture(e.pointerId);
    document.body.dataset.resizing = 'true';
    setDock({ collapsed: false });
    const move = (ev) => setDock({ height: window.innerHeight - ev.clientY - 10 });
    const up = () => {
      document.body.removeAttribute('data-resizing');
      dockGrip.removeEventListener('pointermove', move);
      dockGrip.removeEventListener('pointerup', up);
      dockGrip.removeEventListener('pointercancel', up);
    };
    dockGrip.addEventListener('pointermove', move);
    dockGrip.addEventListener('pointerup', up);
    dockGrip.addEventListener('pointercancel', up);
  });
  dockGrip.addEventListener('dblclick', () => setDock({ height: 250, collapsed: false }));
  dockGrip.addEventListener('keydown', (e) => {
    const cur = bottomDock.getBoundingClientRect().height;
    if (e.key === 'ArrowUp') { e.preventDefault(); setDock({ height: cur + 30, collapsed: false }); }
    if (e.key === 'ArrowDown') { e.preventDefault(); setDock({ height: cur - 30 }); }
  });
  bottomDock.prepend(dockGrip);
  bottomDock.querySelector('.bottom-dock-header')?.prepend(dockToggle);
  window.addEventListener('resize', () => {  // keep a saved height inside the new window
    const cur = parseInt(bottomDock.style.getPropertyValue('--dock-h'), 10);
    if (cur && cur > dockMax()) bottomDock.style.setProperty('--dock-h', `${dockMax()}px`);
  });
  try {
    const saved = JSON.parse(localStorage.getItem(DOCK_KEY) || 'null');
    if (saved) setDock({ height: saved.h || undefined, collapsed: !!saved.c });
  } catch { /* ignore */ }

  root.appendChild(topBar);
  root.appendChild(middleWorkspace);
  root.appendChild(bottomDock);
  root.appendChild(toastContainer);

  // Initial render of static views
  renderOverview(true);
  renderSummaryTab();
  renderChecksTab();
  renderLlmTab();
  renderDecisionLogTab();
  renderHistoryTab();
  render2dOverview(true);

  // ==================== PUBLIC API ====================
  function setAgents(agents) {
    if (Array.isArray(agents) && agents.length > 0) {
      state.agents = agents;
      rebuildAgentMaps();
      for (const { select, defaultTask } of scenarioControls.values()) {
        if (select) populateTaskSelectOptions(select, defaultTask);
      }
      renderOverview(true);
      renderDrawer(true);
      render2dOverview(true);
      state.lastLlmSig = '';
      renderLlmTab();
    }
  }

  function render(run) {
    if (!run || typeof run !== 'object') return;
    const prevRunId = state.currentRun?.run?.['run' + '_id'];
    state.currentRun = run;

    const runMeta = run.run || {};
    const status = runMeta.status || 'PENDING';
    runStatusBadge.className = `badge badge-status status-${status}`;
    runStatusBadge.setAttribute('data-run-status', status);
    runStatusBadge.title = status;
    runStatusBadge.textContent = RUN_STATUS_LABEL[status] || RUN_STATUS_LABEL.PENDING;

    const tasks = getTasksList(run);
    const doneCount = tasks.filter((t) => DONE_STATUSES.has(t.status)).length;
    stepBadge.textContent = `Bước ${doneCount}/14`;

    cancelRunBtn.hidden = !CANCELLABLE_STATUSES.has(status);

    renderOverview(false);

    if (state.selectedTaskKey) {
      renderDrawer(false);
    }

    renderSummaryTab();
    renderChecksTab();
    renderLlmTab();
    if (state.activeTab === 'logs') {
      const newRunId = runMeta['run' + '_id'];
      if (newRunId && newRunId !== prevRunId) {
        fetchDecisionLogIfNeeded(true);
      } else if (Array.isArray(run.decision_log)) {
        state.decisionLogs = run.decision_log;
        renderDecisionLogTab();
      }
    }

    renderHistoryTab();
    render2dOverview(false);
  }

  function renderHistory(runs) {
    state.historyRuns = Array.isArray(runs) ? runs : [];
    renderHistoryTab();
    renderOverview(true);
  }

  function selectTask(taskKey) {
    state.selectedTaskKey = taskKey || null;
    renderOverview(true);
    renderDrawer(true);
    render2dOverview(false);
  }

  function setView(mode) {
    const normalized = mode === '2d' ? '2d' : '3d';
    state.viewMode = normalized;
    if (document.body) {
      document.body.dataset.view = normalized;
    }
    const is2d = normalized === '2d';
    viewToggleBtn.setAttribute('aria-pressed', String(is2d));
    viewToggleBtn.textContent = is2d ? 'Tổng quan (3D)' : 'Tổng quan (2D)';
    view2dContainer.style.display = is2d ? 'flex' : '';
    if (is2d) {
      render2dOverview(false);
    }
  }

  function showError(message) {
    if (!message) return;
    const toast = h('div', { className: 'toast-item', role: 'alert' });
    const msgSpan = h('span', { textContent: errorText(message) });
    const dismissBtn = h('button', {
      type: 'button',
      'aria-label': 'Đóng thông báo lỗi',
      textContent: 'Đóng ×',
      onClick: () => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      },
    });
    toast.appendChild(msgSpan);
    toast.appendChild(dismissBtn);
    toastContainer.appendChild(toast);
  }

  return {
    setAgents,
    render,
    renderHistory,
    selectTask,
    setView,
    showError,
  };
}
