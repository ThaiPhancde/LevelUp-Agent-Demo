# Quyết định

Mã `D-nn` = đã chốt bởi người dùng/DEMO_ONLY; `M-nn` = **mặc định tạm** do Claude đặt, người dùng có thể đè; `Q-nn` = **câu hỏi mở**. Khi một `M`/`Q` được chốt, đổi sang `D` và ghi ngày.

## Đã chốt

| Mã | Quyết định | Nguồn |
|---|---|---|
| D-01 | DEMO ONLY, chạy local. Không production, cloud, VPS, K8s, PostgreSQL, tích hợp thật, thanh toán, quảng cáo thật, tin nhắn thật. | DEMO_ONLY C |
| D-02 | Stack giữ nguyên: Python FastAPI + SQLite + Docker Compose, một container. Không tự đổi stack. | DEMO_ONLY, AGENTS |
| D-03 | Đúng 13 vai trò (10 business + QA Tester, Auditor, Monitor). Không thêm agent. | DEMO_ONLY A.1 |
| D-04 | 3 Engine (QA, Audit, Monitoring) deterministic, độc lập LLM; supervisor chỉ diễn giải kết quả engine. | DEMO_ONLY A.1 |
| D-05 | Mock Mode là mặc định. Test chỉ dùng mock response. | DEMO_ONLY C |
| D-06 | Tối đa **2** lời gọi DeepSeek thật trong toàn bộ triển khai cho đến khi được duyệt thêm. Ghi sổ ở mục cuối file. | DEMO_ONLY C |
| D-07 | Giữ DeepSeek, không đổi provider; model theo `.env` hiện có (`deepseek-v4-flash`). `DEMO_ONLY` ghi `deepseek-flash` được hiểu là cùng model này; không tự đổi tên. | DEMO_ONLY, `.env` |
| D-08 | Trạng thái task: `PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED`. Trạng thái phase: `NOT_STARTED, IN_PROGRESS, DONE, PARTIAL, BLOCKED`. | DEMO_ONLY P3, C |
| D-09 | Dashboard tại `http://localhost:8088/dashboard`, Mock Mode mặc định. | DEMO_ONLY P6 |
| D-10 | Dữ liệu kịch bản Philippines cố định: LU-PH-001, 499/180/75/18 PHP, ngân sách 15.000, DRAFT 4.000, tồn 50, leads 100/20/15/2. | DEMO_ONLY P2 |
| D-11 | ARIS chỉ đánh giá; không bắt buộc chuyển 13 agent sang ARIS; luôn có fallback runtime nội bộ. | DEMO_ONLY P7 |
| D-12 | Không tự push GitHub. Không commit khi chưa được yêu cầu (thư mục hiện chưa có `.git`). | DEMO_ONLY C |
| D-13 | ~~Phân công Claude 100 / Gemini (Antigravity) 0 cho đến khi người dùng đổi; cấu trúc giao việc giữ sẵn theo mẫu CRM2 (`DEMO_AGENT_WORKFLOW.md`). Lý do: Gemini hết token (người dùng, 04/11/2026).~~ Thay bằng D-15. | người dùng 04/11 |
| D-14 | Phương pháp tài liệu theo `D:\Purchasing System` và `D:\CRM2`: AGENTS.md prompt nền, decisions/status/handoff, biên bản nghiệm thu từng phase. | người dùng 04/11 |
| D-16 | Dashboard Phase 6 trực quan chính là **văn phòng 3D isometric** theo ảnh tham khảo, thiết kế lại theo nghiệp vụ; đặc tả `DEMO_DASHBOARD_3D.md`. | người dùng 05/11 |
| D-15 | **Phân công Claude 60 / Gemini 4 Argon 40** tính trên cả dự án, quy trình theo `DEMO_AGENT_WORKFLOW.md`. Thay D-13. | người dùng 05/11 |

## Mặc định tạm (Claude đặt, cần người dùng xác nhận hoặc đè)

| Mã | Mặc định | Lý do / cách đổi |
|---|---|---|
| M-01 | Thứ tự thực hiện phase: 0→1→2→3→4→5→6→8→7→9 (ARIS sau E2E). | DEMO_ONLY ưu tiên P0–P6; P7 không chặn demo. Đổi: sửa `DEMO_PLAN.md` mục 6. |
| M-02 | Cấu trúc `app/` chia `core/ agents/ engines/ mock/ llm/ web/`; giữ `app/main.py` làm entry để Dockerfile không đổi. | Modular monolith, Dockerfile giữ nguyên. |
| M-03 | Trạng thái run: `PENDING, RUNNING, WAITING_APPROVAL, COMPLETED, FAILED, CANCELLED` (tách với trạng thái task). | DEMO_ONLY chỉ quy định trạng thái task; HITL cần trạng thái chờ ở cấp run. |
| M-04 | Mojibake trong `../result.json` coi là lỗi ghi/hiển thị của PowerShell (API và SQLite trả UTF-8 đúng khi probe 04/11). Không sửa dữ liệu; Phase 1 thêm test byte UTF-8 qua API→SQLite→response để chốt. Nếu test phát hiện byte sai trong code thì mới sửa code. | DEMO_ONLY P1: "không sửa dữ liệu gốc khi vấn đề chỉ nằm ở cách PowerShell hiển thị". |
| M-05 | Guardrail HITL: chiến dịch có ngân sách ≥ `APPROVAL_THRESHOLD_PHP` (mặc định 5.000) → run `WAITING_APPROVAL`, duyệt trên dashboard. Chiến dịch mẫu 4.000 chạy thẳng. Mọi `WRITE_EXTERNAL` bị chặn vô điều kiện. | Mô phỏng ngưỡng 2.000.000 VNĐ của Level Up OS theo đơn vị demo PHP; cấu hình env. |
| M-06 | Giữ bảng `events` và dữ liệu run cũ; schema mới thêm bảng, không xóa. Migration = `CREATE TABLE IF NOT EXISTS` + `schema_version`. Reset chỉ qua `POST /admin/reset-demo {confirm:true}` hoặc `docker compose down -v` khi người dùng xác nhận. | DEMO_ONLY P0 "giữ nguyên dữ liệu". |
| M-07 | Hạn mức LLM: `LLM_RUN_TOKEN_BUDGET=20000` token/run, `max_tokens=2000`/lượt, timeout 60 s, retry 3 lần backoff 1-2-4 s. Vượt ngân sách → các task còn lại chạy mock + Monitoring WARN. | DEMO_ONLY P1, P4. |
| M-08 | Chi phí ước tính ghi theo bảng giá cấu hình env `LLM_PRICE_IN_PER_M`, `LLM_PRICE_OUT_PER_M` (USD/1M token), mặc định 0 nếu không đặt — không bịa giá. | Không lấy giá từ trí nhớ. |
| M-09 | ~~Dashboard một file HTML + vanilla JS~~ Thay bằng M-18 (05/11). Vẫn giữ: không framework, không bước build, polling 1 s. | — |
| M-10 | Fixture thêm LU-PH-002, LU-PH-003 (sản phẩm mô phỏng, giá/vốn khác) để Product Scout so sánh thật; tất cả `synthetic: true`. | DEMO_ONLY P2 cho phép. |
| M-11 | Error injection qua `inject: ["bad_cost","timeout:<agent_id>","missing_field:<agent_id>","publish_attempt","empty_response:<agent_id>"]`; `inject_error=true` cũ ánh xạ sang `bad_cost`. | DEMO_ONLY P5, giữ tương thích. |
| M-12 | Workflow chạy task tuần tự theo topo order (không song song) để tránh ghi SQLite đồng thời. | Demo không cần song song; đơn giản hơn. |
| M-13 | Test chạy bằng `pytest` trong container (`docker compose exec demo pytest`); thêm `pytest`, `pytest-asyncio` vào `requirements-dev.txt` hoặc requirements chính (Phase 0/1 quyết định theo kích cỡ image). | Không cần Python host. |
| M-14 | Biên bản nghiệm thu từng phase ghi vào `DEMO_TEST_REPORT.md` theo bảng Tiêu chí / Bằng chứng / Kết quả (mẫu CRM2 `docs/acceptance/`), không tách file riêng. | DEMO_ONLY chỉ yêu cầu 6 file docs. |
| M-18 | 3D dùng **three.js bản cố định copy vào `app/web/vendor/`** (ES module, không bundler, không CDN lúc chạy), nhân vật/phòng dựng từ khối cơ bản, nhãn bằng `CSS2DRenderer`; chế độ 2D SVG khi không có WebGL hoặc `prefers-reduced-motion`. | Giống ảnh cần 3D thật (CSS 3D khó làm nhân vật, ánh sáng); offline khi trình diễn. Đổi: chấp nhận CDN thì bỏ thư mục vendor. |
| M-19 | Product Scout chọn SKU **có dữ liệu bán thử** (có mock campaign) vì toàn bộ số phễu thuộc SKU đó; biên < 30% thì gắn cảnh báo chứ không đổi SKU. Không SKU nào có dữ liệu → biên cao nhất đạt ngưỡng → biên cao nhất. | Nếu đổi SKU khi giá vốn bị inject 9.999, KPI ghép giá SKU mới với phễu SKU cũ và số sai biến mất khỏi chuỗi, QA khó bắt. |
| M-20 | Commander kết luận: `NEEDS_REVIEW` (giám sát có phát hiện) · `HOLD_DRAFT` (giám sát PASS nhưng Finance rủi ro HIGH, ví dụ kịch bản mẫu lỗ 1.062 PHP sau quảng cáo) · `DRAFT_READY` (bản nháp sẵn sàng để người duyệt). | Không kết luận "sẵn sàng" khi kế hoạch đang lỗ. |
| M-21 | Artifact sai schema bị từ chối ngay lúc bàn giao: task FAILED, artifact vẫn lưu với `valid=0` làm bằng chứng, không chuyển cho agent sau. | Agent sau không bao giờ nhận dữ liệu thiếu trường. |
| M-22 | Commander (bước tổng kết) và 3 agent giám sát đọc **mọi artifact đã COMPLETED** của run (quyền SUPERVISE), không chỉ dependency trực tiếp; số trong Final Summary chép từ agent đã tính, không tính lại. | Đồ thị giữ nguyên, tổng kết vẫn đủ số Offer/KPI/Finance. |
| M-23 | Phase 4: QA Tester chỉ kiểm schema, Auditor kiểm quyền hành động theo registry, Monitor đọc trạng thái/lần thử/LLM. Kiểm phép tính, chặn WRITE thật và error injection làm ở Phase 5 bằng 3 Engine. | Đúng ranh giới Phase 4/5 của DEMO_ONLY. |
| M-24 | **Phụ thuộc mềm:** QA, Audit, Monitor và Commander tổng kết chạy khi mọi dependency đã kết thúc (COMPLETED/FAILED/SKIPPED), không chờ COMPLETED. Retry một agent nghiệp vụ chạy lại các task mềm đó (ngoại lệ duy nhất của máy trạng thái: COMPLETED→PENDING cho task mềm). | Nếu giữ phụ thuộc cứng, agent lỗi làm cả 3 giám sát bị SKIPPED và Monitor không thể báo timeout. |
| M-25 | Lỗi giả lập `timeout`, `missing_field`, `empty_response` chỉ áp ở **lần thử đầu**; retry cùng agent sẽ thành công. `bad_cost`, `publish_attempt` áp mọi lần. | Kịch bản S4: retry đúng agent lỗi phải sửa được. |
| M-26 | Timeout mỗi task: Mock `TASK_TIMEOUT_S` = 5 s, LLM `LLM_TASK_TIMEOUT_S` = 200 s (DeepSeek 60 s × 3 lần thử). | Mock chạy mili-giây; demo timeout không bắt người xem chờ 30 s. |
| M-27 | Audit chặn `WRITE_EXTERNAL` tại gateway: hành động không thực thi, ghi `decision_log allowed=0`, Audit Engine FAIL (`blocked_action`), Commander `NEEDS_REVIEW`. Task của agent vẫn COMPLETED (agent không hỏng, chỉ hành động bị chặn). | Phân biệt "agent lỗi" với "hành động bị guardrail chặn". |
| M-28 | QA Engine so giá vốn với **dữ liệu tham chiếu sạch** (`facts_for([])`), tính lại công thức trong tolerance 0,01, kiểm nhất quán SKU/biên/ngân sách giữa artifact; số trong lời diễn giải không có trong artifact chỉ là WARN. | LLM có thể làm tròn khi viết; số chuẩn luôn nằm trong artifact. |
| M-29 | HITL: hành động `WRITE_DRAFT` có `budget_php` ≥ `APPROVAL_THRESHOLD_PHP` (mặc định 5.000) được gateway giữ lại; run kết thúc `WAITING_APPROVAL`; `POST /runs/{id}/approvals/{aid}` duyệt/từ chối; hủy run tự từ chối các yêu cầu đang chờ. Duyệt chỉ đổi trạng thái bản nháp mock, không publish. | Thực hiện M-05. |
| M-30 | Mock Mode chạy chậm có chủ đích `MOCK_STEP_DELAY_S` = 0,8 s mỗi task (task hiện RUNNING trong lúc chờ) để người xem theo dõi bàn giao trên dashboard; test và script đặt 0. LLM Mode không thêm trễ. | Mock xong trong mili-giây, lần polling đầu đã thấy kết quả cuối. |
| M-31 | Commander chỉ kết luận `NEEDS_REVIEW` khi một engine **FAIL** hoặc không chạy; WARN (ví dụ "retried" sau khi Retry thành công, hoặc "pending_approval") được ghi nhận nhưng không chặn. | Retry thành công không nên bị coi là lỗi. |
| M-32 | Cảnh 3D tự chèn CSS cho nhãn/bong bóng của nó; `office-props.js` là tùy chọn (thiếu file vẫn chạy); bong bóng chỉ hiện cho RUNNING, FAILED, vừa COMPLETED (7 s) và cảnh báo (duyệt, QA FAIL, cổng chặn). `window.__officeFps` để đo FPS. | Không phụ thuộc file của Gemini; giảm rối mắt. |
| M-33 | Phase 7 làm trước Phase 8 theo yêu cầu người dùng (05/11), đổi thứ tự M-01. ARIS chỉ được dùng ở phần `dispatch`/`planCards` qua adapter thử; runtime chính và dự phòng là runtime nội bộ. | Commander của ARIS là LLM, vượt hạn mức D-06; ARIS đã ngừng phát triển. |
| M-34 | Dashboard nói tiếng nghiệp vụ: mọi mã kỹ thuật (trạng thái, tên bước, mã quy tắc, tên tình huống thử, UUID) đi qua từ điển `app/web/labels.js`; mã gốc chỉ nằm ở tooltip, thuộc tính `data-*` và mục "Chi tiết kỹ thuật". Lượt chạy gọi là "Lượt #n" (số lấy từ `rowid`, API trả `seq`, `/runs` kèm `inject`). | Người dùng nghiệp vụ không đọc `bad_cost` hay UUID (người dùng, 05/11). |
| M-35 | Bố cục khóa theo khung nhìn: `#app` cố định, trang không bao giờ cuộn, mỗi panel tự cuộn bên trong; thanh dưới kéo giãn được (tay nắm, phím mũi tên, nhấp đúp để về mặc định), thu gọn được, nhớ kích thước trong `localStorage`. | Phóng to trình duyệt làm panel xếp chồng, trang cuộn và thanh trên cùng trôi mất (người dùng báo 05/11). |
| M-36 | File tĩnh `/static/*` trả `Cache-Control: no-cache` (trình duyệt luôn kiểm tra lại, 304 nếu không đổi). | Sau mỗi lần cập nhật, trình duyệt đã chạy CSS/JS cũ trong bộ nhớ đệm. |
| M-37 | Các lượt chạy lỗi giả lập ("Thử: …") là dữ liệu chủ ý, không phải lỗi hệ thống; giao diện ghi rõ tình huống ở cột "Tình huống". | Người dùng hỏi vì sao có 3 lượt "FAILED" (05/11): đó là các lượt thử `missing_field`, `empty_response`. |
| M-15 | Gemini chạy trong bản sao có git `D:\LevelUp-Agent-Demo\_gemini-work` (không `.env`, không `data/`); repo chính vẫn không init git (D-12). Claude tự copy file đã nghiệm thu về repo chính. | Runner cần `git status` để bắt ghi sai chỗ. Đổi: người dùng cho phép `git init` repo chính thì dùng worktree như CRM2. |
| M-16 | Phase 3: task dừng vì container restart chuyển FAILED "interrupted", chờ người bấm Retry. Run chưa xong task nào (hoặc dừng giữa hai task) tự chạy tiếp khi khởi động. | Không tự gọi lại agent đang dở, tránh trả tiền LLM hai lần. |
| M-17 | Phase 3: cancel không ngắt task đang RUNNING; task đó chạy xong, các task còn lại chuyển CANCELLED. | Agent đơn luồng, ngắt giữa chừng có thể để artifact dở. |

## Câu hỏi mở

| Mã | Câu hỏi | Mặc định đang dùng |
|---|---|---|
| Q-01 | Có cho phép dùng 1 trong 2 lời gọi DeepSeek thật ở Phase 1 để kiểm client, hay giữ cả 2 cho Phase 8/9 trình diễn? | Giữ cả 2 đến khi người dùng chỉ định. |
| Q-02 | Ngưỡng HITL M-05 (5.000 PHP) có đúng ý, hay muốn mô phỏng đúng 2.000.000 VNĐ với tỷ giá giả lập? | 5.000 PHP. |
| Q-03 | ~~Khi nào mở lại Gemini và tỷ lệ bao nhiêu?~~ Đã chốt D-15 (60/40, 05/11). | — |
| Q-04 | Ngôn ngữ giao diện dashboard: tiếng Việt (như Purchasing/CRM2) hay song ngữ? | Tiếng Việt, nhãn kỹ thuật giữ tiếng Anh (DRAFT, PASS/FAIL). |

## Sổ gọi LLM thật (D-06)

| # | Ngày | Phase | Mục đích | Token in/out | Kết quả |
|---|---|---|---|---|---|
| 1 | 05/11/2026 | 9 | Kiểm tra API thật tối thiểu (DEMO_ONLY P1): 1 lời gọi trực tiếp `deepseek.complete`, `run_id=phase9-real-check` | 122 / 267 | COMPLETED, `finish_reason=stop`, 2,2 s; API báo model `deepseek-flash` (cấu hình `deepseek-v4-flash`); trả lời tiếng Việt đúng, không đổi số |

Ghi chú: 5 run có trong SQLite trước 04/11 (127 event) do người dùng chạy trước khi bắt đầu đợt này; ít nhất một run dùng LLM thật (nội dung tiếng Việt trong `result.json`). Không tính vào hạn mức 2 lần.

## Phương án A — A0 (06/11/2026)

Người dùng yêu cầu triển khai A0. OA-D01..OA-D13 dùng **mặc định**, chưa có câu trả lời riêng; theo mục 17.1, câu chưa trả lời dùng mặc định. Các mục dưới là hợp đồng cho phase sau, chưa phải tính năng hiện có.

### OA-D và OA-M
Câu nào chưa trả lời thì dùng giá trị mặc định ghi trong bảng.

| Mã | Câu hỏi | Mặc định |
|---|---|---|
| OA-D01 | `bad_cost` nghĩa là gì khi làm lại và khi học? | Báo giá nhà cung cấp cũ hoặc sai. `verify_supplier_cost` đọc lại báo giá mock "mới" (giá trong fixtures, 180). Khi do ký ức áp, thay đổi luôn hiện WARN `memory_override` |
| OA-D02 | Dashboard bật mặc định những gì? | `max_rework=2`, `rooms=true`, `use_memory=true` (giá trị khởi tạo của form). API vẫn 0 / false / false. Test trình duyệt cũ chạy với 0 / false / false |
| OA-D03 | Phòng `risk` có hiện ở mọi run mặc định trên dashboard (finance HIGH)? | Có, khi `rooms=true`, một lần mỗi run |
| OA-D04 | Ngưỡng học | `LEARN_MIN_RUNS=2`, `LEARN_WINDOW_RUNS=10`; 1 lần sửa thành công cho `check`; 1 lần từ chối cho S3; `PROPOSAL_TTL_RUNS=10`; `MEMORY_MAX_PER_AGENT=10`; tối đa 3 đề xuất mỗi lượt |
| OA-D05 | `reset-demo` có xóa ký ức và đề xuất? | Không, trừ khi `include_memory: true`. Reset thường đẩy đề xuất đang mở sang EXPIRED |
| OA-D06 | Có cho duyệt đề xuất phát lại không đạt? | Không bao giờ; chỉ từ chối |
| OA-D07 | Kênh mock mô phỏng đầu tiên? | Telegram (Zalo không có nút trong tin) |
| OA-D08 | Lưu dữ liệu adapter thế nào? | Bảng riêng có kiểu cho từng adapter (`channel_inbox`, `channel_outbox`, `brain_inbox`). `external_jobs` để đến khi có driver thật |
| OA-D09 | Dùng lời gọi DeepSeek thật cuối cùng thế nào? | Không dùng trong phương án A |
| OA-D10 | Agent có đọc Second Brain trong luồng run? | Không; chỉ API (góc nhìn chủ dự án) và test |
| OA-D11 | Thêm nút "trả về làm lại" thủ công (HITL)? | Không |
| OA-D12 | Thêm inject `delegate_attempt` để trình diễn bot ngoài bị BLOCK? | Không; test gọi gateway trực tiếp |
| OA-D13 | Ai được duyệt ký ức? | Chỉ con người: web hoặc thẻ mock với quyền owner (theo `ROLES`). Không có route thêm ký ức tay; test gọi `memory.activate()` trực tiếp |

| OA-D14 | Định danh người duyệt/dừng/mở lại (A3, chốt 25/11/2026) | Token riêng mỗi người (`Authorization: Bearer`), cấu hình `AUTH_OWNER` / `AUTH_DELEGATES` / `AUTH_MAX_DELEGATES=3`; server suy ra tên, chỉ lưu tên. Không cấu hình = không ai thao tác được |
| OA-D15 | Tạo run mới khi đang dừng khẩn (A3, chốt 25/11/2026) | Từ chối 409. Run đang chạy: không giao task mới, task chờ giữ PENDING, mở lại thì chạy tiếp |

| OA-D16 | Giao diện của vòng làm lại (A4, chốt 25/11/2026) | Lùi sang A9 như A1: 3D tài liệu đỏ + bong bóng "Làm lại: <luật>" + dấu tích, ô `max_rework` (mặc định 2 theo OA-D02). A4 chỉ trả dữ liệu qua `GET /runs/{id}` |
| OA-D17 | Giá chuẩn khi `verify_supplier_cost` (A4, 25/11/2026) | Dùng `data.facts_for((), objective)` — cùng nguồn QA so — thay vì `fixture('suppliers')`, để mục tiêu tùy chỉnh không bị sửa về giá mặc định |

### 17.2 Mặc định kỹ thuật (OA-M), ràng buộc với agent lập trình

| Mã | Mặc định |
|---|---|
| OA-M01 | `max_rework` 0..`MAX_REWORK_CEILING=2`, mặc định 0; `rooms` và `use_memory` mặc định false; ngoài miền hoặc trường lạ trả 422 |
| OA-M02 | Không sửa `TRANSITIONS`. Làm lại task nghiệp vụ chỉ qua `can_rework` + `_move(rework=True)`; task mềm qua `can_rerun`. `retry()` / `retry_plan()` giữ nguyên. Móc làm lại ở điểm `'monitor'` |
| OA-M03 | Gateway luôn `check_action` trước. Chỉ dùng lại khi trùng `(run_id, task_key, tool, target, action_hash)` và phán quyết. Dòng dùng lại chép đủ `detail` + `reused`, `attempt`. `tool_calls()` lọc theo lần thử. Gateway ghi `approvals.tool` |
| OA-M04 | Phần sửa chỉ từ phát hiện của `rework_plan` + `FIX`; lời thoại phòng chỉ để xem |
| OA-M05 | `checks` thuần, từ vựng đóng, có cờ `learnable`. Phép kiểm cấp facts áp cho mọi task của run và ghi before/after. `drop_blocked_action` chỉ dùng khi làm lại. Agent trả dữ liệu, `workflow` ghi log |
| OA-M06 | `learning.after_run` gọi ở `_finish` (COMPLETED/FAILED, không còn PENDING), `decide_approval` (không còn PENDING, bất kể trạng thái) và `recover()`. Mỗi `(run_id, learn_seq)` một lượt. Chiếm chỗ, làm việc, ghi lỗi ở ba tx riêng |
| OA-M07 | Phát lại chỉ đọc, gọi tường minh qua API, mô phỏng tool bằng `audit.check_action` trên hành động của chính lần chạy, tính `decision` bằng `business.summary`. Lưu `active_hash`; phát lại cũ không duyệt được; REPLAYED_FAIL không duyệt được |
| OA-M08 | `learn.py` chỉ stdlib. `DENY` là token so trên `key` và nội dung. Tập `learnable_checks` truyền vào làm tham số |
| OA-M09 | Ghim ký ức bằng `runs.memory_ids`, chỉ khi `use_memory` và `MEMORY_READ=1`. Mỗi `key` tối đa một bản ACTIVE (chỉ mục một phần). Mọi lần ghi qua `memory.activate()` với `BEGIN IMMEDIATE`; `IntegrityError` trả 409 |
| OA-M10 | Hết hạn đề xuất đếm theo `learning_meta.run_seq`, không theo ngày; reset không xóa bộ đếm |
| OA-M11 | Chống trùng theo `key` chính xác; không Jaccard, không độ tin cậy số thực |
| OA-M12 | Chữ phòng và bài học luôn từ mẫu ở phương án A; `speak` là chỗ cắm cho sau này |
| OA-M13 | Mọi task trong `rework_plan.changes` ép narrative mock |
| OA-M14 | Adapter chỉ mock. `assert_mock_mode()` trong `lifespan()`. AST cấm import mạng / subprocess. Adapter chỉ ghi DB qua gateway |
| OA-M15 | Nội dung ngoài `trust='external'` không thành `check` / `core`, không là chỉ thị. Danh tính mock là tự khai |
| OA-M16 | `get_run` chỉ thêm tóm tắt (≤ 2 KB): `rework`, `rooms_summary`, `tasks[].last_dispatch`, `tasks[].memory_used`. Tab tải khi mở. WAL không bật nếu chưa kiểm trên volume |
| OA-M17 | Gemini không sửa `app/core/*`, `app/engines/*`, `app/agents/*`, `app/adapters/*`, `app/db.py`; không viết phần phán xét; không giữ dữ liệu phân quyền. Claude review mọi sản phẩm |
| OA-M18 | Env mặc định trong code: `MEMORY_READ=0`, `LEARNING_ENABLED=0`, `REVIEW_CHANNEL=off`. `compose.yaml` bật hai cờ đầu cho trình diễn. `conftest.py` tắt cả ba. Test bật cờ thì dùng fixture `clean_memory` |

