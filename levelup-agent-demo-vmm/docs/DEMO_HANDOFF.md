# Handoff

Trạng thái từng phase: `DEMO_PHASE_STATUS.md` (nguồn duy nhất). Checkpoint bên dưới là mốc lịch sử, mới nhất ở trên. Phiên sau bắt đầu bằng prompt ở `DEMO_PLAN.md` mục 9.

## Checkpoint 25/11/2026 — A4 đã nghiệm thu: vòng làm lại

- Triển khai đúng phiếu "A4 mở" bên dưới trên nhánh `phase-a4-rework`. Chi tiết, 3 chỗ lệch đặc tả có lý do, số test: `DEMO_TEST_REPORT.md` mục "A4". Log: `latest_logs/a4-rework-20261125/`.
- File đổi: `app/core/graph.py`, `app/agents/checks.py` (mới), `app/core/workflow.py`, `app/agents/__init__.py`, `app/engines/monitor.py`, `app/runs_api.py`; test `tests/test_rework.py` (mới), `tests/test_rework_plan_table.py` + `tests/test_checks_table.py` (Gemini), `ai-jobs/oa-a4/`.
- Gemini chạy trên bản sao sạch trong scratchpad như A3 (lý do ở checkpoint A3).
- Dashboard không đổi; `GET /runs/{id}` có thêm khóa `rework` để A9 vẽ.
- Chủ dự án nghiệm thu 25/11/2026, đã commit/push nhánh `phase-a4-rework`.
- **Bước tiếp theo:** mở A5 (phòng thảo luận) hoặc A8a (adapter).

## Checkpoint 25/11/2026 — A4 mở: phiếu phạm vi đã chốt

- Nhánh `phase-a4-rework` tách từ `fd197b1` (A3 đã nghiệm thu, đã push).
- **Phạm vi (đúng `DEMO_PLAN_OPTION_A.md` §7.2 phần A4, bước 1–11, và prompt A4):**
  - `graph`: `can_rework()` chỉ cho COMPLETED→PENDING; `rework_plan(findings, statuses, rounds_used, graph, soft, max_rework, fixable)` trả kế hoạch hoặc `(None, lý do)` với `business_task_not_completed` / `no_fixable_rule` / `exhausted`. Không sửa `TRANSITIONS`, `retry()`, `retry_plan()`.
  - `app/agents/checks.py` (mới): `CHECKS`, `FIX` = {QA `reference` → `verify_supplier_cost:<sku>` (cấp facts, learnable), Audit `blocked_action` → `drop_blocked_action:<tool>` (cấp artifact, không learnable)}; `apply_facts` / `apply_artifact` thuần, trả before/after.
  - `workflow`: móc ở điểm `next_ready == 'monitor'` khi `max_rework > 0`; chốt yêu cầu cũ (RESOLVED / NO_CHANGE / EXHAUSTED), lập kế hoạch mới; ghi `rework_requests` + `rework_requested` (agent 01) / `rework_resolved` / `rework_skipped` (chỉ khi có FAIL hoặc task nghiệp vụ FAILED/SKIPPED); `Ctx` thêm `feedback`, `memory`, `rework`, `checks`; phép kiểm cấp facts áp cho mọi task chạy lại; `check_applied` ghi trong tx của `task_completed`; task trong `changes` luôn narrative mock; `evidence()['rework']`.
  - Monitor: WARN `reworked` (khác `retried`) và `rework_exhausted`. `runs_api`: `max_rework` 0..`MAX_REWORK_CEILING=2`, mặc định 0, ngoài miền 422. `get_run` trả dữ liệu rework để A9 vẽ.
  - Test `tests/test_rework.py`: các ca S6 (`bad_cost` + `max_rework=2` → 1 vòng `product`, QA PASS, HOLD_DRAFT, giá vốn 180; `publish_attempt` → `campaign` bỏ `meta_ads.publish`, Audit PASS; `missing_field:offer` → FAILED, NEEDS_REVIEW, `rework_skipped`), run lành không có dòng làm lại, hai lần chạy cùng chuỗi decision_log, `max_rework=0` không đổi hành vi cũ, 422 khi `max_rework=3`, `mode=llm` với client giả không tạo `llm_calls` cho task làm lại.
- **Lùi sang A9 (chủ dự án chọn 25/11/2026, như A1):** tài liệu đỏ + bong bóng "Làm lại: <luật>" + dấu tích trong văn phòng 3D, và ô `max_rework` trên form Start (mặc định 2 theo OA-D02). A4 không đổi dashboard.
- **Ngoài phạm vi A4:** ký ức `check` đã ghim trong `active_checks` (A6); phòng thảo luận (A5). `Ctx.memory` chỉ có giá trị mặc định.
- **Gemini** (`ai-jobs/oa-a4`): bảng test `rework_plan` (đích, hậu duệ, giới hạn, các lý do None, retry + làm lại cùng run) và `FIX`. Bỏ phần chữ 3D vì UI lùi sang A9.
- Ghi chú đọc đặc tả: S6 "decision-log có `rule='rework'` ở task chạy lại" hiểu là dòng `rework_requested` của task đích có `detail.rule` và dòng `dispatch` của task chạy lại có lý do làm lại. Sẽ ghi lại nếu cách hiểu khác.
- **Bước tiếp theo:** triển khai A4 theo phiếu trên.

## Checkpoint 25/11/2026 — A3 đã nghiệm thu: gateway chạy lại an toàn, dừng khẩn, token

- Triển khai đúng phiếu "A3 mở" bên dưới trên nhánh `phase-a3-gateway-rerun`. Chi tiết, số test, hạn chế: `DEMO_TEST_REPORT.md` mục "A3". Log: `latest_logs/a3-gateway-20261125/`.
- File đổi: `app/core/gateway.py`, `app/core/workflow.py` (`tool_calls`, dừng trong `execute`, `decide_approval(actor)`), `app/agents/__init__.py`, `app/auth.py` (mới), `app/runs_api.py`, `app/main.py` (kiểm cấu hình khi khởi động), `app/web/main.js`, `.env.example`, `tests/test_phase5.py`, `tests/test_a3_gateway_stop.py` (mới), `tests/test_gateway_attempt_table.py` (Gemini), `ai-jobs/oa-a3/`.
- Gemini: không chạy trong `_gemini-work` vì thư mục đó đang bị repo gốc theo dõi (128 file) và đã cũ so với code (`.git` của nó bị đổi thành `.git.bak`). Thay bằng bản sao sạch có git riêng trong scratchpad của phiên (cùng nguyên tắc: Gemini làm trên bản sao, runner kiểm ghi lạc = 0, Claude nghiệm thu rồi mới chép về). Nên dọn `_gemini-work` khỏi git ở một lượt riêng.
- **Việc của chủ dự án trước khi tạo lại container chính:** thêm `AUTH_OWNER` (và `AUTH_DELEGATES` nếu cần) vào `.env`, token ≥ 16 ký tự. Thiếu thì app vẫn chạy nhưng không ai bấm Duyệt/Dừng được.
- Chủ dự án nghiệm thu 25/11/2026, đã commit/push nhánh `phase-a3-gateway-rerun`.
- **Bước tiếp theo:** mở A4 (vòng làm lại) hoặc A8a (adapter, làm song song được sau A3).

## Checkpoint 25/11/2026 — A3 mở: phiếu phạm vi đã chốt

- Sửa ngoài phạm vi trước khi mở: SeleniumBase cài global trên máy host tự nạp vào pytest và xóa sạch `latest_logs/` mỗi lần chạy (nguyên nhân log A1 mất ở checkpoint A2; làm mất luôn `latest_logs/a2-pre-migrate/demo.sqlite.bak`, file không có trong git). `pytest.ini`: `addopts = -p no:seleniumbase`, `testpaths = tests`. Commit `3f4e8f2` trên `phase-a2-db-v3`, đã push. Không để bản sao lưu trong `latest_logs/` nữa.
- Nhánh `phase-a3-gateway-rerun` tách từ `3f4e8f2`.
- **Phạm vi phần 1 (`DEMO_PLAN_OPTION_A.md` §7.2):** `gateway.execute(..., attempt)` lưu `attempt` + `action_hash` (sha256 JSON chuẩn hóa) trong `detail`, ghi `approvals.tool`; luôn gọi `audit.check_action` trước; dùng lại chỉ khi trùng `(run_id, task_key, tool, target, action_hash)` với dòng không BLOCK và trùng phán quyết → không tạo DRAFT/approval mới, vẫn ghi dòng `tool_call` mới chép đủ `detail` + `reused=true`; `workflow.tool_calls()` chỉ giữ lần thử hiện tại (thiếu `attempt` = 1). Test theo kế hoạch (ngưỡng 3000 qua monkeypatch), hồi quy retry, E2E giữ nguyên.
- **Phạm vi phần 2 (chuyển từ A2, quyết định 24/11 trong `DEMO_KE_HOACH_NANG_CAP_4_MOC.md` mục 2):**
  - Dừng khẩn: không dispatch task mới khi `system_stop.stopped=1` (task đang chạy được chạy xong, task chờ giữ PENDING, mở lại thì chạy tiếp). `POST /runs` khi đang dừng → **409** (chủ dự án chọn).
  - Định danh: **token riêng mỗi người** (chủ dự án chọn). Header `Authorization: Bearer <token>`; env `OWNER_TOKEN` và danh sách người được ủy quyền tên:token, giới hạn `MAX_AUTHORIZED=3` (cấu hình, nâng được không sửa mã). Không token/sai → 401; đúng nhưng không đủ quyền → 403. Không ghi token vào log/DB, chỉ ghi tên.
  - Quyền: người được ủy quyền duyệt/từ chối và dừng khẩn; chỉ chủ dự án mở lại. Quyết định ghi trước có hiệu lực, người sau nhận 409. `approvals.decided_by` và `system_stop.actor` = tên server suy ra từ token.
  - Hệ quả cần xử lý trong A3: dashboard và E2E đang gọi approve/stop không có token → container E2E đặt token thử; dashboard hỏi token một lần khi gặp 401 và giữ trong `sessionStorage` (sửa tối thiểu, UI đầy đủ để A9).
- **Gemini** (`ai-jobs/oa-a3`): bảng test cho bộ lọc theo lần thử (chỉ dữ liệu, Claude review).
- Không làm: vòng làm lại (A4), UI ngoài phần token tối thiểu, không gọi DeepSeek thật.
- **Bước tiếp theo:** triển khai A3 theo phiếu trên.

## Checkpoint 25/11/2026 — A2 đã nghiệm thu: DB v3, chốt dừng khẩn (chỉ lưu trữ)

- Jarvis duyệt phiếu phạm vi A2 (gồm cả bảng `system_stop`/`system_stop_log` làm ngay trong A2) và cho commit/push A1 lên GitHub trước khi bắt đầu. Nhánh `phase-a2-db-v3` tách từ `phase-a1-dispatch` (`25ee168`). Jarvis nghiệm thu A2 ngày 25/11/2026, đã commit/push nhánh `phase-a2-db-v3`; A3 chưa mở.
- `app/db.py`: `SCHEMA_VERSION=3`; `_migrate_alter()` kiểm `PRAGMA table_info` trước mỗi `ALTER` nên chạy lại trên volume v2 không lỗi và không mất run cũ (M-06). Thêm bảng khung cho A4/A5 (`rework_requests`, `rooms`, `room_messages`), A6/A7 (`memory_items` với chỉ mục duy nhất một phần `key WHERE status='ACTIVE'`, `learning_proposals`, `learning_runs`, `learning_meta`), A8a/A8b (`channel_inbox`, `channel_outbox`, `brain_inbox`). Thêm `system_stop`/`system_stop_log` (mới, ngoài `DEMO_PLAN_OPTION_A.md` gốc) kèm `get_stop_state()`/`set_stop()` có logic thật ngay, để A3 dùng sẵn.
- `app/core/workflow.py`: `RESET_TABLES` mở rộng, xóa bảng con trước. `reset_demo(include_memory=False)` (mặc định) giữ `memory_items`/`learning_proposals` đã quyết, chuyển đề xuất đang mở sang `EXPIRED`; `include_memory=True` xóa thêm hai bảng đó (chỉ dùng trên DB thử, test có kiểm). `learning_meta`/`system_stop*` không bao giờ bị reset đụng tới.
- `app/runs_api.py`: `ResetRequest.include_memory`; `GET/POST /admin/stop`, `POST /admin/resume` — chỉ lưu/đọc trạng thái, **chưa chặn dispatch mới và chưa kiểm ai được phép bấm** (để A3).
- Test mới `tests/test_db_migrate.py` (6 ca, xem `DEMO_TEST_REPORT.md` mục "A2"). Đo 3 lượt: `pytest` local 456 passed; `pytest` trong container 456 passed/7 skipped; `python tools/e2e/run_e2e.py` API 7/7 + restart OK + trình duyệt 9/9. 0 lời gọi DeepSeek thật. Không đụng `lalahoa-db`/`aiops-demo-n8n-1`/`openmausbot-computer`.
- Log: `latest_logs/a2-db-v3-20261125/`. Cập nhật `DEMO_TEST_REPORT.md`, `DEMO_PHASE_STATUS.md` (A2 → DONE), file này.
- Phát hiện ngoài phạm vi (đã sửa khi thấy, không phải lỗi do lượt này gây ra): các file log của A1 ở `latest_logs/a1-dispatch-20261124/` bị xóa khỏi working tree trước khi lượt A2 bắt đầu sửa gì — đã `git checkout --` khôi phục lại từ commit `25ee168`, chưa rõ nguyên nhân xóa.
- **Bước tiếp theo (đã xong, xem checkpoint A3 mở):** mở A3 (gateway chạy lại an toàn: `attempt`/`action_hash`, chặn dispatch mới khi `system_stop.stopped=1`, kiểm danh sách tối đa 3 người được ủy quyền).

## Checkpoint 24/11/2026 — A1 Jarvis nghiệm thu: nhật ký điều phối có lý do

- Jarvis duyệt phiếu phạm vi A1, triển khai trên nhánh `phase-a1-dispatch`; nghiệm thu xong cùng ngày, commit `25ee168` (đã push lên GitHub ở lượt mở A2).
- `app/core/graph.py` thêm hàm thuần `dispatch_reason()` + `DISPATCH_REASON`, không sửa `TRANSITIONS`. `app/core/workflow.py` ghi `dispatch`/`dispatch_result` vào `decision_log` (không đổi schema DB, dùng cột `detail` JSON có sẵn). `app/mock/data.py` trả `input_sources` (`fixture`/`extracted`/`default`, default → `needs_review`) và `currency_note` khi thị trường khác Philippines. `app/web/panels.js` tab Nhật ký hiện lý do/nguồn.
- Test mới `tests/test_dispatch.py` (9 ca). Đo 3 lượt: pytest 450 passed/7 skipped trong container; E2E 3 lần liên tiếp đều API 7/7, restart OK, trình duyệt 9/9. 0 lời gọi DeepSeek thật.
- Lùi theo phiếu đã duyệt: màn hình "bấm lùi từ quyết định cuối về dữ liệu đầu vào" đầy đủ và bong bóng "Giao việc → agent" trong văn phòng 3D sang A9; A1 chỉ bảo đảm API trả đủ liên kết.
- Log: `latest_logs/a1-dispatch-20261124/`.
- **Bước tiếp theo:** A2 — nâng DB v3 (xem checkpoint 25/11/2026 ở trên).

## Checkpoint 23/11/2026 — A0 DONE: baseline mới, tag baseline-v2

- Người dùng duyệt tiếp A0. Đo lại hoàn toàn, không dùng số cũ; không mở A1, không commit/push.
- Lần đo đầu (16:26–16:41): pytest 441 passed/7 skipped; E2E 2 lần: API 7/7, restart OK, trình duyệt 8/9 rồi 7/9 — lỗi `locator.check` timeout chập chờn, mỗi lần ở ca injection khác nhau. Ca `dock-and-viewport` (lỗi cũ 06/11) **đạt cả hai lần**, kết luận ca đó đã hết lỗi.
- Điều tra: đọc `app/web/panels.js`, `app/web/main.js` — không có re-render hay CSS transition nào xóa trạng thái checkbox tình huống; `startFormBody` là DOM tĩnh, `renderOverview()` (chạy mỗi 1s khi poll) không đụng tới nó. Không có lỗi ứng dụng tái hiện được → xác nhận lỗi chập chờn do script/môi trường (tranh tài nguyên Docker khi `lalahoa-db`, `aiops-demo-n8n-1`, `openmausbot-computer` chạy song song), không phải lỗi logic dashboard.
- Sửa `tests/e2e/browser/dashboard.e2e.mjs`: tăng timeout `.check()`/`.uncheck()`/`.selectOption()` từ 5000ms → 15000ms, thêm `assert.ok(isChecked())` ngay sau mỗi lần tick để lộ sớm nếu không giữ trạng thái. Không sửa mã `app/web/`.
- Tạm dừng `lalahoa-db` (DB thử local của LaLaHoa, không phải DB thật trên VPS) và `aiops-demo-n8n-1`, không đụng `openmausbot-computer`. Chạy `pytest` (441 passed/7 skipped) rồi `python tools/e2e/run_e2e.py` 3 lần liên tiếp: cả 3 lần API 7/7, restart OK, trình duyệt **9/9 PASS**. Bật lại 2 container ngay sau khi đo.
- Build lại image, gắn tag `levelup-vmm-demo:baseline-v2` (ID `d041ad35b2a7`). Cập nhật `DEMO_TEST_REPORT.md`, `DEMO_PHASE_STATUS.md` (A0 → DONE), file này.
- Log/ảnh: `latest_logs/a0-baseline-20261123/` (lần PARTIAL) và `latest_logs/a0-baseline-20261123/rerun2/run1-3.log` (3 lần đạt sau khi sửa).
- DeepSeek thật: không gọi mới, sổ vẫn 1/2.
- **Bước tiếp theo:** chờ chủ dự án quyết định mở A1 (nhật ký điều phối) và chốt 2 việc còn treo — ai được ủy quyền duyệt/dừng/mở lại và kích hoạt ký ức; ngưỡng dữ liệu đủ để kết luận (chốt ở F1, chưa cần ngay).

## Checkpoint 06/11/2026 — A0 PARTIAL: tài liệu xong, baseline bị chặn

- Người dùng xác nhận đã hoàn thành UX và yêu cầu triển khai đúng A0. Không sửa app/, không nhảy A1.
- Đã thêm OA-D01..13 (mặc định theo §17.1), OA-M01..18, sửa nguyên tắc Learn, thêm sơ đồ TO-BE và bảng trạng thái A0–A10 (có A8a/A8b).
- Gemini `ai-jobs/oa-a0`: bảng API kế hoạch đã review và đưa vào DEMO_API.md; 120.4 giây, exit 0, stray writes 0.
- Docker Desktop khởi động nhưng daemon không sẵn sàng: log `HEAD /_ping: context deadline exceeded`, backend báo chưa chạy sau hơn 4 phút. Đã thử start và restart. Chưa chạy được baseline mới và chưa gắn tag `levelup-vmm-demo:baseline-v2`.
- File E2E có sẵn `tests/e2e/results/latest.json` là `ok=false`, lỗi `dock-and-viewport` do browser/page bị đóng; không khẳng định đây là lỗi ứng dụng. Handoff trước ghi 9/9 PASS nhưng chưa có baseline mới xác nhận.
- Tiếp theo: khi Docker engine hoạt động, chạy `docker compose build -q`, `docker compose run --rm -T demo pytest -p no:cacheprovider -q`, `python tools/e2e/run_e2e.py`. Chỉ khi xanh mới tag image và ghi image ID + số test vào TEST_REPORT, chuyển A0 DONE. Nếu lỗi UI tái hiện, báo rõ trước khi mở rộng phạm vi A0 (A0 yêu cầu không sửa code).
- DeepSeek: không gọi mới, sổ vẫn 1/2. A1 chưa triển khai.

## Checkpoint 05/11/2026 (lần 9) — Hoàn thiện UX nghiệp vụ & Thiết kế lại Văn phòng 3D (tham khảo `khanh020905/my-office`)

- **Đã làm:**
  - Hoàn tất phần việc đang dở ở Claude Code ("Môi trường demo Purchasing System") và Codex ("hoàn thiện thiết kế phòng bạn"):
    1. **Ngôn ngữ nghiệp vụ tiếng Việt (`app/web/labels.js`, `app/web/panels.js`, `app/agents/business.py`, `app/agents/supervisors.py`):** thay toàn bộ mã kỹ thuật (`bad_cost`, `publish_attempt`, `HOLD_DRAFT`, `NEEDS_REVIEW`, `HIGH`, UUID…) bằng từ ngữ kinh doanh rõ ràng; bảng Lịch sử hiển thị tên tình huống thử và lý do lỗi cụ thể.
    2. **Cột trái "Tổng quan" & Thanh dưới kéo giãn (`app/web/panels.js`, `app/web/styles.css`):** 4 ô đếm (Đang làm, Chờ làm, Chờ duyệt, Lỗi), danh sách 14 việc của lượt hiện tại, form kịch bản thu gọn, thanh dưới có tay nắm kéo giãn/nhấp đúp/thu gọn (lưu `localStorage`), khóa cuộn trang ở mọi độ phân giải (1440×900, 1280×720, 960×600).
    3. **Thiết kế lại Văn phòng 3D (`app/web/office-layout.js`, `app/web/office-props.js`, `app/web/office3d.js`) tham khảo `khanh020905/my-office`:** bố cục Campus trực giao căn gọn vào khung trống `#office`; tường cắt kiến trúc 14 cm (`#ECE6DC`, viền cắt `#3B4049`, phào `#8D7F70`), vách kính khung thép đen, bảng tên phòng (`P.01`..`P.13`), bảng Sprint Kanban dán giấy nhớ nhiều màu (`sprintBoardTex`), sàn gỗ ghép (`plankTex`) & thảm hạt (`speckTex`), bàn làm việc gỗ óc chó có màn hình + laptop phụ + cốc cà phê + đèn bàn, ghế xoay 5 chấu vắt áo khoác, cây cảnh (`monstera`, `snake`, `bush`), 13 nhân vật chibi có tóc/mắt/má hồng/kính/tai nghe và tay gõ phím khi `RUNNING`, cùng cơ chế tự động chống chồng lấn nhãn 2D (`declutterLabels`).
- **Đã xác minh:** `pytest` **441 passed** + HTTP E2E **7/7 passed** + Browser E2E **9/9 kịch bản PASS** (`load`, `happy-path`, `timeout-then-retry`, `publish-blocked`, `qa-bad-cost`, `overview-2d`, `history-replay`, `dock-and-viewport`, `no-console-errors`).
- **DeepSeek thật:** 1 / 2 (0 lời gọi mới trong đợt này).
- **Bước tiếp theo:** Chủ dự án duyệt `docs/DEMO_PLAN_OPTION_A.md` (các quyết định `OA-D1`..`OA-D5`) để bắt đầu triển khai **Phase A0 — Quyết định và tài liệu** (nhật ký điều phối ở A1, làm lại ở A4, thảo luận ở A5).

## Checkpoint 05/11/2026 (lần 8) — Phase 8, 9 DONE; kế hoạch phương án A

- **Đã làm:** E2E (`tests/e2e/test_e2e_api.py`, `tools/e2e/run_e2e.py`, Gemini: `tests/e2e/browser/dashboard.e2e.mjs`); sửa lỗi task kẹt RUNNING khi container restart (`workflow._interrupt_orphans`); `POST /admin/reset-demo`; README, `docs/DEMO_API.md`, `docs/DEMO_FINAL_REPORT.md`; `.dockerignore`; 1 lời gọi DeepSeek thật; kế hoạch `docs/DEMO_PLAN_OPTION_A.md`.
- **Đã xác minh:** 439 passed; E2E 7/7 API + restart + 8/8 trình duyệt; container chính build lại, healthy.
- **DeepSeek thật:** 1 / 2 (còn 1).
- **Bước tiếp theo:** chủ dự án duyệt `DEMO_PLAN_OPTION_A.md` (mục quyết định OA-D), rồi làm theo phase A của kế hoạch đó.
- Chạy lại E2E sau mỗi thay đổi lớn: `python tools/e2e/run_e2e.py` (container riêng, không đụng dữ liệu chính).

## Checkpoint 05/11/2026 (lần 7) — Phase 7 DONE (theo yêu cầu người dùng, làm trước Phase 8)

- **Đã làm:** clone ARIS vào `D:\LevelUp-Agent-Demo\_aris\aris-agent` (ngoài repo); đánh giá `docs/DEMO_ARIS_EVALUATION.md`; adapter thử `tools/aris-adapter/spike.mjs` + kết quả JSON; build/test ARIS trong container.
- **Đã xác minh:** spike 4/4 thẻ `completed`, guard từ chối giao sớm, fallback COMPLETED; ARIS install + build OK, 1.206/1.209 test qua trên Linux.
- **Không giao Gemini** ở Phase 7: toàn bộ là đánh giá/phán đoán (`DEMO_AGENT_WORKFLOW.md` mục 5).
- **DeepSeek thật:** 0 / 2.
- **Bước tiếp theo:** Phase 8 — E2E 5 kịch bản (Gemini viết script Playwright theo kịch bản Claude), rồi Phase 9 đóng gói.

## Checkpoint 05/11/2026 (lần 6) — Phase 6 DONE

- **Đã làm:** dashboard văn phòng 3D tại `/dashboard` (three.js r160 offline), chế độ 2D `?mode=2d`; Claude: `app/web/office3d.js`, `office-layout.js`, `main.js`, route; Gemini: `dashboard.html`, `styles.css`, `panels.js`, `office-props.js`. Sửa thêm: nhịp chậm Mock (M-30), WARN không chặn tổng kết (M-31), tổng kết không in "None". Mặc định mới M-30…M-32.
- **Đã xác minh:** 435 passed; trình duyệt thật 4 kịch bản + HITL + 2D, FPS 108.
- **DeepSeek thật:** 0 / 2.
- **Bước tiếp theo (theo M-01):** Phase 8 — E2E 5 kịch bản (`tests/e2e`, Playwright theo kịch bản Claude viết; Gemini viết script), rồi Phase 7 (ARIS), Phase 9 (đóng gói).

## Checkpoint 05/11/2026 (lần 5) — Phase 5 DONE

- **Đã làm:** 3 engine thuần (`app/engines/`), Mock Tool Gateway (`app/core/gateway.py`), supervisor chuyển thành báo cáo từ `engine_results`, 5 lỗi giả lập (`app/agents/__init__.py`), phụ thuộc mềm cho task giám sát (`graph.SOFT`), HITL duyệt khi vượt ngưỡng (`POST /runs/{id}/approvals/{aid}`), `get_run` trả `engines` và `approvals`. Gemini batch `p5-engines` (148 ca) đạt. Mặc định mới M-24…M-29.
- **Đã xác minh:** 424 passed trong container; chạy trực tiếp 6 kịch bản (`DEMO_TEST_REPORT.md` Phase 5).
- **DeepSeek thật:** 0 / 2.
- **Bước tiếp theo:** Phase 6 — Dashboard văn phòng 3D theo `docs/DEMO_DASHBOARD_3D.md` và prompt Phase 6 trong `DEMO_PLAN.md`. API đã đủ cho dashboard: `/runs`, `/runs/{id}` (tasks + artifacts + engines + approvals + llm), retry, cancel, approvals, decision-log, llm-calls, `/agents`.

## Checkpoint 05/11/2026 (lần 4) — Phase 4 DONE

- **Đã làm:** registry 13 vai trò, 14 schema artifact, 9 agent nghiệp vụ + Commander tính bằng Python, 3 agent giám sát mức Phase 4, lớp diễn giải Mock/DeepSeek có hạn mức token, `/demo/run` thành wrapper của `/runs`, xóa `app/llm/mock_llm.py` và code chết trong `main.py`. Gemini batch `p4-agents` (14 mẫu văn bản, 138 ca test bảng) đạt. Mặc định mới M-19…M-23.
- **Đã xác minh:** 281 passed trong container; run live Mock → 14 task COMPLETED, Commander `HOLD_DRAFT` vì lỗ 1.062 PHP sau quảng cáo.
- **DeepSeek thật:** 0 / 2 (LLM mode chỉ test bằng client giả).
- **Bước tiếp theo:** Phase 5 — `app/engines/qa.py` (tính lại công thức, nhất quán số giữa artifact, so giá vốn với nguồn tham chiếu), `audit.py` + `app/core/gateway.py` (thực thi `requested_actions`, chặn WRITE_EXTERNAL), `monitor.py`; injection còn thiếu: `timeout`, `missing_field`, `publish_attempt`, `empty_response` (`bad_cost` đã có); supervisor đọc `engine_results`. Gemini Phase 5: test bảng quy tắc engine.

## Checkpoint 05/11/2026 (lần 3) — rà soát Phase 0–2, Phase 3 DONE, thiết kế Dashboard 3D

- **Đã làm:** sửa 10 lỗi sót Phase 0–2 (`DEMO_PHASE_STATUS.md`); Phase 3: `app/db.py`, `app/core/graph.py`, `app/core/workflow.py`, `app/runs_api.py`, `app/mock/data.py`, `tests/test_workflow.py`; Gemini batch `p3-workflow` (test bảng + 12 hội thoại) nghiệm thu đạt; phân công 60/40 (D-15); đặc tả Dashboard văn phòng 3D `docs/DEMO_DASHBOARD_3D.md` (D-16, M-18), sửa prompt Phase 6 và DEMO_ONLY P6 (bổ sung).
- **Đã xác minh:** 133 passed trong container; live `POST /runs?wait=true` với `bad_cost` → 14 task COMPLETED; test không còn ghi DB demo.
- **DeepSeek thật:** 0 / 2.
- **Bước tiếp theo:** Phase 4 — registry 13 agent, artifact schema, `compute()` thật thay `placeholder` (đăng ký vào `workflow.HANDLERS`), `narrate()` mock/LLM, hạn mức token; chuyển `/demo/run` sang `/runs`. Gemini Phase 4: văn bản `mock_llm` 13 agent + test bảng `compute()`.

## Checkpoint 04/11/2026 (lần 2) — Phase 0 và Phase 1 DONE

- **Đã làm:** hoàn tất audit/test scaffolding; thêm DeepSeek client có timeout, retry, empty-response handling và `llm_calls`; Mock Mode mặc định; test smoke và MockTransport.
- **Đã xác minh:** Docker build PASS; `docker compose run --rm demo pytest -p no:cacheprovider -q` → **6 passed in 9.72s**; live smoke `/health`, `/agents`, `/sample`, `/demo/run`, `/events/{run_id}` PASS.
- **DeepSeek thật:** 0 calls; không gửi API key hay request thật.
- **Bước tiếp theo:** Phase 3 — Commander và Workflow Engine (task graph, persistence, retry/cancel/replay).
## Quy ước code (bổ sung dần theo phase)

- Entry giữ `app/main.py`; module mới theo cây ở `DEMO_PLAN.md` §3. Ranh giới import ở `DEMO_ARCHITECTURE.md` §3 (engine không import llm/agents).
- Mọi ghi DB qua helper trong `app/db.py`; giao dịch ngắn; không giữ connection toàn cục qua `await`.
- Mọi hành động "Act" của agent qua `core/gateway.call(...)`; không gọi `/mock/*` ghi trực tiếp từ agent.
- Số liệu chỉ sinh trong `compute()` (Python). `narrate()` nhận artifact đã có số, chỉ viết văn bản; không parse số từ LLM ngược vào artifact.
- Văn bản Mock ở `app/llm/mock_texts.json` (template `{field}` lấy từ `narrate.flat(artifact)`, không chữ số cứng); thiếu trường thì dùng `summary`.
- Agent thật đi qua `app/agents/handle` (mặc định); `workflow.HANDLERS[task_key]` chỉ để ghi đè trong test/injection; test engine đặt `wf.DEFAULT_HANDLER = wf.placeholder`. Hàm `compute` thuần ở `app/agents/business.py`/`supervisors.py`, nhận `(facts, inputs)`; `ctx.inputs` = artifact của dependency, `ctx.facts` = mock data theo run (đã áp inject). Không ghi DB trong agent.
- Test luôn qua `tests/conftest.py` (DB tạm, key rỗng). Không bao giờ chạy test với DB demo.
- Mọi fixture có `"synthetic": true`; mọi response `/runs/*` có `"environment": "MOCK_ONLY"`.
- Test: `pytest` trong container; test dùng DB tạm (`DEMO_DB_PATH` env) không đụng `demo.sqlite`.
- Không ghi API key vào log, artifact, docs. Log lỗi DeepSeek cắt 280 ký tự, bỏ header.
- Tài liệu tiếng Việt; nhãn kỹ thuật (DRAFT, PASS/FAIL, trạng thái) tiếng Anh.

## Còn mở

Xem `DEMO_DECISIONS.md` mục "Câu hỏi mở" (Q-01…Q-04).
