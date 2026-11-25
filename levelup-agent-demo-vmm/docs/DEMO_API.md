# API của bản Demo

Tài liệu tương tác đầy đủ (OpenAPI): `http://localhost:8088/docs`. Mọi phản hồi về run đều có `"environment": "MOCK_ONLY"`. Không endpoint nào kết nối hệ thống ngoài; DeepSeek chỉ được gọi khi run ở `mode: "llm"` và có khóa.

## Run (Commander + Workflow Engine)

| Method | Đường dẫn | Mục đích | Mã lỗi |
|---|---|---|---|
| POST | `/runs` | Tạo run. Thân: `{"objective": str, "mode": "mock"\|"llm", "inject": [str]}`. Mặc định chạy nền, trả `202 {run_id, status: PENDING}`; `?wait=true` chạy xong mới trả toàn bộ run | 422 objective rỗng/mode lạ/inject lạ; 400 `mode=llm` khi thiếu `DEEPSEEK_API_KEY` |
| GET | `/runs?limit=50` | Lịch sử run, mới nhất trước (1–200) | — |
| GET | `/runs/{run_id}` | Xem lại run: `run`, 14 `tasks` kèm `artifact`, `engines` (kết quả mới nhất của qa/audit/monitor), `approvals`, `llm` (số lời gọi, token, chi phí ước tính). Chỉ đọc DB, không chạy agent, không gọi LLM | 404 |
| POST | `/runs/{run_id}/cancel` | Hủy run đang PENDING/RUNNING/WAITING_APPROVAL; task đang chạy được chạy xong, task còn lại CANCELLED, yêu cầu duyệt đang chờ bị từ chối | 404; 409 run đã kết thúc |
| POST | `/runs/{run_id}/tasks/{task_key}/retry` | Chạy lại một task FAILED; task SKIPPED phía sau và các task giám sát chạy lại; artifact cũ của task đã xong giữ nguyên. `?wait=true` như trên | 404 task lạ; 409 run không FAILED hoặc task không FAILED |
| POST | `/runs/{run_id}/approvals/{approval_id}` | Người duyệt hành động bị giữ (HITL). Thân `{"decision": "APPROVED"\|"REJECTED"}`. Cần `Authorization: Bearer <token>` của chủ dự án hoặc người được ủy quyền (A3); trả `decided_by`. Hết yêu cầu chờ thì run WAITING_APPROVAL → COMPLETED | 401 thiếu/sai token; 422 decision lạ; 409 đã quyết hoặc không có |
| GET | `/admin/stop` | Trạng thái dừng khẩn (ai bấm, lý do, lúc nào) | — |
| POST | `/admin/stop` | Dừng khẩn (A3): không giao task mới, `POST /runs` trả 409. Thân `{"reason": "…"}`. Token chủ dự án hoặc người được ủy quyền | 401; 403 |
| POST | `/admin/resume` | Mở lại sau dừng khẩn; run đang chờ chạy tiếp. Chỉ token chủ dự án | 401; 403 |
| GET | `/runs/{run_id}/decision-log` | Nhật ký quyết định: lập kế hoạch, bàn giao (`input_hash`, `inputs_from`), lời gọi công cụ (`tool`, `permission`, `allowed`), kết quả engine, retry, hủy, duyệt | 404 |
| GET | `/runs/{run_id}/llm-calls` | Từng lời gọi DeepSeek: model, token vào/ra, `finish_reason`, độ trễ, trạng thái (kể cả lỗi HTTP/timeout), chi phí ước tính | 404 |

**Lỗi giả lập** (`inject`, tối đa 10): `bad_cost` · `publish_attempt` · `timeout:<task>` · `missing_field:<task>` · `empty_response:<task>`. Ba loại có `<task>` chỉ áp ở lần thử đầu, nên Retry đúng task sẽ thành công.

**Task:** `plan, market, product, offer, content, campaign, leads, care, kpi, finance, qa, audit, monitor, summary`. **Trạng thái task:** `PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED`. **Trạng thái run:** thêm `WAITING_APPROVAL`.

## Agent, dữ liệu giả lập, giao diện

| Method | Đường dẫn | Mục đích |
|---|---|---|
| GET | `/agents` | Registry 13 vai trò: nhóm, nhiệm vụ, task, công cụ, quyền, loại artifact |
| GET | `/mock/market`, `/mock/meta-ads`, `/mock/products`, `/mock/suppliers`, `/mock/campaigns`, `/mock/leads`, `/mock/orders`, `/mock/logistics`, `/mock/customer-conversations`, `/mock/finance` | Dữ liệu giả lập cố định kịch bản Philippines, chỉ đọc, `synthetic: true` |
| GET | `/dashboard` | Văn phòng 3D; `?mode=2d` cho chế độ Tổng quan |
| GET | `/static/*` | JS/CSS của dashboard, three.js r160 trong `vendor/` |
| GET | `/health` | `{"ok": true, "live_integrations": false, "model": ...}` |

## Quản trị

| Method | Đường dẫn | Mục đích | Mã lỗi |
|---|---|---|---|
| POST | `/admin/reset-demo` | Xóa toàn bộ run, task, artifact, nhật ký (giữ schema). Thân bắt buộc `{"confirm": true}` | 400 thiếu xác nhận; 409 còn run đang chạy |

## Tương thích cũ

| Method | Đường dẫn | Ghi chú |
|---|---|---|
| POST | `/demo/run` | Bọc `/runs`: `{"objective", "inject_error": bool, "use_llm": bool}` → chạy xong trả `checks` (qa/audit/monitor), `outputs` 14 dòng |
| GET | `/events/{run_id}` | Sự kiện thô theo run |
| GET | `/sample` | Bộ số liệu mẫu, suy ra từ fixtures |

## Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `DEEPSEEK_API_KEY` | trống | Chỉ cần cho `mode=llm` |
| `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | `deepseek-v4-flash`, `https://api.deepseek.com` | Model và địa chỉ |
| `DEEPSEEK_TIMEOUT`, `DEEPSEEK_MAX_TOKENS`, `DEEPSEEK_BACKOFF_BASE` | 60, 2000, 1 | Timeout, token tối đa mỗi lượt, cơ số chờ khi thử lại |
| `LLM_RUN_TOKEN_BUDGET` | 20000 | Hạn mức token mỗi run; hết thì dùng văn bản mẫu |
| `LLM_PRICE_IN_PER_M`, `LLM_PRICE_OUT_PER_M` | 0 | Giá USD/1 triệu token để ước tính chi phí; để 0 nếu chưa có giá chính thức |
| `TASK_TIMEOUT_S`, `LLM_TASK_TIMEOUT_S` | 5, 200 | Timeout mỗi task ở Mock / LLM |
| `MOCK_STEP_DELAY_S` | 0.8 | Nhịp chậm mỗi task ở Mock để xem dashboard; test đặt 0 |
| `APPROVAL_THRESHOLD_PHP` | 5000 | Ngân sách bản nháp từ mức này phải chờ người duyệt |
| `DEMO_DB_PATH` | `/app/data/demo.sqlite` | Đường dẫn SQLite |

## Phương án A — Endpoint dự kiến (KẾ HOẠCH, CHƯA TRIỂN KHAI / KE HOACH, CHUA TRIEN KHAI)

> **Lưu ý:** Toàn bộ các endpoint mới và phần mở rộng dưới đây thuộc **Phương án A** (`docs/DEMO_PLAN_OPTION_A.md` mục 8.1), hiện ở trạng thái **KẾ HOẠCH, CHƯA TRIỂN KHAI** (`KE HOACH, CHUA TRIEN KHAI`).

| Method | Đường dẫn | Mục đích | Phase |
|---|---|---|---|
| POST | `/admin/reset-demo` | Mở rộng thân: thêm `include_memory: bool` (mặc định `false`; khi `false` thì đề xuất đang mở thành `EXPIRED`, khi `true` xóa cả `memory_items` và `learning_proposals`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A2 |
| POST | `/runs` | Mở rộng thân: thêm `max_rework` (0..2, mặc định 0), `rooms: bool` (mặc định `false`), `use_memory: bool` (mặc định `false`); trả 422 nếu ngoài miền — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A4, A5, A6 |
| GET | `/runs/{run_id}` | Mở rộng phản hồi: thêm `rework`, `rooms_summary`, và `last_dispatch {rule, reason}` + `memory_used` cho từng task (tăng tối đa 2 KB) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A1, A4–A6 |
| GET | `/runs/{run_id}/rework` | Xem danh sách yêu cầu làm lại (`rework_requests`), phát hiện lỗi, phép kiểm và trạng thái từng vòng của run — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A4 |
| GET | `/runs/{run_id}/rooms` | Danh sách phòng thảo luận (`rework`, `risk`) của run kèm trạng thái và số vòng/tin — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A5 |
| GET | `/runs/{run_id}/rooms/{room_id}/messages` | Lời thoại chi tiết trong phòng thảo luận (`say`, `pass`, `skip`, cảnh báo số `number_warn`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A5 |
| GET | `/memory?agent=&status=` | Danh sách mục ký ức dài hạn (`memory_items`), lọc theo `agent` và `status` (`ACTIVE`/`RETIRED`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A6 |
| GET | `/memory/{key}/versions` | Lịch sử các phiên bản của một khóa ký ức `key` — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A6 |
| POST | `/memory/{id}/retire` | Rút lại mục ký ức đang `ACTIVE` sang `RETIRED` (404 / 409) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A6 |
| POST | `/memory/{key}/restore/{version}` | Khôi phục bản `version` của `key` thành bản `N+1 ACTIVE` qua `memory.activate()` (404 / 409 / 422 lint) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A6 |
| GET | `/learning/proposals?status=` | Danh sách đề xuất tự học (`learning_proposals`), lọc theo `status` — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| POST | `/learning/proposals/{id}/replay` | Chạy kiểm thử phát lại tất định (chỉ đọc) cho đề xuất học, cập nhật trạng thái `REPLAYED_PASS`/`REPLAYED_FAIL` và `active_hash` — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| POST | `/learning/proposals/{id}` | Duyệt hoặc từ chối đề xuất học (thân `{"decision": "APPROVED"\|"REJECTED"}`; 409 nếu sai trạng thái/đã quyết/phát lại cũ; 422 nếu có trường lạ như `by`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| GET | `/learning/runs` | Nhật ký các lượt chạy đường học (`learning_runs`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| GET | `/learning/routing-stats` | Thống kê điều phối theo agent × task từ `dispatch`/`dispatch_result` (chỉ hiển thị) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| GET | `/inbox` | Hộp duyệt chung (chỉ đọc): gộp `approvals` đang `PENDING` và đề xuất học chờ duyệt — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A7 |
| GET | `/adapters` | Danh sách cổng adapter mở rộng (`[{port, kind, mode: "mock", available}]`) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a |
| GET | `/adapters/outbox` | Hộp thư ra nháp của kênh mock: thẻ `ap:` đã lưu và thẻ `lp:` dựng khi đọc — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a, A8b |
| POST | `/adapters/channels/{kind}/mock-inbound` | Giả lập tin nhắn vào kênh mock, kiểm `access_decide` và ghi `channel_inbox` chống trùng — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a |
| POST | `/adapters/channels/{kind}/mock-callback` | Giả lập callback bấm nút duyệt `ap:`/`lp:` trên kênh mock (`{sender_id, data}`; 400 / 403 không phải owner / 404 / 409 đã quyết) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a, A8b |
| GET | `/adapters/brain/search?q=` | Tìm kiếm văn bản trên Second Brain mock (`Reader` do server đặt) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a |
| GET | `/adapters/brain/page?page=` | Đọc trang Second Brain mock (`Reader` do server đặt; trang bị cấm hoặc không có đều trả 404) — *KẾ HOẠCH, CHƯA TRIỂN KHAI* | A8a |

