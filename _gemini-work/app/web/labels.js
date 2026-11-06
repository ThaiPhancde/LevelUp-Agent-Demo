// Business wording for everything the dashboard shows (Claude). One place, so panels and the 3D scene say the same thing.
// Technical codes (bad_cost, FAILED, run ids...) stay in the API and in "chi tiết kỹ thuật"; people read these labels.

export const RUN_STATUS_LABEL = {
  PENDING: 'Sắp chạy', RUNNING: 'Đang chạy', WAITING_APPROVAL: 'Chờ duyệt',
  COMPLETED: 'Hoàn tất', FAILED: 'Có lỗi', CANCELLED: 'Đã hủy',
};

export const TASK_STATUS_LABEL = {
  PENDING: 'Chờ làm', RUNNING: 'Đang làm', COMPLETED: 'Xong', FAILED: 'Lỗi', SKIPPED: 'Bỏ qua', CANCELLED: 'Đã hủy',
};

// Work items of one run, in business words (task_key -> title).
export const TASK_TITLE = {
  plan: 'Lập kế hoạch', market: 'Phân tích thị trường', product: 'Chọn sản phẩm', offer: 'Tính giá và hòa vốn',
  content: 'Soạn nội dung quảng cáo', campaign: 'Lập chiến dịch (bản nháp)', leads: 'Xử lý khách tiềm năng',
  care: 'Chăm sóc sau bán', kpi: 'Đo hiệu quả bán hàng', finance: 'Đánh giá lợi nhuận và rủi ro',
  qa: 'Kiểm tra chất lượng', audit: 'Kiểm tra quyền và an toàn', monitor: 'Theo dõi vận hành', summary: 'Báo cáo tổng kết',
};

// Who does it (agent id -> role).
export const AGENT_ROLE = {
  '01': 'Giám đốc kinh doanh', '02': 'Nghiên cứu thị trường', '03': 'Tìm sản phẩm', '04': 'Định giá và chiến lược',
  '05': 'Nội dung và sáng tạo', '06': 'Chạy quảng cáo', '07': 'Tư vấn và chốt đơn', '08': 'Chăm sóc khách hàng',
  '09': 'Phân tích bán hàng', '10': 'Tài chính và rủi ro', '11': 'Kiểm tra chất lượng', '12': 'Kiểm toán', '13': 'Giám sát',
};

// Situations the demo can simulate (the API calls them "inject"). `needsTask`: the situation happens at one step.
export const SCENARIOS = [
  { id: 'bad_cost', label: 'Giá vốn nhà cung cấp bị nhập sai',
    hint: 'Giá vốn thành 9.999 PHP. Bộ phận Kiểm tra chất lượng phải phát hiện.' },
  { id: 'publish_attempt', label: 'Nhân viên cố đăng quảng cáo thật',
    hint: 'Agent quảng cáo thử đăng thật. Bộ phận Kiểm toán phải chặn, chiến dịch giữ bản nháp.' },
  { id: 'timeout', label: 'Một bước bị treo', needsTask: true,
    hint: 'Bước được chọn không trả lời kịp. Bộ phận Giám sát ghi nhận, bấm Thử lại để làm tiếp.' },
  { id: 'missing_field', label: 'Một bước trả kết quả thiếu thông tin', needsTask: true,
    hint: 'Kết quả thiếu mục bắt buộc nên bị từ chối, không chuyển cho bước sau.' },
  { id: 'empty_response', label: 'Một bước không trả lời nội dung', needsTask: true,
    hint: 'Agent trả về rỗng. Hệ thống coi là lỗi, không báo thành công giả.' },
];

export const SCENARIO_LABEL = Object.fromEntries(SCENARIOS.map((s) => [s.id, s.label]));

// Findings of the three checking departments (rule code -> what it means).
export const RULE_LABEL = {
  schema: 'Kết quả thiếu hoặc sai cấu trúc', reference: 'Giá vốn lệch so với nguồn gốc',
  arithmetic: 'Phép tính không khớp', consistency: 'Số liệu giữa các bước không khớp',
  narrative: 'Lời diễn giải có con số lạ', blocked_action: 'Hành động bị chặn',
  not_via_gateway: 'Hành động không đi qua cổng kiểm soát', draft_only: 'Chiến dịch không còn ở bản nháp',
  pending_approval: 'Đang chờ người duyệt', timeout: 'Bước bị quá thời gian', empty_response: 'Bước không trả nội dung',
  task_failed: 'Bước bị lỗi', skipped: 'Bước bị bỏ qua', retried: 'Bước phải làm lại',
  llm_errors: 'Lỗi khi gọi mô hình AI', token_budget: 'Hết hạn mức token',
};

export const SEVERITY_LABEL = { FAIL: 'Nghiêm trọng', WARN: 'Cần lưu ý' };
export const CHECK_STATUS_LABEL = { PASS: 'Đạt', WARN: 'Cần lưu ý', FAIL: 'Không đạt', NOT_RUN: 'Chưa chạy' };
export const ENGINE_LABEL = { qa: 'Kiểm tra chất lượng', audit: 'Kiểm toán quyền', monitor: 'Giám sát vận hành' };

// Commander's conclusion.
export const DECISION_LABEL = {
  DRAFT_READY: 'Sẵn sàng để duyệt', HOLD_DRAFT: 'Giữ ở bản nháp', NEEDS_REVIEW: 'Cần xem lại',
};
export const DECISION_HINT = {
  DRAFT_READY: 'Các kiểm tra đều đạt và rủi ro chấp nhận được. Chờ người duyệt trước khi chạy thật.',
  HOLD_DRAFT: 'Kiểm tra đạt nhưng kế hoạch đang lỗ. Giữ chiến dịch ở bản nháp, chờ người quyết định.',
  NEEDS_REVIEW: 'Có bộ phận kiểm tra báo không đạt. Cần xem lại trước khi đi tiếp.',
};

export const LLM_SOURCE_LABEL = { mock: 'Văn bản mẫu', llm: 'Mô hình AI', mock_budget: 'Văn bản mẫu (hết hạn mức)' };

// Backend error strings -> plain Vietnamese. Unknown text is shown as is.
export function errorText(error) {
  const e = String(error || '');
  const t = e.match(/^timeout after ([\d.]+)s/i);
  if (t) return `Quá thời gian chờ (${t[1]} giây)`;
  if (/empty narrative|empty model response/i.test(e)) return 'Agent không trả về nội dung';
  if (/failed schema/i.test(e)) return 'Kết quả thiếu thông tin bắt buộc nên bị từ chối';
  if (/^interrupted/i.test(e)) return 'Bị gián đoạn khi hệ thống dừng hoặc khởi động lại';
  if (/dependency not completed/i.test(e)) return 'Bỏ qua vì bước trước chưa xong';
  return e || 'Không rõ nguyên nhân';
}

// "Lượt #12" plus what was simulated, from a run row ({seq, inject}).
export function scenarioText(inject = []) {
  if (!inject.length) return 'Chạy bình thường';
  return 'Thử: ' + inject.map((i) => {
    const [id, task] = i.split(':');
    return SCENARIO_LABEL[id] ? (task ? `${SCENARIO_LABEL[id]} (${TASK_TITLE[task] || task})` : SCENARIO_LABEL[id]) : i;
  }).join('; ');
}

export const runTitle = (run) => `Lượt #${run.seq ?? '?'}`;

export function formatTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });
}

// Counters for the overview card: tasks of the current run.
export function overviewCounts(run) {
  const tasks = run?.tasks || [];
  const n = (s) => tasks.filter((t) => t.status === s).length;
  return {
    running: n('RUNNING'),
    todo: n('PENDING'),
    awaiting: (run?.approvals || []).filter((a) => a.status === 'PENDING').length,
    failed: n('FAILED'),
    done: n('COMPLETED'),
  };
}

// Decision-log vocabulary (action codes and tool names -> what happened).
export const ACTION_LABEL = {
  plan_tasks: 'Lập kế hoạch', task_completed: 'Hoàn tất bước', task_failed: 'Bước bị lỗi', task_skipped: 'Bỏ qua bước',
  task_retry: 'Thử lại bước', task_interrupted: 'Bước bị gián đoạn', tool_call: 'Gọi công cụ bên ngoài',
  engine_result: 'Kết quả kiểm tra', human_approval: 'Người duyệt quyết định', run_finished: 'Kết thúc lượt',
  run_cancelled: 'Hủy lượt', run_recovered: 'Khôi phục sau khi khởi động lại',
};

export const TOOL_LABEL = {
  'meta_ads.create_draft': 'Tạo bản nháp quảng cáo', 'meta_ads.publish': 'Đăng quảng cáo thật',
  'crm.reply_draft': 'Soạn trả lời khách (bản nháp)', 'crm.ticket_note': 'Ghi chú chăm sóc (bản nháp)',
  'payment.charge': 'Thanh toán thật', 'messaging.send': 'Gửi tin nhắn thật',
};

export const APPROVAL_STATUS_LABEL = { PENDING: 'Chờ duyệt', APPROVED: 'Đã duyệt', REJECTED: 'Đã từ chối' };

// Render old stored runs and new narratives alike, without rewriting original artifacts.
const BUSINESS_WORDS = {
  ...TASK_STATUS_LABEL, ...DECISION_LABEL, ...CHECK_STATUS_LABEL,
  WAITING_APPROVAL: RUN_STATUS_LABEL.WAITING_APPROVAL,
  HIGH: 'cao', MEDIUM: 'trung bình', LOW: 'thấp', DRAFT: 'bản nháp',
  Commander: 'Giám đốc kinh doanh', QA: 'Kiểm tra chất lượng', Audit: 'Kiểm toán', Monitor: 'Giám sát',
  product_question: 'hỏi về sản phẩm', price_question: 'hỏi giá', shipping_question: 'hỏi vận chuyển',
  order_status: 'hỏi tình trạng đơn', complaint: 'khiếu nại', return_request: 'xin đổi trả',
};
export function businessText(raw) {
  return String(raw ?? '').replace(/\b[A-Za-z][A-Za-z_]*\b/g, (word) => BUSINESS_WORDS[word] ?? word);
}
