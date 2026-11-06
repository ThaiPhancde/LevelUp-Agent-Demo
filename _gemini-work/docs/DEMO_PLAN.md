# Thiết kế bản Demo 13 AI Agents và kế hoạch triển khai cho Claude

Phiên bản 1.0 — 04/11/2026. Nguồn phạm vi: `../../DEMO_ONLY.md`. Bối cảnh: `../../level-up-os-full-summary.md`. Khung phương pháp: dự án `D:\Purchasing System` (prompt nền + phase + decisions/status/handoff).

Trạng thái từng phase lấy từ `DEMO_PHASE_STATUS.md`, không lấy từ tài liệu này.

---

## 1. Mục tiêu và phạm vi

**Mục tiêu.** Một bản demo chạy local (Docker Compose, một container) chứng minh 13 AI Agents nhận nhiệm vụ, phối hợp theo dependency, dùng dữ liệu mock, kiểm tra chéo bằng engine deterministic và tạo kết quả kinh doanh giả lập. Người xem mở `http://localhost:8088/dashboard`, bấm Start Demo và quan sát toàn bộ quá trình.

**Đây là môi trường demo để các agent demo làm việc với nhau**, không phải hệ thống kinh doanh. Mọi "hệ thống ngoài" (Meta Ads, POS, nhà cung cấp, 3PL, CRM) là Mock API trong cùng container.

**Trong phạm vi:** 13 vai trò (10 business + 3 supervisory), 3 Control Engine (QA, Audit, Monitoring), Commander + Workflow Engine, Mock Business Environment Philippines, Dashboard, Mock Mode + DeepSeek Mode, 5 kịch bản E2E, đánh giá ARIS, đóng gói.

**Ngoài phạm vi:** production, cloud, Kubernetes, PostgreSQL, tích hợp thật, thanh toán, agent thứ 14, đổi LLM provider, n8n/BigQuery thật (chỉ mô phỏng nguyên tắc).

### 1.1 Ánh xạ sang Level Up OS (mô phỏng nguyên tắc, không xây hệ thống)

| Nguyên tắc Level Up OS | Cách demo thể hiện |
|---|---|
| One Source of Truth | Một SQLite; mọi số liệu agent dùng đều lấy từ Mock API, không tự bịa |
| Rules First, AI Second | QA/Audit/Monitoring Engine chạy bằng code trước; LLM chỉ diễn giải |
| Human-in-the-Loop | Hành động vượt ngưỡng → run chuyển `WAITING_APPROVAL`, nút Duyệt/Từ chối trên dashboard (M-05) |
| Think ≠ Act ≠ Learn | Agent chỉ "Think" (tạo artifact); "Act" chỉ qua Mock Tool Gateway có kiểm quyền; không có "Learn" trong demo |
| Observable by Design | Bảng `decision_log` + `llm_calls` (token, chi phí ước tính), xem được trên dashboard |
| Security & RBAC | Agent Registry gán quyền READ/WRITE_DRAFT/WRITE_EXTERNAL cho từng agent; Audit Engine chặn |
| Circuit breaker | Monitoring Engine: timeout, retry bất thường, ngân sách token theo run |

---

## 2. Yêu cầu truy vết

Mã `R-nn` dùng xuyên suốt status/test report. Cột "Nguồn" là mục trong `DEMO_ONLY.md`.

| Mã | Yêu cầu | Nguồn | Phase |
|---|---|---|---|
| R-01 | 13 vai trò đúng tên, mỗi vai trò có nhiệm vụ, tool, schema I/O, quyền riêng | A.1, P4 | 4 |
| R-02 | 3 Engine deterministic độc lập LLM; supervisor chỉ đọc bằng chứng engine | A.1, P5 | 5 |
| R-03 | Một yêu cầu tự nhiên → chuỗi 13 bước, agent sau dùng kết quả agent trước | A.2, P3 | 3–4 |
| R-04 | Không phải "13 lần gọi DeepSeek cùng prompt" | A.2 | 4 |
| R-05 | Sửa lỗi LLM: encoding, `finish_reason=length`, empty result, token thấp, timeout/retry, token usage, "rỗng nhưng báo thành công" | P1 | 1 |
| R-06 | Mock Market/Ads/Products/Suppliers/Campaigns/Leads/Orders/Logistics/Conversations/Finance; fixtures cố định Philippines | P2 | 2 |
| R-07 | Mock API cho agent truy vấn; không kết nối ngoài | P2 | 2 |
| R-08 | Task có dependency, trạng thái 6 giá trị, retry, cancel, replay không gọi LLM, checkpoint qua restart | P3 | 3 |
| R-09 | Artifact chuyên biệt theo agent, có schema, số học bằng Python | P4 | 4 |
| R-10 | Mock Mode chạy không cần DeepSeek; LLM Mode có hạn mức token/ngân sách | P4 | 1, 4 |
| R-11 | Error injection: cost 9.999, timeout, artifact thiếu trường, publish thật, response rỗng | P5 | 5 |
| R-12 | Dashboard đủ 10 thành phần tối thiểu, Mock Mode mặc định; trực quan chính là văn phòng 3D, có chế độ 2D dự phòng (D-16) | P6 | 6 |
| R-13 | Đánh giá ARIS: license, dependency, Docker Linux, Keychain, adapter, fallback | P7 | 7 |
| R-14 | 5 kịch bản E2E có bằng chứng PASS/FAIL | P8 | 8 |
| R-15 | Đóng gói: compose, README, reset data, API doc, sơ đồ, bảng code/mock/LLM, hạn chế, `DEMO_FINAL_REPORT.md` | P9 | 9 |
| R-16 | ≤ 2 lời gọi DeepSeek thật trong triển khai; không lộ key | C | mọi phase |
| R-17 | 6 tài liệu `docs/DEMO_*.md` duy trì, trạng thái phase 5 giá trị | C | mọi phase |

---

## 3. Kiến trúc đề xuất (TO-BE)

Giữ **modular monolith** FastAPI, một container, một SQLite. Chi tiết AS-IS và sơ đồ: `DEMO_ARCHITECTURE.md`.

```
app/
  main.py            # FastAPI app, mount router + static dashboard (giữ tên để Dockerfile không đổi)
  config.py          # env: model, key, MOCK_DEFAULT=true, token budget, approval threshold
  db.py              # sqlite connect, migrate(), helper
  core/
    registry.py      # 13 agent: id, name, role, tools, input/output schema, permissions
    workflow.py      # Commander: objective → task graph (dependency), state machine, retry/cancel/replay, checkpoint
    artifacts.py     # pydantic schema cho từng artifact
    gateway.py       # Mock Tool Gateway: điểm duy nhất "Act"; kiểm quyền → Audit
  agents/            # 13 module: mỗi agent = compute(inputs)->artifact (Python) + narrate(artifact)->text (LLM/mock)
  engines/
    qa.py  audit.py  monitor.py        # deterministic, không import llm
  mock/
    fixtures/*.json  # Philippines dataset cố định, có cờ "synthetic": true
    api.py           # /mock/market, /mock/ads, ... đọc fixtures + override theo run (error injection)
  llm/
    deepseek.py      # client: timeout, retry backoff, max_tokens, usage log, empty→error
    mock_llm.py      # trả văn bản mẫu theo agent, không gọi mạng
  web/               # Phase 6, đặc tả docs/DEMO_DASHBOARD_3D.md
    dashboard.html   # khung + thanh công cụ + panel
    office3d.js      # scene văn phòng 3D (three.js)
    office-layout.js # vị trí phòng, màu khu, đạo cụ (dữ liệu thuần)
    panels.js        # ngăn kéo, tab, chế độ Tổng quan 2D
    vendor/          # three.js bản cố định, chạy offline
tests/
  unit/  integration/  e2e/
docs/
```

**Luồng một run:**
1. Dashboard `POST /runs {objective, mode}` → Commander tạo `run` + 13 `tasks` với dependency (mục 4).
2. Workflow Engine chạy task theo topological order; task chỉ RUNNING khi mọi dependency bắt buộc COMPLETED.
3. Mỗi task: lấy artifact upstream → `compute()` bằng Python với dữ liệu Mock API → `narrate()` (mock hoặc DeepSeek) → validate schema → lưu `artifacts` + `decision_log`.
4. Hành động "Act" (tạo campaign, gửi tin, ghi đơn) chỉ qua `gateway.call(agent, tool, action, payload)`: Audit Engine kiểm quyền; `WRITE_EXTERNAL` luôn bị chặn và ghi log; `WRITE_DRAFT` được phép.
5. Sau business agents: QA Engine, Audit Engine, Monitoring Engine chạy; 3 supervisor đọc kết quả engine và viết báo cáo.
6. Commander tổng hợp Final Summary. Run → `COMPLETED` / `FAILED` / `WAITING_APPROVAL`.

**Trạng thái.** Task: `PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED` (đúng DEMO_ONLY). Run: `PENDING, RUNNING, WAITING_APPROVAL, COMPLETED, FAILED, CANCELLED`.

---

## 4. Mô hình dữ liệu và đồ thị nhiệm vụ

### 4.1 Bảng SQLite

| Bảng | Mục đích | Ghi chú |
|---|---|---|
| `events` | **đã có**, nhật ký sự kiện thô | giữ nguyên, không xóa dữ liệu cũ (M-06) |
| `runs` | run_id, objective, mode (mock/llm), status, created_at, finished_at, inject (JSON), token_total, cost_est | |
| `tasks` | task_id, run_id, agent_id, status, depends_on (JSON), attempt, input_ref, artifact_id, error, started_at, finished_at | unique (run_id, agent_id) |
| `artifacts` | artifact_id, run_id, agent_id, type, schema_version, payload (JSON), narrative, valid (bool), validation_errors | |
| `decision_log` | id, run_id, task_id, agent_id, action, tool, permission, allowed (bool), input_hash, output_ref, duration_ms, tokens, ts | mọi hành động agent + gateway |
| `llm_calls` | id, run_id, task_id, model, prompt_tokens, completion_tokens, finish_reason, latency_ms, status, cost_est | không lưu nội dung key |
| `approvals` | id, run_id, task_id, reason, amount, status (PENDING/APPROVED/REJECTED), decided_at | HITL |
| `engine_results` | id, run_id, engine (qa/audit/monitor), status (PASS/FAIL/WARN), findings (JSON) | |

Migration: `db.migrate()` dùng `CREATE TABLE IF NOT EXISTS` + bảng `schema_version`. Không có down migration; reset = `docker compose down -v` (chỉ khi người dùng xác nhận).

### 4.2 Đồ thị nhiệm vụ mặc định (Commander sinh ra)

| # | Agent | Phụ thuộc bắt buộc | Artifact |
|---|---|---|---|
| 01 | Commander (plan) | — | Execution Plan |
| 02 | Market Intelligence | 01 | Market Report |
| 03 | Product Scout | 02 | Product Shortlist |
| 04 | Offer & Strategy | 03 | Pricing & Offer Proposal |
| 05 | Content & Creative | 04 | Content Brief & Draft Ads |
| 06 | Campaign Operator | 04, 05 | Campaign Plan (DRAFT) |
| 07 | Lead & Sales | 06 | Lead Processing Report |
| 08 | Customer Success | 07 | Customer Care & Delivery Report |
| 09 | Sales Analyst | 07, 08 | KPI Report |
| 10 | Finance & Risk | 04, 09 | Finance & Risk Report |
| 11 | QA Tester | 02–10 + QA Engine | QA Report |
| 12 | Auditor | 02–10 + Audit Engine | Audit Report |
| 13 | Monitor | tất cả + Monitoring Engine | Monitoring Report |
| 01' | Commander (summary) | 11, 12, 13 | Final Summary |

Phụ thuộc bắt buộc chưa COMPLETED → task không chạy; dependency FAILED và không retry được → task `SKIPPED`, run `FAILED` nhưng artifact đã có vẫn giữ.

### 4.3 Dữ liệu mock Philippines (fixtures cố định)

Theo `DEMO_ONLY.md` P2: LU-PH-001 giá bán 499, giá vốn 180, ship 75, phí thanh toán 18, ngân sách 15.000, chiến dịch DRAFT 4.000, tồn 50, leads 100, confirmed 20, delivered 15, returned 2. Thêm ≥ 2 sản phẩm mô phỏng khác (LU-PH-002, LU-PH-003) để Product Scout so sánh; mọi fixture có `"synthetic": true`.

Công thức QA kiểm (Python): `margin_per_unit = 499 − 180 − 75 − 18 = 226`; `contribution_delivered = 226 × 15 = 3.390`; `breakeven_orders(4000) = ceil(4000 / 226) = 18`; `return_rate = 2/15`.

---

## 5. Quyền và guardrail

| Nhóm quyền | Agent | Ý nghĩa |
|---|---|---|
| `READ` | tất cả | đọc Mock API |
| `WRITE_DRAFT` | Campaign Operator, Lead & Sales, Customer Success | tạo campaign DRAFT, ghi lead note, ghi ticket giả lập |
| `WRITE_EXTERNAL` | **không ai** | publish ads, pay, send message — luôn bị Audit chặn |
| `APPROVE` | chỉ con người qua dashboard | duyệt `approvals` |
| `SUPERVISE` | QA Tester, Auditor, Monitor | đọc engine_results, decision_log, llm_calls |

Guardrail (cấu hình env, mặc định ở `DEMO_DECISIONS.md` M-05): ngân sách chiến dịch ≥ `APPROVAL_THRESHOLD_PHP` (mặc định 5.000) → `WAITING_APPROVAL`; chiến dịch mẫu 4.000 chạy thẳng (happy path). Token budget mỗi run `LLM_RUN_TOKEN_BUDGET` (mặc định 20.000); vượt → Monitoring FAIL, các task còn lại chuyển mock.

---

## 6. Kế hoạch phase

Gửi Claude prompt nền một lần (`AGENTS.md`). Mỗi lượt chỉ một phase. Số phase là mã định danh theo `DEMO_ONLY.md`.

| Phase | Kết quả | Phụ thuộc | Nghiệm thu (tóm tắt từ DEMO_ONLY) |
|---|---|---|---|
| 0 | Audit, sơ đồ, bộ tài liệu, bảng tiến độ | — | Báo cáo hiện trạng thực tế có bằng chứng chạy |
| 1 | LLM client ổn định + Mock LLM | 0 | LLM mock test PASS; response rỗng → lỗi rõ |
| 2 | Mock Business Environment + Mock API | 0 | Mock API nhất quán, test độc lập |
| 3 | Commander + Workflow Engine + schema DB | 1, 2 | Một workflow nhiều bước, agent sau dùng kết quả agent trước |
| 4 | 13 agent + registry + artifact schema | 3 | 13 vai trò khác nhau, có dấu vết bàn giao |
| 5 | 3 Engine + 3 Supervisor + error injection | 4 | QA bắt cost sai, Auditor chặn publish, Monitor bắt timeout |
| 6 | Dashboard văn phòng 3D + chế độ 2D | 5 | Thao tác toàn bộ demo từ trình duyệt; nghiệm thu bổ sung `DEMO_DASHBOARD_3D.md` §7 |
| 7 | Đánh giá/thử ARIS | 4 | Bằng chứng thử hoặc báo cáo blocker |
| 8 | 5 kịch bản E2E + unit/integration | 6 | 5 kịch bản có PASS/FAIL |
| 9 | Đóng gói, README, reset, FINAL_REPORT | 8 | Mở trình duyệt, Start Demo, không cấu hình thêm |

Thứ tự thực hiện: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 8 → 7 → 9 (P7 làm sau P8 vì không chặn demo; ưu tiên P0–P6 theo DEMO_ONLY). Phase 1 và 2 độc lập, có thể làm trong cùng lượt nếu context cho phép.

### 6.1 Phân biệt code / mock / LLM (duy trì sang FINAL_REPORT)

| Thành phần | Thực hiện bằng |
|---|---|
| Workflow, state machine, retry, checkpoint | Code |
| QA/Audit/Monitoring Engine | Code |
| Số liệu kinh doanh, công thức tài chính | Code trên fixtures |
| Dữ liệu thị trường, ads, đơn hàng, logistics | Mock (fixtures) |
| Diễn giải, lập kế hoạch dạng văn bản, nội dung quảng cáo mẫu | LLM (DeepSeek) hoặc Mock LLM |
| Phê duyệt | Con người (dashboard) |

---

## 7. Prompt nền gửi Claude

Đã đưa vào `AGENTS.md`. Sửa ở đó là nguồn chính.

## 8. Prompt từng phase

### Phase 0 — Audit và chuẩn bị
```text
Thực hiện Phase 0. Đọc DEMO_ONLY.md, AGENTS.md, docs/DEMO_PLAN.md. Audit app/main.py, compose.yaml, Dockerfile, SQLite thực tế trong container (bảng, số run). Kiểm tra /health, /agents, /sample, /demo/run với use_llm=false. Không gọi DeepSeek thật.
Cập nhật DEMO_ARCHITECTURE.md (AS-IS có bằng chứng), DEMO_PHASE_STATUS.md, DEMO_HANDOFF.md. Viết tests/test_smoke.py chạy trong container kiểm 4 endpoint hiện có.
Nghiệm thu: báo cáo hiện trạng có lệnh + kết quả; phần đang lỗi ghi rõ; không tự đánh dấu DONE phase khác.
```

### Phase 1 — LLM client và Mock LLM
```text
Thực hiện Phase 1. Tách app/llm/deepseek.py: timeout cấu hình, retry exponential backoff (tối đa 3), max_tokens ≥ 2000, bắt finish_reason=length (ghi WARN, giữ nội dung), response rỗng → ném LLMEmptyError, ghi llm_calls (token, latency, finish_reason, cost ước tính). Tạo app/llm/mock_llm.py trả văn bản theo agent, không gọi mạng. Kiểm encoding: test byte UTF-8 qua API → SQLite → JSON response; chỉ sửa code nếu byte sai, không sửa dữ liệu vì PowerShell (M-04).
Test: unit với httpx MockTransport cho 200, 429, 500, timeout, rỗng, length. Không gọi API thật trừ khi được giao (tối đa 1 lần, ghi sổ).
Nghiệm thu: pytest PASS; response rỗng cho task trạng thái FAILED.
```

### Phase 2 — Mock Business Environment
```text
Thực hiện Phase 2. Tạo app/mock/fixtures/*.json (market, ads, products ≥ 3, suppliers, campaigns, leads, orders, logistics, conversations, finance) theo số liệu DEMO_ONLY P2, mọi bản ghi có "synthetic": true. Tạo app/mock/api.py với router /mock/* chỉ đọc + cơ chế override theo run_id cho error injection (cost 9999). Không gọi mạng.
Test: mỗi endpoint trả đúng fixture; override chỉ ảnh hưởng run được chỉ định.
Nghiệm thu: Mock API nhất quán, kiểm thử độc lập được.
```

### Phase 3 — Commander và Workflow Engine
```text
Thực hiện Phase 3. Tạo app/db.py (migrate idempotent, giữ bảng events), bảng runs/tasks/artifacts/decision_log/llm_calls/approvals/engine_results. Tạo app/core/workflow.py: Commander sinh task graph theo DEMO_PLAN mục 4.2; chạy theo dependency; trạng thái 6 giá trị; retry task FAILED (API POST /runs/{id}/tasks/{agent}/retry); cancel run; replay GET /runs/{id} đọc từ DB không gọi LLM; task RUNNING khi container restart → đánh FAILED có lý do "interrupted", cho retry.
Agent tạm dùng placeholder compute trả artifact tối thiểu (Phase 4 thay). Giữ /demo/run cũ hoạt động hoặc chuyển hướng sang /runs.
Test: integration: 3 task A→B→C, B lỗi → C SKIPPED, retry B → C chạy; restart giả lập.
Nghiệm thu: bằng chứng workflow nhiều bước, artifact trước được task sau đọc.
```

### Phase 4 — 13 Agents
```text
Thực hiện Phase 4. Tạo app/core/registry.py (13 agent: tools, schema in/out, permissions theo DEMO_PLAN mục 5), app/core/artifacts.py (pydantic), app/agents/*.py: compute() bằng Python từ Mock API + artifact upstream; narrate() qua llm (mock mặc định). Số học trong Python, LLM không được sửa số. Hạn mức token theo run. Commander tạo Execution Plan đầu và Final Summary cuối.
Test: unit từng compute() với fixtures; integration run Mock Mode đủ 13 artifact khác loại; kiểm artifact 06 có status DRAFT; artifact 10 dùng số từ 04 và 09.
Nghiệm thu: 13 vai trò rõ ràng, kết quả khác nhau, dấu vết bàn giao trong decision_log.
```

### Phase 5 — Engines, Supervisors, error injection
```text
Thực hiện Phase 5. app/engines/qa.py (tính lại công thức mục 4.3, schema, nhất quán số giữa artifact, trường bắt buộc), audit.py (quyền theo registry, chặn WRITE_EXTERNAL, phân biệt DRAFT/APPROVED, ghi decision_log), monitor.py (timeout, retry > 1, response rỗng, token, thời gian). app/core/gateway.py là đường duy nhất cho "Act". 3 supervisor đọc engine_results và viết báo cáo (mock/LLM).
Error injection qua POST /runs body "inject": ["bad_cost","timeout:<agent>","missing_field:<agent>","publish_attempt","empty_response:<agent>"].
Test: 5 injection → QA FAIL / Audit BLOCK / Monitor FAIL đúng chỗ; happy path tất cả PASS.
Nghiệm thu: QA bắt cost 9999, Auditor chặn publish, Monitor bắt timeout.
```

### Phase 6 — Dashboard văn phòng 3D
```text
Thực hiện Phase 6 theo docs/DEMO_DASHBOARD_3D.md (đặc tả chính) và 10 thành phần tối thiểu của DEMO_ONLY P6.
Claude: copy three.js bản cố định vào app/web/vendor/ (ES module, không build, chạy offline); viết app/web/office3d.js (scene isometric, camera OrbitControls có tự xoay, ánh sáng, nhân vật low-poly từ khối cơ bản, ánh xạ trạng thái task → hình theo §3, tài liệu bay theo GRAPH khi task COMPLETED, polling GET /runs/{id} mỗi 1s); định nghĩa schema office-layout.js và sự kiện giữa scene và panel; nút Retry/Cancel/Approve gọi API.
Gemini (batch ai-jobs/p6-dashboard): đạo cụ từng khu trong office-layout.js; dashboard.html + panels.js (thanh công cụ Tự xoay/Tên/Bong bóng/Toàn cảnh/Tổng quan/Start, ô objective, chọn Mock/DeepSeek, chọn lỗi giả lập, ngăn kéo input/output, tab Kết quả cuối/QA-Audit-Monitor/Token/Nhật ký/Lịch sử, chế độ Tổng quan 2D); chữ tiếng Việt.
FastAPI phục vụ /dashboard và /static. Không gọi LLM để sinh bong bóng.
Test: smoke httpx (/dashboard 200, file vendor 200); Playwright chạy một run Mock từ UI, chụp 4 trạng thái; kiểm ?mode=2d; đo FPS khi tự xoay.
Nghiệm thu: DEMO_DASHBOARD_3D.md §7 + toàn bộ demo thao tác từ trình duyệt.
```

### Phase 7 — ARIS
```text
Thực hiện Phase 7. Clone https://github.com/tauhb/aris-agent vào thư mục tạm (ngoài repo). Đọc license, package.json, kiến trúc, phụ thuộc macOS Keychain, khả năng chạy Docker Linux. Viết docs/DEMO_ARIS_EVALUATION.md: tương thích, blocker, thiết kế adapter (giao diện tool mock → ARIS), so sánh với runtime nội bộ. Chỉ thử tích hợp một workflow nhỏ nếu build được an toàn; không đổi 13 agent sang ARIS. Fallback luôn là runtime nội bộ.
Nghiệm thu: bằng chứng thử hoặc blocker cụ thể; adapter chưa chạy không tính là tích hợp.
```

### Phase 8 — Kiểm thử E2E
```text
Thực hiện Phase 8. tests/e2e: S1 happy path 13 vai trò; S2 bad_cost → QA FAIL; S3 publish_attempt → Audit BLOCK; S4 timeout agent → Monitor ghi lỗi, artifact cũ giữ, retry đúng agent; S5 không có DEEPSEEK_API_KEY → Mock Mode chạy đủ. Chạy trong container. Cập nhật DEMO_TEST_REPORT.md với lệnh + kết quả.
Nghiệm thu: 5 kịch bản có PASS/FAIL; chưa đạt thì sửa hoặc ghi blocker.
```

### Phase 9 — Đóng gói
```text
Thực hiện Phase 9. README (chạy, reset an toàn, Mock/LLM), API doc (/docs OpenAPI + bảng tóm tắt), sơ đồ kiến trúc, bảng code/mock/LLM, bảng hạn chế, POST /admin/reset-demo (xóa run, giữ schema, cần xác nhận), docs/DEMO_FINAL_REPORT.md theo 7 mục báo cáo cuối của DEMO_ONLY.
Nghiệm thu: máy sạch: docker compose up -d --build → mở /dashboard → Start Demo chạy hết Mock Mode.
```

## 9. Cách tiếp tục khi Claude hết context

```text
Tiếp tục dự án Level Up 13-Agent Demo. Đọc AGENTS.md, docs/DEMO_PHASE_STATUS.md, docs/DEMO_DECISIONS.md, docs/DEMO_HANDOFF.md; đối chiếu code thực tế trong app/ và trạng thái container (docker compose ps, /health). Tiếp tục đúng phase và checkpoint đang dở, không bắt đầu lại, không tự nhảy phase. Nêu ngắn gọn phần đã xác minh rồi làm tiếp. Tài liệu và code khác nhau thì kiểm bằng chứng và sửa trạng thái cho trung thực. Không gọi DeepSeek thật nếu sổ gọi đã đủ 2 lần.
```

## 10. Checklist nghiệm thu toàn demo

- Mở `/dashboard` (không cần Internet), Mock Mode mặc định, bấm Start Demo → 13 nhân vật trong văn phòng 3D lần lượt RUNNING → COMPLETED, tài liệu bay theo dependency, Final Summary hiện; chế độ Tổng quan 2D có cùng thông tin.
- 13 artifact khác loại; artifact 10 (Finance) dùng đúng số của 04 và 09; không artifact nào chứa số ngoài fixtures.
- QA/Audit/Monitor là code: tắt LLM vẫn ra kết quả giống nhau.
- Inject cost 9.999 → QA FAIL và Commander không kết luận DRAFT_READY.
- Inject publish → Audit BLOCK, campaign vẫn DRAFT, decision_log có dòng `allowed=false`.
- Inject timeout → Monitor FAIL, retry đúng agent, artifact cũ không mất.
- Replay run cũ không tạo `llm_calls` mới.
- Restart container giữa run → run vẫn xem được, task gián đoạn FAILED có thể retry.
- Không có `DEEPSEEK_API_KEY` → toàn bộ demo chạy.
- Sổ gọi LLM thật ≤ 2 (hoặc theo số đã được duyệt thêm); không có key trong log, docs, git.
- 6 tài liệu `docs/DEMO_*.md` đúng trạng thái; `DEMO_FINAL_REPORT.md` trả lời đủ 7 mục.
