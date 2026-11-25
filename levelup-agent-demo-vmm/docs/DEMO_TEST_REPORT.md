# Báo cáo kiểm thử và biên bản nghiệm thu

Mỗi phase có một mục theo mẫu Tiêu chí / Bằng chứng / Kết quả (Đạt · Không đạt · Chưa kiểm). Chỉ ghi "Đạt" khi có lệnh và kết quả thực tế. Bảng 5 kịch bản E2E ở cuối.

## Phase 0 — Audit và chuẩn bị (04/11/2026)

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| Audit hệ thống và 13 vai trò | Audit ban đầu, `DEMO_ARCHITECTURE.md` | **Đạt** |
| Smoke tests | Docker: `pytest -p no:cacheprovider -q` → 8 passed (04/11, báo cáo cũ ghi nhầm 6) | **Đạt** |
| Live API smoke | `/health`, `/agents` (13), `/sample`, `/demo/run`, `/events/{run_id}` | **Đạt** |

## Phase 1 — DeepSeek client và Mock LLM (04/11/2026)

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| Mock Mode mặc định, không gọi mạng | `app/main.py`, `tests/test_smoke.py` | **Đạt** |
| Timeout/retry DeepSeek | `tests/test_llm.py`: timeout, 429, 500 | **Đạt** |
| Empty response và length handling | `LLMEmptyError`, warning log, tests | **Đạt** |
| `llm_calls` token/cost logging | `app/llm/deepseek.py` | **Đạt** |
| Docker build/test | Build PASS; **6 passed in 9.72s** | **Đạt** |

DeepSeek thật: **0 calls**.

## Phase 2 — Mock Business Environment (04/11/2026)

| Tiêu chí | Bằng chứng | Kết quả |
|---|---|---|
| Ten domain fixtures Philippines | `app/mock/fixtures.json` | **Đạt** |
| Read-only mock APIs | `app/mock/router.py`: 10 `/mock/*` endpoints | **Đạt** |
| Synthetic/network-free responses | `MOCK_ONLY` and `synthetic=true`; no external client | **Đạt** |
| Independent API tests and fixture isolation | `tests/test_mock_api.py` | **Đạt** |

## Rà soát lại Phase 0–2 (05/11/2026)

Chi tiết lỗi và cách sửa: `DEMO_PHASE_STATUS.md` mục "Rà soát lại Phase 0–2". Sau sửa: số run trong DB demo trước/sau `pytest` = 13/13.

## Phase 3 — Commander và Workflow Engine (05/11/2026)

Lệnh: `docker compose run --rm -T demo pytest -p no:cacheprovider -q` → **133 passed in 1.74s**.

| Tiêu chí (DEMO_ONLY P3) | Bằng chứng | Kết quả |
|---|---|---|
| Commander nhận mục tiêu, chuyển thành nhiệm vụ có dependency | `create_run` sinh 14 task theo `GRAPH`; `decision_log` `plan_tasks` | **Đạt** |
| Giao đúng agent, theo dõi đầu vào/kết quả | mỗi task có `agent_id`, artifact, `input_hash`, `inputs_from` | **Đạt** |
| Lưu trạng thái SQLite, 6 trạng thái | bảng `tasks` CHECK 6 giá trị; 69 ca test bảng `graph.py` | **Đạt** |
| Retry agent lỗi | `test_failed_agent_skips_downstream_and_retry_keeps_earlier_results`: kpi lỗi → 5 task SKIPPED → retry → COMPLETED, artifact cũ giữ nguyên id | **Đạt** |
| Cancel | `test_cancel_while_running_stops_remaining_tasks` | **Đạt** |
| Xem lại không gọi LLM | `test_replay_is_read_only_and_does_not_call_llm` | **Đạt** |
| Không chạy khi dependency chưa xong | `next_ready` + thứ tự `task_completed` = `topo_order` | **Đạt** |
| Checkpoint, restart container | `test_restart_recovery_…`, `test_recovery_resumes_run_stopped_between_tasks` | **Đạt** |
| **Bằng chứng workflow nhiều bước, agent sau dùng kết quả agent trước** | Live: `POST /runs?wait=true` → 14 task COMPLETED, `summary.chain_depth` = 13 (độ dài đường dài nhất), mỗi artifact `received_from` = đúng dependency | **Đạt** |
| Agent không trả artifact không được báo thành công | test 3 ca none/no-type/empty → FAILED; timeout → FAILED | **Đạt** |

Gemini batch `p3-workflow`: `ai-jobs/LEDGER.md` dòng 1.

## Phase 4 — 13 Agents (05/11/2026)

Lệnh: `docker compose run --rm -T demo pytest -p no:cacheprovider -q` → **281 passed in 3.56s**.

| Tiêu chí (DEMO_ONLY P4) | Bằng chứng | Kết quả |
|---|---|---|
| Agent Registry: nhiệm vụ, công cụ, schema I/O, quyền riêng | `GET /agents` → 13 vai trò, 14 output khác nhau, không ai có `WRITE_EXTERNAL`; 58 ca test bảng registry + giám sát | **Đạt** |
| Mỗi business agent tạo artifact chuyên biệt | 14 loại artifact, đều qua schema (`test_mock_run_produces_13_role_specific_valid_artifacts`) | **Đạt** |
| Bàn giao qua artifact có schema | `decision_log.inputs_from` = đúng dependency từng task; artifact sai schema bị từ chối, lưu `valid=0` | **Đạt** |
| Không bịa số liệu, số học bằng Python | Mọi số từ fixtures/artifact trước; 80 ca test bảng kỳ vọng viết tay; LLM chỉ viết `narrative`, test LLM mode giữ nguyên biên 226 | **Đạt** |
| Mock Mode chạy không cần DeepSeek | Run live 14 task COMPLETED, 0 lời gọi LLM, 14 lời diễn giải khác nhau | **Đạt** |
| LLM Mode có giới hạn token | `test_token_budget_falls_back_to_mock`: ngân sách 120 token → 3 lời gọi rồi `mock_budget`; LLM trả rỗng → task FAILED | **Đạt** |
| Không cần 13 container | Một container, agent là module Python | **Đạt** |
| **Nghiệm thu: 13 vai trò rõ ràng, kết quả khác theo chức năng, có dấu vết bàn giao** | Run live: Offer biên 226 / hòa vốn 18 → KPI ROAS 1,62 → Finance −1.062 PHP, HIGH → Commander `HOLD_DRAFT` | **Đạt** |

Gemini batch `p4-agents`: `ai-jobs/LEDGER.md` dòng 2.

## Phase 5 — Supervisory Agents và kiểm tra chéo (05/11/2026)

Lệnh: `docker compose run --rm -T demo pytest -p no:cacheprovider -q` → **424 passed in 4.96s**.

Chạy trực tiếp trên container (`POST /runs?wait=true`):

| Inject | Run | QA | Audit | Monitor | Commander | Quy tắc bắt được |
|---|---|---|---|---|---|---|
| (không) | COMPLETED | PASS | PASS | PASS | HOLD_DRAFT | — |
| `bad_cost` | COMPLETED | **FAIL** | PASS | PASS | NEEDS_REVIEW | reference (9999 ≠ 180) |
| `publish_attempt` | COMPLETED | PASS | **FAIL** | PASS | NEEDS_REVIEW | blocked_action |
| `timeout:market` | FAILED | FAIL | PASS | **FAIL** | NEEDS_REVIEW | timeout, skipped, schema |
| `missing_field:kpi` | FAILED | **FAIL** | PASS | FAIL | NEEDS_REVIEW | schema (artifact bị từ chối), task_failed |
| `empty_response:offer` | FAILED | FAIL | PASS | **FAIL** | NEEDS_REVIEW | empty_response |

| Tiêu chí (DEMO_ONLY P5) | Bằng chứng | Kết quả |
|---|---|---|
| QA Engine: phép tính, schema, nhất quán, thiếu trường | `app/engines/qa.py`; 51 ca test bảng; `test_s2_invalid_cost…`, `test_missing_field…` | **Đạt** |
| Audit Engine: quyền, ghi log, chặn WRITE trái phép, phân biệt DRAFT/được duyệt | `gateway.py` + `audit.py`; mọi hành động có dòng `tool_call`; publish → `allowed=0`, BLOCKED; HITL `WAITING_APPROVAL` → duyệt | **Đạt** |
| Monitoring Engine: timeout, retry bất thường, lỗi, thời gian/token/trạng thái | `monitor.py`; 65 ca test bảng (cùng Audit); timeout/empty/retried/token_budget | **Đạt** |
| 3 Supervisory Agents đọc bằng chứng từ Engine | artifact giám sát chứa `engine_result_id` trỏ tới `engine_results` | **Đạt** |
| Engine độc lập LLM | `test_engines_do_not_import_llm_or_agents`; `test_engines_are_independent_of_llm_output` (người kể "bịa" số chỉ gây WARN, số không đổi) | **Đạt** |
| 5 error injection | bảng chạy trực tiếp ở trên + 6 test tích hợp | **Đạt** |
| **Nghiệm thu: QA bắt lỗi chi phí, Auditor chặn publish, Monitor bắt timeout** | 3 dòng in đậm trong bảng chạy trực tiếp | **Đạt** |

Gemini batch `p5-engines`: `ai-jobs/LEDGER.md` dòng 3.

## Phase 6 — Dashboard văn phòng 3D (05/11/2026)

Lệnh: `docker compose run --rm -T demo pytest -p no:cacheprovider -q` → **435 passed** (thêm 11 test phục vụ file tĩnh, không URL ngoài).
Kiểm trên trình duyệt thật (Playwright, Chromium 1440×900, container `127.0.0.1:8088`), ảnh chụp ở `D:\LevelUp-Agent-Demo\.playwright-mcp\p6-*.png`.

| Tiêu chí (DEMO_ONLY P6 + `DEMO_DASHBOARD_3D.md` §7) | Bằng chứng | Kết quả |
|---|---|---|
| Ô nhập yêu cầu + Start Demo; chọn Mock/DeepSeek, Mock mặc định | form trái; radio Mock checked mặc định; DeepSeek hiện cảnh báo chi phí | **Đạt** |
| 13 agent với trạng thái cập nhật | `p6-03-running.png`: "Bước 1/14", Market "Đang làm", phòng khác ⏸; polling 1 s | **Đạt** |
| Sơ đồ công việc và dependency | 3D: tài liệu bay theo `depends_on`; 2D: SVG 14 nút theo tầng (`p6-08-2d-fixed.png`) | **Đạt** |
| Xem đầu vào/đầu ra từng agent, kết quả bàn giao | bấm nhãn phòng 02 → ngăn chi tiết: Đầu vào = artifact `plan`, Đầu ra JSON + diễn giải (`p6-04-failed-drawer.png`) | **Đạt** |
| QA / Auditor / Monitor | tab "QA / Audit / Monitor" từ `run.engines`; QA FAIL hiện bong bóng ở phòng QA | **Đạt** |
| Token, lỗi, lịch sử | tab Token & chi phí, Nhật ký (decision log), Lịch sử (mở lại run = replay) | **Đạt** |
| Xem lại run, Retry lỗi, Cancel | `timeout:market` → FAILED → Retry trong ngăn chi tiết → COMPLETED, Monitor WARN `retried`; Cancel chỉ hiện khi đang chạy | **Đạt** |
| Báo cáo cuối của Commander | tab Kết quả cuối: HOLD_DRAFT, bảng key_numbers, next_steps | **Đạt** |
| Audit chặn publish thấy được | `p6-05-publish-blocked.png`: đèn cổng đỏ, "Chặn publish thật — chiến dịch giữ DRAFT" | **Đạt** |
| HITL | container tạm `APPROVAL_THRESHOLD_PHP=3000` cổng 8089: thẻ "Chờ phê duyệt" + chuông → Duyệt → COMPLETED (`p6-06-approval.png`) | **Đạt** |
| Không cần Internet | three.js phục vụ từ `/static/vendor/`; test khẳng định HTML không có URL ngoài | **Đạt** |
| Chế độ 2D dự phòng | `?mode=2d`: đồ thị + bảng + mọi tab; không hiện thông báo lỗi 3D | **Đạt** |
| FPS ≥ 30 khi tự xoay | `window.__officeFps` = 108 trên máy demo | **Đạt** |
| **Nghiệm thu: thao tác toàn bộ demo từ trình duyệt, không cần PowerShell** | các dòng trên | **Đạt** |

Gemini batch `p6-dashboard`: `ai-jobs/LEDGER.md` dòng 4.

## Phase 7 — ARIS (05/11/2026)

| Tiêu chí (DEMO_ONLY P7) | Bằng chứng | Kết quả |
|---|---|---|
| License, dependency, kiến trúc | MIT; 34 gói pnpm; nền DeepSeek Harness `0.2.1-rc.2`; tác giả đã dừng phát triển | **Đạt** |
| Docker Linux | `pnpm install` + `pnpm build` thành công trên `node:22-bookworm`; vitest 1.206/1.209 ca qua | **Đạt** |
| macOS Keychain | `@aris/keychain` gọi `/usr/bin/security`; trên Linux trả rỗng, không sập; thay được qua `KeychainRunner` | **Đạt** |
| Thiết kế adapter | `DEMO_ARIS_EVALUATION.md` mục 4 | **Đạt** |
| Thử workflow nhỏ với mock tools | `tools/aris-adapter/spike-result.json`: 4 thẻ ARIS → agent 02, 03, 04, 11 `completed`; ARIS từ chối giao sớm thẻ đang chờ; 0 lời gọi LLM | **Đạt (giới hạn)** |
| Fallback khi ARIS lỗi | `spike-fallback-result.json`: không nạp được ARIS → `POST /runs` → COMPLETED | **Đạt** |
| Không tính adapter chưa chạy là tích hợp | ARIS runtime đầy đủ ghi rõ "chưa tích hợp" | **Tuân thủ** |

## Phase 8 — Kiểm thử E2E (05/11/2026)

Lệnh: `python tools/e2e/run_e2e.py` (dựng container riêng: cổng 8090 Mock, không khóa DeepSeek; cổng 8091 cho kịch bản khởi động lại; trình duyệt trong `mcr.microsoft.com/playwright:v1.48.2-jammy`). Kết quả lưu ở `tests/e2e/results/latest.json`, ảnh ở `tests/e2e/results/shots/`.

| Kịch bản | Mô tả | Bằng chứng | Kết quả |
|---|---|---|---|
| S1 Happy Path | Commander điều phối đủ 13 vai trò, báo cáo cuối | 14 task COMPLETED, 13 `agent_id`, 14 loại artifact, 3 engine PASS, 8 lời gọi công cụ đều được phép, `HOLD_DRAFT`; trình duyệt: `2-happy-path.png` | **PASS** |
| S2 Invalid Cost | QA phát hiện giá vốn sai | QA FAIL `reference` có 9999, Commander `NEEDS_REVIEW`; trình duyệt: `5-qa-bad-cost.png` | **PASS** |
| S3 Unauthorized Action | Auditor chặn publish | `meta_ads.publish` `allowed=0`, `WRITE_EXTERNAL`, Audit FAIL `blocked_action`, chiến dịch DRAFT; trình duyệt: `4-publish-blocked.png` | **PASS** |
| S4 Agent Failure | Timeout, kết quả cũ giữ, retry đúng agent | market FAILED `timeout`, Monitor FAIL; Retry → COMPLETED, market lần thử 2, artifact `plan` giữ nguyên id, Monitor WARN `retried`; trình duyệt: `3-timeout-then-retry.png` | **PASS** |
| S5 No LLM | Không khóa DeepSeek, Mock chạy đủ | `mode=llm` → 400; run Mock COMPLETED, 0 lời gọi LLM, mọi diễn giải `mock` | **PASS** |
| Bổ sung: restart container | Checkpoint và khôi phục (DEMO_ONLY P3) | `product` đang RUNNING khi `docker restart` → FAILED "interrupted"; `plan`, `market` giữ COMPLETED; Retry → COMPLETED | **PASS** (sau khi sửa lỗi, xem dưới) |
| Bổ sung: trình duyệt | 9 kịch bản qua giao diện | load, happy-path, timeout-then-retry, publish-blocked, qa-bad-cost, overview-2d, history-replay, dock-and-viewport, no-console-errors | **9/9 PASS** |

**Lỗi E2E tìm ra:** lần chạy đầu kịch bản restart FAIL. uvicorn hủy tác vụ nền khi container dừng; run bị đánh FAILED nhưng task `product` kẹt RUNNING, bước phục hồi chỉ quét run PENDING/RUNNING nên bỏ sót, task không Retry được. Sửa: `workflow._interrupt_orphans` gọi trong `_finish` và `recover` (quét mọi run có task RUNNING); test hồi quy `test_executor_cancelled_on_shutdown_leaves_retryable_task`, `test_recover_fixes_running_task_under_a_finished_run`.

## Phase 9 — Đóng gói và bàn giao (05/11/2026)

| Tiêu chí (DEMO_ONLY P9) | Bằng chứng | Kết quả |
|---|---|---|
| Docker Compose | `docker compose up -d --build --force-recreate` → healthy, `/dashboard` 200, dữ liệu cũ giữ (19 run) | **Đạt** |
| Dashboard | Phase 6 + E2E trình duyệt 8/8 | **Đạt** |
| Database schema và dữ liệu demo | `app/db.py` (schema v2), fixtures `app/mock/fixtures.json` | **Đạt** |
| API documentation | `/docs` (OpenAPI) + `docs/DEMO_API.md` | **Đạt** |
| README | `README.md` viết lại (chạy, 13 agent, DeepSeek, reset, test, an toàn) | **Đạt** |
| Reset Demo Data an toàn | `POST /admin/reset-demo` cần `{"confirm": true}`, 409 khi còn run chạy; 2 test | **Đạt** |
| Báo cáo kiểm thử | tài liệu này | **Đạt** |
| Sơ đồ kiến trúc | `DEMO_FINAL_REPORT.md` mục 2, `DEMO_ARCHITECTURE.md` | **Đạt** |
| Phân biệt code / mock / LLM | `DEMO_FINAL_REPORT.md` mục 3 | **Đạt** |
| Bảng hạn chế | `DEMO_FINAL_REPORT.md` mục 7 | **Đạt** |
| `docs/DEMO_FINAL_REPORT.md` | có, trả lời đủ 7 câu hỏi | **Đạt** |
| Kiểm API thật tối thiểu (DEMO_ONLY P1, còn nợ) | 1 lời gọi DeepSeek thật: COMPLETED, 122/267 token | **Đạt** |
| **Nghiệm thu cuối: mở trình duyệt, Start Demo, không cấu hình công cụ kinh doanh thật** | Container build lại, `/dashboard` → Start Demo chạy Mock (E2E trình duyệt `happy-path`) | **Đạt** |

Lệnh cuối: `docker compose run --rm -T demo pytest -p no:cacheprovider -q` → **439 passed, 7 skipped** (bộ E2E HTTP, chỉ chạy qua `run_e2e.py`).

## Sổ chạy test

| Ngày | Lệnh | Kết quả |
|---|---|---|
| — | — | — |

## A0 — kiểm tra mốc cơ sở 06/11/2026 (chưa đạt cổng nghiệm thu)

- `docker ps`: ban đầu không có pipe dockerDesktopLinuxEngine.
- `docker desktop start`: mở Desktop nhưng daemon không sẵn sàng; `docker info` chờ, log lặp `HEAD /_ping: context deadline exceeded`. Đã thử `docker desktop restart --timeout 90`.
- `docker compose build -q` chờ daemon; chuỗi pytest/E2E chưa thực thi được. Không có số passed/skipped mới; 441 passed và 9/9 ở checkpoint trước là lịch sử, không phải baseline A0.
- `tests/e2e/results/latest.json` có sẵn: ok=false, browser dock-and-viewport bị đóng page/context. Cần chạy lại trước kết luận hồi quy.
- Tag `levelup-vmm-demo:baseline-v2`: chưa tạo. Không sửa code, không gọi DeepSeek, không xóa volume.
- Tài liệu kiểm đủ 13 OA-D, 18 OA-M, 12 phase A (A8 tách a/b), sơ đồ TO-BE và bảng API đánh dấu kế hoạch. Gemini job api-plan exit 0, stray writes 0.

## A0 — mốc cơ sở 23/11/2026 (ĐẠT, baseline-v2)

Đo lại hoàn toàn, không dùng số cũ. Git HEAD `6a2eb56a4a214687c3f4f16c8bc9839dca137b92` (working tree chỉ có 2 tài liệu mới chưa track, không thay đổi mã khi bắt đầu).

**Lần đo 16:26–16:41 (PARTIAL):** `docker compose run --rm -T demo pytest` → 441 passed, 7 skipped. E2E 2 lần: API 7/7 cả hai; restart OK; trình duyệt 8/9 rồi 7/9 — lỗi `locator.check` timeout chập chờn, mỗi lần ở ca khác nhau (qa-bad-cost, timeout-then-retry, publish-blocked). Ca `dock-and-viewport` (lỗi cũ 06/11) **đạt cả hai lần**. Kết luận ban đầu: nghi do tranh tài nguyên Docker với các container khác (`lalahoa-db`, `aiops-demo-n8n-1`, `openmausbot-computer`) chạy song song trên máy.

**Điều tra nguyên nhân:** đọc `app/web/panels.js` và `app/web/main.js` — `startFormBody`/checkbox tình huống là DOM tĩnh, tạo một lần; `renderOverview()` (gọi lại mỗi 1s khi poll run) chỉ cập nhật số liệu/danh sách việc, không đụng tới `startFormBody` hay các checkbox; không có CSS transition trên `.start-form-body`/`.scenario-item` làm chậm hiển thị. Không tìm thấy lỗi tái hiện ở ứng dụng — xác nhận là **lỗi script/môi trường (Playwright flaky do tranh tài nguyên)**, không phải lỗi logic dashboard.

**Sửa:** `tests/e2e/browser/dashboard.e2e.mjs` — tăng timeout các bước `.check()`/`.uncheck()`/`.selectOption()` từ 5000ms lên 15000ms, thêm `assert.ok(isChecked())` ngay sau mỗi `.check()` để phát hiện sớm nếu tick không giữ. Không sửa mã ứng dụng (`app/web/`).

**Đo lại 17:0x–17:1x, dừng `lalahoa-db` và `aiops-demo-n8n-1` trước khi chạy (chỉ là DB thử cục bộ của LaLaHoa, không phải DB thật trên VPS; không đụng `openmausbot-computer`):**
- `pytest` trong container: 441 passed, 7 skipped, 0 failed.
- `python tools/e2e/run_e2e.py` chạy 3 lần liên tiếp, môi trường tách biệt (cổng 8090/8091, không đụng volume demo chính):

| Lần | API | Restart | Trình duyệt (9 ca) |
|---|---|---|---|
| 1 | 7/7 | OK, COMPLETED | **9/9 PASS** |
| 2 | 7/7 | OK, COMPLETED | **9/9 PASS** |
| 3 | 7/7 | OK, COMPLETED | **9/9 PASS** |

0 lời gọi DeepSeek thật cả 3 lần. 2 container đã dừng được bật lại ngay sau khi đo (`lalahoa-db`, `aiops-demo-n8n-1` đều `Up`).

**Image:** build lại, ID `d041ad35b2a7`, gắn tag `levelup-vmm-demo:baseline-v2`.

**Bằng chứng:** `latest_logs/a0-baseline-20261123/` (log lần đo 16:26 PARTIAL) và `latest_logs/a0-baseline-20261123/rerun2/run1.log`, `run2.log`, `run3.log` (3 lần đạt 9/9 sau khi sửa).

**A0: DONE.**

## A1 — Nhật ký điều phối có lý do (24/11/2026, ĐẠT, Jarvis nghiệm thu)

`app/core/graph.py`: hàm thuần `dispatch_reason()` + bảng `DISPATCH_REASON`, không sửa `TRANSITIONS`. `app/core/workflow.py` ghi `dispatch`/`dispatch_result` vào `decision_log` (không đổi schema). `app/mock/data.py` trả `input_sources` (`fixture`/`extracted`/`default`), `needs_review` khi không hiểu, `currency_note` khi thị trường khác Philippines. `app/web/panels.js` tab Nhật ký hiện lý do/nguồn.

`tests/test_dispatch.py` (9 ca, mới) + `pytest` trong container: **450 passed, 7 skipped**. `python tools/e2e/run_e2e.py` chạy 3 lần liên tiếp: API 7/7, restart OK, trình duyệt 9/9 — cả 3 lần, 0 lời gọi DeepSeek thật.

**Bằng chứng:** `latest_logs/a1-dispatch-20261124/`.

**A1: DONE.**

## A2 — Nâng DB v3 và bảo toàn dữ liệu (25/11/2026, chờ Jarvis nghiệm thu)

Theo phiếu phạm vi đã duyệt (`docs/DEMO_PLAN_OPTION_A.md` mục 6.3). Nhánh `phase-a2-db-v3` từ `phase-a1-dispatch` (commit `25ee168`).

- `app/db.py`: `SCHEMA_VERSION = 3`. `_migrate_alter()` kiểm `PRAGMA table_info` trước mỗi `ALTER` (`runs.max_rework/rooms/use_memory/memory_ids`, `approvals.tool/decided_by`) — chạy lại không lỗi, không đổi cột cũ. Thêm `CREATE TABLE IF NOT EXISTS` cho `rework_requests`, `rooms`, `room_messages`, `memory_items` (chỉ mục duy nhất một phần `ON memory_items(key) WHERE status='ACTIVE'`), `learning_proposals` (chỉ mục duy nhất một phần tương tự cho các trạng thái mở), `learning_runs`, `learning_meta`, `channel_inbox`, `channel_outbox`, `brain_inbox`. Thêm mới `system_stop` + `system_stop_log` (không có trong `DEMO_PLAN_OPTION_A.md` gốc — phục vụ quyết định "chốt dừng khẩn" mục 2 kế hoạch 4 mốc) cùng `get_stop_state()`/`set_stop()`.
- `app/core/workflow.py`: `RESET_TABLES` mở rộng (xóa bảng con trước do `foreign_keys=ON`). `reset_demo(include_memory=False)`: giữ `memory_items` + `learning_proposals` đã quyết, chuyển `PROPOSED`/`REPLAYED_*` → `EXPIRED`. `include_memory=True`: xóa thêm hai bảng đó (chỉ dùng trên DB thử). `learning_meta`, `system_stop`, `system_stop_log` không bao giờ bị xóa bởi reset.
- `app/runs_api.py`: `ResetRequest.include_memory` (mặc định `false`). Thêm `GET/POST /admin/stop`, `POST /admin/resume` — **chỉ lưu trữ trạng thái**, chưa chặn dispatch và chưa kiểm người bấm (để A3 làm).
- Không đổi `app/core/graph.py`, `app/mock/data.py`, `app/web/*` — A2 không có phạm vi UI/giao diện.

**Test mới** `tests/test_db_migrate.py` (6 ca): migrate DB v2 giả (có run/event/artifact/approval cũ) lên v3 → đọc đúng lịch sử, cột mới có mặc định đúng; migrate 2 lần liên tiếp không lỗi; 2 `memory_items` cùng `key` đều `ACTIVE` → bị chặn bởi chỉ mục; `reset_demo(include_memory=False)` giữ ký ức + hết hạn đề xuất mở + giữ `learning_meta`; `reset_demo(include_memory=True)` xóa ký ức trên DB thử; `set_stop()` giữ qua reset và qua việc mở lại connection (mô phỏng restart), có nhật ký `stop`/`resume`.

**Kết quả đo:**
- `pytest` local (host, 456 test): **456 passed** — `latest_logs/a2-db-v3-20261125/pytest-local.log`.
- `docker compose run --rm -T demo pytest -p no:cacheprovider -q`: **456 passed, 7 skipped** (450 cũ của A1 + 6 mới của A2; 7 skipped là bộ E2E-qua-HTTP không đổi) — `latest_logs/a2-db-v3-20261125/pytest-container.log`.
- `python tools/e2e/run_e2e.py`: API 7/7, restart OK (COMPLETED), trình duyệt 9/9 — `latest_logs/a2-db-v3-20261125/e2e-run1.log`. Container E2E tự dọn sau khi chạy; `lalahoa-db`, `aiops-demo-n8n-1`, `openmausbot-computer` không bị đụng tới (không cần dừng, đủ tài nguyên).
- Kiểm lại bởi MausBot 25/11 14:10–14:20 (sau khi log A2 bị xóa khỏi `latest_logs/`, chạy lại từ đầu): pytest container 456 passed/7 skipped, E2E API 7/7 + restart OK + trình duyệt 9/9.
- Nâng cấp trên **bản sao DB thật** (`latest_logs/a2-pre-migrate/demo.sqlite.bak`, chụp bằng sqlite backup từ volume `demo_data` lúc 14:17, bản 2): sau 2 lần migrate → bản 3, 8 bảng cũ giữ nguyên từng dòng (22 runs, 308 tasks, 1227 events, 310 artifacts, 613 decision_log, 22 llm_calls, 69 engine_results), cột mới mặc định 0/0/0/'[]', chốt dừng mặc định tắt. Khôi phục bản sao → đọc lại bản 2 và run đối chứng `4748c724…` COMPLETED — `latest_logs/a2-db-v3-20261125/real-copy-migrate.log`. DB thật trong volume vẫn ở bản 2 (container đang chạy chưa đổi image).
- 0 lời gọi DeepSeek thật.

**Chưa làm (lùi theo phiếu):** chặn dispatch mới khi `system_stop.stopped=1` và kiểm ai được phép bấm dừng/mở lại — để A3.

**Đường quay lại:** commit `25ee168` (A1) + image `levelup-vmm-demo:baseline-v2`; chưa chạy migration trên volume `demo_data` thật trong lượt này (chỉ test trên DB tạm), nên không cần bản sao riêng để quay lại.

**A2: Jarvis nghiệm thu 25/11/2026.** Đã commit/push nhánh `phase-a2-db-v3`, chưa mở A3.

## A3 — Gateway chạy lại an toàn, dừng khẩn, phân quyền bằng token (25/11/2026)

Theo phiếu phạm vi đã chốt (checkpoint "A3 mở" trong `DEMO_HANDOFF.md`). Nhánh `phase-a3-gateway-rerun` từ `phase-a2-db-v3` (`3f4e8f2`).

- `app/core/gateway.py`: `execute(..., attempt=1)` luôn gọi `audit.check_action` trước; `detail` có thêm `attempt` + `action_hash` (sha256 JSON chuẩn hóa toàn bộ action); `approvals.tool` có giá trị. Dùng lại khi đã có dòng `tool_call` không BLOCK cùng `(run_id, task_key, tool, target, action_hash)` **và** trùng phán quyết: không tạo DRAFT/approval mới, vẫn ghi dòng `tool_call` mới chép đủ `detail` gốc + `reused=true` + `attempt` hiện tại. Ba hàm thuần mới `action_hash()`, `reusable()`, `current_attempt()`.
- `app/agents/__init__.py`: truyền `ctx.attempt` vào gateway. `app/core/workflow.py`: `tool_calls()` chỉ giữ lời gọi của lần thử hiện tại của từng task (thiếu `attempt` = 1); `/runs/{id}/decision-log` vẫn trả đủ lịch sử.
- Dừng khẩn: vòng `execute()` không giao task mới khi `system_stop.stopped=1` (task đang chạy chạy xong, task chờ giữ PENDING, run giữ RUNNING; ghi `dispatch_paused` / `dispatch_resumed` một lần mỗi đợt); mở lại thì chạy tiếp; hủy vẫn được khi đang dừng. Hỏi lại mỗi `STOP_POLL_S` (mặc định 0,5 s). `POST /runs` khi đang dừng → 409.
- Phân quyền (`app/auth.py`): token riêng mỗi người qua `Authorization: Bearer <token>`; env `AUTH_OWNER=<tên>:<token>`, `AUTH_DELEGATES=<tên>:<token>,…`, `AUTH_MAX_DELEGATES=3`. Token ≥ 16 ký tự, tên/token không trùng; cấu hình sai thì app không khởi động (kiểm trong lifespan). Không cấu hình = không ai duyệt/dừng được. Duyệt/từ chối và dừng: chủ dự án hoặc người được ủy quyền; mở lại: chỉ chủ dự án. 401 thiếu/sai token, 403 không đủ quyền. Ghi trước có hiệu lực (người sau 409). DB/log chỉ lưu tên (`approvals.decided_by`, `system_stop.actor`, `decision_log`), không lưu token.
- `app/web/main.js`: gặp 401 thì hỏi token một lần (`prompt`), giữ trong `sessionStorage` của tab, gửi lại; token sai thì xóa. Giao diện đăng nhập đầy đủ để A9.
- `tests/test_phase5.py`: test HITL thêm token (bắt buộc từ A3), các kỳ vọng cũ giữ nguyên, thêm kiểm `decided_by`.

**Test mới:**
- `tests/test_a3_gateway_stop.py` (20 ca, Claude): happy path vẫn 8 `tool_call`, tất cả attempt 1 có hash; `missing_field:campaign` + ngưỡng 3000 → retry lần 2 cùng action chỉ 1 approval, dòng `reused` chép đủ `detail`, Audit không báo `not_via_gateway` (hồi quy retry); ngưỡng đổi giữa 2 lần thử → approval PENDING mới; Audit lần 2 không thấy BLOCK của lần 1 nhưng decision-log vẫn giữ; 401/403/200 cho stop/resume; `POST /runs` 409 khi dừng; run đang chạy dừng giao việc rồi chạy tiếp; hủy khi đang dừng; ghi trước có hiệu lực; không lưu token; 9 ca cấu hình (quá 3 người, nâng giới hạn bằng env, token ngắn/trùng, 2 owner, rỗng).
- `tests/test_gateway_attempt_table.py` (31 ca, Gemini `ai-jobs/oa-a3`): bảng `action_hash` / `reusable` / `current_attempt`. Claude đọc từng ca; 1 sửa chữ (tool `pancake.create_draft` không có trong demo → `crm.reply_draft`).
- Kiểm test bắt lỗi thật: tắt từng cơ chế (dùng lại, lọc lần thử, so phán quyết, chặn khi dừng) → mỗi lần đều có test đỏ; khôi phục code sau đó.

**Kết quả đo:**
- `pytest` local: **507 passed, 7 skipped** (456 cũ + 20 + 31).
- `docker compose run --rm -T demo pytest -p no:cacheprovider -q`: **476 passed, 7 skipped** trước khi nhận file Gemini (`latest_logs/a3-gateway-20261125/pytest-container.log`); checker Gemini chạy file đó trong image: 31 passed.
- `python tools/e2e/run_e2e.py` (E2E không gọi duyệt nên không cần token): 3 lượt liên tiếp đều API 7/7, restart OK, trình duyệt 9/9 — `e2e-run1.log`..`e2e-run3.log`.
- Kiểm tay trên trình duyệt thật (container tạm cổng 8092, token thử, ngưỡng 3000): bấm Duyệt → hộp nhập token → run COMPLETED, `decided_by=an`; curl: stop không token 401, người ủy quyền stop 200, `POST /runs` 409, người ủy quyền resume 403, chủ dự án resume 200; log container không chứa token.
- 0 lời gọi DeepSeek thật. Không đụng `lalahoa-db`/`aiops-demo-n8n-1`/`openmausbot-computer`.

**Hạn chế đã biết:** dùng lại theo đúng đặc tả kể cả khi approval cũ đã bị từ chối (lần chạy lại giữ phán quyết cũ, không hỏi lại); hai action giống hệt trong cùng một lần thử cũng chỉ tạo một DRAFT. Container chính (8088) chưa tạo lại với image mới và `.env` chưa có `AUTH_*` → khi tạo lại phải thêm token thì nút Duyệt trên dashboard mới dùng được.

**A3: chủ dự án nghiệm thu 25/11/2026.** Đã commit/push nhánh `phase-a3-gateway-rerun`, chưa mở A4.
