# Trạng thái triển khai (nguồn duy nhất về trạng thái phase)

Cập nhật: 05/11/2026 (Phase 0–9 DONE; 1/2 lời gọi DeepSeek thật đã dùng; bước tiếp: phương án A theo `DEMO_PLAN_OPTION_A.md`).

Trạng thái: `NOT_STARTED` · `IN_PROGRESS` · `DONE` · `PARTIAL` · `BLOCKED`. Chỉ DONE khi tiêu chí nghiệm thu trong `DEMO_ONLY.md` đạt và có bằng chứng ở `DEMO_TEST_REPORT.md`.

| Phase | Tên | Trạng thái | Đã làm | Còn thiếu để DONE |
|---|---|---|---|---|
| 0 | Audit và chuẩn bị | **DONE** | Đọc toàn bộ project; probe container; AS-IS có bằng chứng; sơ đồ AS-IS/TO-BE; bộ tài liệu; `tests/test_smoke.py` chạy PASS trong container; live smoke `/health`, `/agents`, `/sample`, `/demo/run`, `/events/{run_id}` | — |
| 1 | Sửa DeepSeek và lỗi hệ thống | **DONE** | `app/llm/deepseek.py` (timeout, retry 429/5xx/timeout, empty/length handling, `llm_calls` log); `app/llm/mock_llm.py`; Mock Mode mặc định; `DEMO_DB_PATH`; test MockTransport PASS trong container | — |
| 2 | Mock Business Environment | **DONE** | Deterministic Philippines fixtures in `app/mock/fixtures.json`; ten read-only `/mock/*` APIs; all responses marked `MOCK_ONLY`/synthetic; independent endpoint and fixture-isolation tests | — |
| 3 | Commander và Workflow Engine | **DONE** | `app/db.py` (8 bảng, migrate idempotent), `app/core/graph.py` (đồ thị 14 task, máy trạng thái thuần), `app/core/workflow.py` (chạy theo dependency, timeout, FAILED/SKIPPED, retry giữ artifact cũ, cancel, recover sau restart, replay), `app/runs_api.py`; Gemini: test bảng graph/data + 12 hội thoại | Agent thật thay `placeholder` ở Phase 4 |
| 4 | 13 Agents | **DONE** | `app/core/registry.py` (13 vai trò: tool, quyền, output), `app/core/artifacts.py` (14 schema), `app/agents/business.py` (9 agent nghiệp vụ + Commander, số học Python), `app/agents/supervisors.py` (QA schema, Audit quyền, Monitor), `app/agents/narrate.py` (Mock template / DeepSeek có hạn mức token), `/demo/run` thành wrapper của `/runs`; Gemini: 14 mẫu văn bản + 138 ca test bảng | QA kiểm phép tính, chặn WRITE thật, error injection → Phase 5 |
| 5 | Supervisory Agents và kiểm tra chéo | **DONE** | `app/engines/qa.py`, `audit.py`, `monitor.py` (thuần, không import LLM); `app/core/gateway.py` (điểm "Act" duy nhất); supervisor = báo cáo từ `engine_results`; 5 lỗi giả lập; phụ thuộc mềm; HITL duyệt khi vượt ngưỡng; Gemini: 148 ca test bảng engine + đồ thị | — |
| 6 | Dashboard văn phòng 3D | **DONE** | three.js r160 trong `app/web/vendor/`; Claude: `office3d.js` (đảo, 13 phòng, nhân vật, bong bóng, tài liệu bay, cổng mock đổi màu, chuông duyệt), `office-layout.js`, `main.js` (API, polling, nối cảnh–panel), route `/dashboard` + `/static`, nhịp chậm Mock; Gemini: `dashboard.html`, `styles.css`, `panels.js`, `office-props.js` | — |
| 7 | ARIS Runtime | **DONE** (đánh giá + tích hợp một phần) | `docs/DEMO_ARIS_EVALUATION.md`: MIT, ngừng phát triển, chạy trên DeepSeek Harness rc; cài + build OK trên Docker Linux, 1.206/1.209 test qua; `tools/aris-adapter/spike.mjs` chạy `planCards`/`dispatch` thật của ARIS điều khiển 4 agent LevelUp bằng mock tool (0 lời gọi LLM), dự phòng về runtime nội bộ đã kiểm | ARIS runtime đầy đủ không tích hợp (Commander là LLM, vượt hạn mức D-06) — ghi rõ, không tính là tích hợp |
| 8 | Kiểm thử E2E | **DONE** | `tests/e2e/test_e2e_api.py` (S1–S5 + replay + dashboard, HTTP thật), `tools/e2e/run_e2e.py` (container riêng 8090/8091, kịch bản khởi động lại container), Gemini: `tests/e2e/browser/dashboard.e2e.mjs` (8 kịch bản Chromium); kết quả 7/7 + restart + 8/8; sửa lỗi task kẹt RUNNING khi restart | — |
| 9 | Đóng gói và bàn giao | **DONE** | README mới, `docs/DEMO_API.md`, `POST /admin/reset-demo` (+ test), `.dockerignore`, `docs/DEMO_FINAL_REPORT.md` (7 câu hỏi, sơ đồ, code/mock/LLM, hạn chế); 1 lời gọi DeepSeek thật kiểm API; build lại và chạy lại container chính | — |

## Rà soát lại Phase 0–2 (05/11/2026)

Code có thật và chạy được, nhưng còn các lỗi sót sau, **đã sửa**:

| Phase | Lỗi | Bằng chứng | Sửa |
|---|---|---|---|
| 0 | Test ghi vào DB demo thật | số run 12 → 13 sau một lần `pytest`; 21 dòng `llm_calls` giả trong DB | `tests/conftest.py` đặt `DEMO_DB_PATH` tạm; đo lại 13 → 13 |
| 0 | Test nạp API key thật từ `.env` | test `llm-without-key` nhận 202 thay vì 400 | conftest luôn xóa `DEEPSEEK_API_KEY` |
| 0 | Báo cáo ghi 6 passed, thực tế 8 test | `pytest` | báo cáo cập nhật |
| 1 | Lượt gọi lỗi (HTTP, timeout, response hỏng) không ghi `llm_calls` | đọc code | ghi mọi lượt; test `HTTP_503` ×2 |
| 1 | Chưa có test UTF-8 qua SQLite + API (M-04) | — | test byte tiếng Việt qua `/events` |
| 1 | Test chậm 9,5 s vì ngủ thật khi retry | `pytest` | `DEEPSEEK_BACKOFF_BASE`; suite 1,7 s |
| 1 | `with sqlite3.connect()` không đóng kết nối | đọc code | `db.tx()` commit + đóng |
| 2 | Chỉ 2 sản phẩm, thiếu LU-PH-003 (M-10) | fixtures | thêm LU-PH-003 + NCC C |
| 2 | Hai nguồn số liệu: `SAMPLE` trong `main.py` và fixtures | đọc code | `/sample` suy ra từ fixtures (`app/mock/data.py`) |
| 2 | Chưa áp lỗi giả lập theo run | — | `facts_for(inject)`; test run lỗi 9999, run sạch 180 |

Còn lại, không chặn: 21 dòng `llm_calls` giả cũ (`run_id` rỗng) trong DB demo, không ảnh hưởng số theo run; `app/main.py.bak` còn trong thư mục (bản sao lưu, chưa xóa); `/demo/run` cũ chưa chuyển sang `/runs` (Phase 4).

## Chi tiết Phase 0 và Phase 1 (04/11/2026)

- Docker image build: **PASS**.
- Container tests: `docker compose run --rm demo pytest -p no:cacheprovider -q` → **6 passed in 9.72s**.
- Live smoke: `/health` → `ok`; `/agents` → 13 agents; `/sample` → dữ liệu synthetic UTF-8; `/demo/run` Mock Mode → run `f193c071-4d30-4194-acdf-b576dd1e7176`; `/events/{run_id}` → 31 events.
- DeepSeek thật: **0 calls**; toàn bộ test LLM dùng `httpx.MockTransport`.

## Chi tiết Phase 0 (04/11/2026)

**Hiện trạng thực tế** (bằng chứng ở `DEMO_ARCHITECTURE.md` §1):
- Chạy được: container healthy; `/health`, `/agents`, `/sample`, `/events/{id}`, `/demo/run` (Mock trả 13 chuỗi giống nhau; LLM gọi 13 lượt tuần tự).
- Lỗi/thiếu đã xác định: `use_llm` mặc định `True`; response rỗng vẫn `task_completed`; `max_tokens=1000`, không retry, không token log; không dependency/trạng thái/retry/cancel/checkpoint; không artifact; engine là dict cứng; không test; không dashboard.
- Encoding: API/SQLite UTF-8 đúng; `../result.json` mojibake do PowerShell (M-04, chốt bằng test ở Phase 1).
- Môi trường: Docker 29.9.2, Compose v5.6.1, Python host 3.11 (không dùng; test chạy trong container, M-13).

**Lời gọi DeepSeek thật trong đợt này:** 0 / 2.

## Bộ đếm toàn dự án

| Chỉ số | Giá trị |
|---|---|
| Agent hoạt động đúng (có artifact riêng, qua QA) | 13 / 13 |
| Engine độc lập LLM | 3 / 3 |
| Kịch bản E2E PASS | 5 / 5 (+ restart, + 8 kịch bản trình duyệt) |
| Dashboard dùng được | Có: `http://localhost:8088/dashboard` (3D) và `?mode=2d` |
| ARIS | Đã đánh giá; tích hợp thật phần `dispatch`/`planCards` qua adapter, không thay runtime |
| Lời gọi DeepSeek thật | 1 / 2 |
| Test tự động | 441 passed + E2E 7 API / restart / 9 trình duyệt (05/11) |

## Phương án A (06/11/2026)

| Phase | Mục tiêu | Trạng thái |
|---|---|---|
| A0 | Chốt quyết định, tài liệu | **DONE** |
| A1 | Nhật ký điều phối | **DONE** |
| A2 | DB v3 | ĐANG SOẠN PHIẾU PHẠM VI |
| A3 | Gateway chạy lại an toàn | NOT_STARTED |
| A4 | Vòng làm lại | NOT_STARTED |
| A5 | Phòng thảo luận | NOT_STARTED |
| A6 | Ký ức: lưu và đọc | NOT_STARTED |
| A7 | Tự học | NOT_STARTED |
| A8a | Adapter: cổng + mock | NOT_STARTED |
| A8b | Adapter: thẻ `lp:` | NOT_STARTED |
| A9 | Hoàn thiện dashboard và API | NOT_STARTED |
| A10 | E2E và bàn giao | NOT_STARTED |

A0: hoàn tất 23/11/2026. Baseline mới đo lại 3 lần: pytest 441 passed/7 skipped, E2E API 7/7, restart OK, trình duyệt 9/9 (cả 3 lần). Sửa `tests/e2e/browser/dashboard.e2e.mjs` (timeout checkbox 5000ms → 15000ms, có kiểm tra ngay sau khi tick) sau khi xác nhận không có lỗi ứng dụng gây mất trạng thái tick. Image tag `levelup-vmm-demo:baseline-v2` (ID `d041ad35b2a7`). Xem `DEMO_TEST_REPORT.md` mục "A0 — mốc cơ sở 23/11/2026" và `DEMO_HANDOFF.md`.

A1: Jarvis nghiệm thu 24/11/2026 (chưa commit); A2 được mở cùng ngày, đang soạn phiếu phạm vi. Mỗi lần giao việc (`dispatch`) và kết quả (`dispatch_result`) ghi vào `decision_log` kèm lý do (ví dụ "Mọi phụ thuộc đã hoàn tất: …", "Làm lại lần thử #2…"), không đổi schema DB. Mỗi trường objective nhập tay (market/product/price/budget) ghi rõ nguồn: `fixture` | `extracted` | `default` (default → `needs_review`); thị trường khác Philippines luôn kèm `currency_note` nói rõ vẫn tính bằng PHP. Tab "Nhật ký" trên web hiện cột "Lý do / Nguồn" và banner cảnh báo khi có `needs_review`/`currency_note`. Màn hình "bấm lùi" đầy đủ và bong bóng 3D lùi sang A9 theo phiếu đã duyệt; A1 chỉ bảo đảm API trả đủ liên kết (`tasks[].last_dispatch`, `inputs_from`). Test mới: `tests/test_dispatch.py` (9 test). Kiểm thử toàn luồng 3 lần: pytest 450 passed/7 skipped (trong container), E2E API 7/7, restart OK, trình duyệt 9/9 — cả 3 lần, không đụng `levelup-vmm-demo:baseline-v2` hay `openmausbot-computer`. Xem `DEMO_TEST_REPORT.md` mục "A1" và `DEMO_HANDOFF.md`.
