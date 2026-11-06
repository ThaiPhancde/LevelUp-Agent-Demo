# Hướng dẫn cho agent — Level Up 13-Agent Demo

Nguồn gốc: prompt gốc tại `../DEMO_ONLY.md` (Phần C), khung phương pháp mượn từ dự án `D:\Purchasing System` (AGENTS.md + docs/decisions, implementation-status, handoff). Khi sửa quy tắc ở đây, cập nhật mục "Prompt nền" trong `docs/DEMO_PLAN.md` theo.

## Nguồn và thứ tự ưu tiên

1. `../DEMO_ONLY.md` — nguồn quyết định phạm vi (13 vai trò, 10 phase, quy tắc bắt buộc).
2. `docs/DEMO_DECISIONS.md` — quyết định đã chốt / mặc định tạm / câu hỏi mở; đè lên mặc định của bản thiết kế.
3. `docs/DEMO_PLAN.md` — thiết kế, bảng phase, prompt từng phase, checklist nghiệm thu.
4. `../level-up-os-full-summary.md` — bối cảnh Level Up OS (nguyên tắc kiến trúc, guardrail, 10 agent). Chỉ dùng để **mô phỏng** nguyên tắc; không phải phạm vi phải xây.

Không thêm chức năng ngoài phạm vi demo (production, tích hợp thật, agent thứ 14, cloud, Kubernetes). Không coi giả định là yêu cầu đã chốt.

## Prompt nền

Bạn hoàn thiện bản Demo 13 AI Agents theo `DEMO_ONLY.md` và `docs/DEMO_PLAN.md`. Chỉ thực hiện phase được chỉ định (hoặc phase kế tiếp theo `docs/DEMO_PHASE_STATUS.md` khi được giao "tiếp tục"). Không triển khai toàn bộ roadmap trong một lượt.

Trước khi làm: đọc `AGENTS.md`, `docs/DEMO_PHASE_STATUS.md`, `docs/DEMO_DECISIONS.md`, `docs/DEMO_HANDOFF.md`. Audit code thực tế (`app/`) trước khi thêm hoặc sửa. Không tự khẳng định chức năng có sẵn nếu chưa chạy kiểm tra. Không tự thay stack (FastAPI + SQLite + Docker Compose) hoặc viết lại dự án.

Quy trình mỗi phase:
1. Tóm tắt phạm vi, phần đã có, phần thiếu, file/module dự kiến thay đổi.
2. Triển khai theo một luồng chạy được: dữ liệu → engine/API → giao diện → kiểm thử. Phase quá lớn thì chia lát nhỏ, ghi checkpoint.
3. Kiểm tra rủi ro thực của phase: Mock Mode chạy không cần DeepSeek; engine deterministic không phụ thuộc LLM; không gọi API trả phí ngoài hạn mức; response rỗng phải thành FAILED; restart container không mất run.
4. Cập nhật `DEMO_PHASE_STATUS`, `DEMO_DECISIONS`, `DEMO_HANDOFF`, `DEMO_TEST_REPORT`, README khi cần: đã xong, đang dở, test đã chạy, lỗi còn lại, env mới, bước kế tiếp.
5. Dừng khi hoàn thành phase hoặc đạt checkpoint an toàn. Không tự nhảy phase khi phase hiện tại chưa PASS nghiệm thu. Gần hết context: ưu tiên lưu handoff.

Yêu cầu xuyên suốt (từ `DEMO_ONLY.md` Phần C):
- DEMO ONLY, chạy local. Không AWS/VPS, không PostgreSQL production, không Meta/Pancake/Shopify thật, không gửi tin nhắn thật, không quảng cáo thật, không thanh toán, không push GitHub.
- Mock Mode là mặc định. Unit/integration test chỉ dùng mock response.
- **Tối đa 2 lời gọi DeepSeek thật trong toàn bộ quá trình triển khai** cho đến khi được phê duyệt thêm; ghi mỗi lần vào `docs/DEMO_DECISIONS.md` mục "Sổ gọi LLM thật". Không lặp request trả phí.
- Giữ DeepSeek, model theo `.env` hiện có; không đổi provider. Không lộ API key trong log, báo cáo, git.
- Rules First, AI Second: QA/Audit/Monitoring Engine kiểm tra bằng code; LLM chỉ suy luận, lập kế hoạch, diễn giải. Số học quan trọng tính bằng Python.
- Agent không bịa dữ liệu thị trường hay số liệu; chỉ dùng dữ liệu từ Mock API, bàn giao qua artifact có schema.
- Mọi hành động WRITE ra "hệ thống ngoài" (publish, pay, send) phải đi qua Mock Tool Gateway và bị Audit Engine chặn/ghi log. Chiến dịch luôn `DRAFT`.
- Mọi hành động của agent ghi `decision_log` (ai, làm gì, đầu vào, đầu ra, token, thời gian, kết quả).
- Không tạo thêm agent ngoài 13 vai trò đã xác định.
- Lỗi hiển thị tiếng Việt: kiểm tra byte thực tế giữa API, SQLite, web trước khi sửa; không sửa dữ liệu nếu chỉ do PowerShell hiển thị (xem `DEMO_DECISIONS.md` M-04).

Kết thúc mỗi phase trả ngắn gọn: đã làm gì; cách chạy/test; kết quả test thực tế (PASS/FAIL kèm lệnh); phần chưa làm hoặc bị chặn; cách nghiệm thu; phase tiếp theo. Chỉ đánh dấu DONE khi tiêu chí nghiệm thu trong `DEMO_ONLY.md` của phase đó đã đạt và có bằng chứng chạy.

## Quy tắc riêng đã chốt (04/11/2026)

- Thư mục làm việc: `D:\LevelUp-Agent-Demo\levelup-agent-demo-vmm`. Tài liệu ở `docs/` của thư mục này (đường dẫn `docs/DEMO_*.md` trong `DEMO_ONLY.md` hiểu là ở đây).
- Docker Desktop (Docker VMM) đang chạy; cổng `127.0.0.1:8088`; dữ liệu ở named volume `demo_data`. Không bind mount thư mục Windows.
- Dữ liệu run cũ trong SQLite (bảng `events`) phải giữ được qua migration schema mới (M-06).
- Dashboard là văn phòng 3D (three.js copy vào `app/web/vendor/`) + chế độ 2D, HTML/JS tĩnh phục vụ từ FastAPI, không bước build (D-16, M-18). Đặc tả: `docs/DEMO_DASHBOARD_3D.md`.
- Phân công Claude 60 / Gemini 40 theo `docs/DEMO_AGENT_WORKFLOW.md` (D-15); Gemini chạy trong `D:\LevelUp-Agent-Demo\_gemini-work`, Claude nghiệm thu rồi mới copy về.
