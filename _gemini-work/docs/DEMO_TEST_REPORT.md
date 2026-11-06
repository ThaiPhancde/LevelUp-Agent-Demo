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
| Bổ sung: trình duyệt | 8 kịch bản qua giao diện | load, happy-path, timeout-then-retry, publish-blocked, qa-bad-cost, overview-2d, history-replay, no-console-errors | **8/8 PASS** |

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
