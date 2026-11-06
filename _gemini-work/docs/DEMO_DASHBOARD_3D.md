# Thiết kế Dashboard "Văn phòng Level Up 3D" (Phase 6)

Phiên bản 1.0 — 05/11/2026. Yêu cầu người dùng (05/11/2026, D-16): hiển thị trực quan dạng **một phòng ban 3D** như ảnh tham khảo "thị trấn AI agent" (diorama isometric, mỗi agent một phòng, bong bóng lời thoại, thanh công cụ xoay/tên/bong bóng), không cần giống hệt, thiết kế lại theo nghiệp vụ bán hàng Level Up. Link TikTok tham khảo không đọc được nội dung, chỉ dựa vào ảnh chụp.

Nguồn chức năng tối thiểu vẫn là `DEMO_ONLY.md` Phase 6 (10 thành phần). 3D là **lớp trình bày** trên cùng REST API của Phase 3–5, không thay thế các bảng dữ liệu.

## 1. Ý tưởng

Một **tầng văn phòng isometric** nổi trên nền, chia khu theo phòng ban. Mỗi agent là một nhân vật low-poly ngồi trong phòng riêng. Khi workflow chạy, người xem thấy ai đang làm, việc gì, tài liệu chuyền từ phòng nào sang phòng nào, và chỗ nào bị chặn hoặc lỗi.

| Ảnh tham khảo | Bản Level Up |
|---|---|
| Lâu đài "Claude Code" ở giữa | **Phòng Chỉ huy** (Commander) ở trung tâm, tháp kính có bảng kế hoạch |
| Các nhà nhỏ: Nghiên cứu, Viết bài, Thiết kế… | 6 khu phòng ban theo nghiệp vụ (mục 2) |
| Bong bóng "Gấp gấp, sếp chờ duyệt!" | Bong bóng lấy từ trạng thái task và `decision_log` |
| Nhân vật đi mang "Video cần QC" | **Tài liệu bàn giao** bay theo cạnh dependency khi task COMPLETED |
| Thanh: Dừng xoay, Tên, Bong bóng, Toàn cảnh, Tổng quan, Tự chạy | Giữ nguyên ý (mục 4) |
| "7 agent", "1 bước đã…" | "13 agent", "Bước 6/14", trạng thái run |
| Chú thích dưới cùng | Chú thích 13 vai trò, màu theo khu |

## 2. Bố cục khu (lưới 5 × 5 ô, tâm là Commander)

| Khu | Agent | Đạo cụ gợi ý | Màu khu |
|---|---|---|---|
| Trung tâm — Phòng Chỉ huy | 01 Commander | Tháp kính, bảng kế hoạch 14 bước, chuông duyệt (HITL) | vàng |
| Thị trường & Sản phẩm | 02 Market Intelligence, 03 Product Scout | Bản đồ Philippines, kệ 3 sản phẩm LU-PH-001/002/003 | xanh dương |
| Chiến lược & Sáng tạo | 04 Offer & Strategy, 05 Content & Creative | Bảng giá, giá vẽ, máy ảnh | tím |
| Quảng cáo | 06 Campaign Operator | Màn hình chiến dịch có nhãn **DRAFT** | cam |
| Bán hàng & CSKH | 07 Lead & Sales, 08 Customer Success | Điện thoại, hộp hàng, xe giao hàng mock | xanh lá |
| Phân tích & Tài chính | 09 Sales Analyst, 10 Finance & Risk | Biểu đồ cột, két sắt | xanh ngọc |
| Phòng Giám sát (kính) | 11 QA Tester, 12 Auditor, 13 Monitor | 3 bàn điều khiển = 3 Engine, đèn PASS/FAIL | đỏ nhạt |
| Rìa bản đồ — Cổng Mock | (không phải agent) | Cổng "Mock Tool Gateway" có rào chắn; nhà Meta Ads mock, POS mock, 3PL mock | xám |

Băng **"MOCK ONLY — dữ liệu giả lập"** luôn hiện ở góc trên.

## 3. Trạng thái → hình ảnh

| Trạng thái task | Nhân vật | Phòng | Bong bóng |
|---|---|---|---|
| PENDING | ngồi yên, xám nhạt | đèn tắt | ẩn hoặc "Chờ …" (tên dependency còn thiếu) |
| RUNNING | nhún/gõ phím, viền sáng | đèn bật, nhấp nháy nhẹ | việc đang làm, ví dụ "Đang phân tích thị trường PH" |
| COMPLETED | dấu ✓ xanh trên đầu | đèn xanh | tóm tắt artifact 1 dòng, tự ẩn sau vài giây |
| FAILED | dấu ! đỏ, khói nhỏ | đèn đỏ | lỗi rút gọn, ví dụ "Timeout sau 30s" + nút Retry khi mở chi tiết |
| SKIPPED | mờ 50% | đèn tắt | "Bỏ qua: chờ kpi lỗi" |
| CANCELLED | mờ, gạch chéo | đèn tắt | "Đã hủy" |

Sự kiện đặc biệt:
- **Bàn giao:** khi task X COMPLETED, một tờ tài liệu bay theo đường cong từ phòng X tới phòng từng task phụ thuộc vào X (từ `GRAPH`).
- **Audit chặn publish (Phase 5):** rào chắn ở Cổng Mock hạ xuống đỏ, bong bóng Auditor "Chặn publish thật — giữ DRAFT".
- **QA FAIL:** đèn bàn QA đỏ, đường đỏ nối tới phòng có số sai.
- **WAITING_APPROVAL:** chuông ở Phòng Chỉ huy rung, bong bóng "Chờ người duyệt", nút Duyệt/Từ chối nổi ở bảng bên.

Văn bản bong bóng lấy theo thứ tự: lỗi task → `summary` của artifact → nhãn mặc định theo agent. Không gọi LLM để sinh bong bóng.

## 4. Thanh công cụ và bảng điều khiển

Thanh trên (giống ảnh): **Tự xoay/Dừng xoay** · **Tên** (bật/tắt nhãn) · **Bong bóng** (bật/tắt) · **Toàn cảnh** (camera về góc mặc định) · **Tổng quan** (chuyển sang chế độ 2D) · **Start Demo ▶**. Góc phải: "13 agent", "Bước n/14", trạng thái run có màu.

Ô nhập objective + chọn **Mock** (mặc định) / **DeepSeek** (cảnh báo chi phí, hiện số lời gọi còn lại theo D-06) + chọn lỗi giả lập (5 loại Phase 5).

Bấm vào phòng hoặc nhân vật → **ngăn kéo bên phải**: input (artifact upstream), output (artifact + narrative), lỗi, số lần thử, thời gian, nút **Retry** (khi FAILED).

Bảng dưới có tab: **Kết quả cuối** (Final Summary của Commander) · **QA / Audit / Monitor** · **Token & chi phí** · **Nhật ký** (`decision_log`) · **Lịch sử run** (xem lại run cũ = replay, không gọi LLM) · nút **Cancel**.

Chế độ **Tổng quan 2D**: đồ thị dependency 14 nút (SVG) + bảng trạng thái. Đây cũng là chế độ dự phòng khi máy không có WebGL và khi `prefers-reduced-motion` bật.

## 5. Kỹ thuật

| Mục | Lựa chọn | Lý do |
|---|---|---|
| Thư viện 3D | **three.js** bản cố định, copy file vào `app/web/vendor/` (ES module, không bước build) | Chạy offline, không phụ thuộc CDN khi trình diễn; một file JS, không bundler (M-18) |
| Nhãn, bong bóng | `CSS2DRenderer` của three.js (HTML thật đè lên 3D) | Chữ tiếng Việt sắc nét, đọc được bằng trình đọc màn hình |
| Camera | `OrbitControls`, giới hạn góc nghiêng, tự xoay chậm | Như ảnh; người xem kéo xoay được |
| Mô hình | Dựng bằng khối cơ bản (box, cylinder, sphere) trong code, không tải GLTF ngoài | Không lo bản quyền tài sản, nhẹ |
| Dữ liệu | Polling `GET /runs/{id}` mỗi 1 s khi run đang chạy, dừng khi kết thúc | Dùng nguyên API Phase 3, không cần WebSocket |
| Cấu trúc file | `app/web/dashboard.html` (khung + panel), `app/web/office3d.js` (scene), `app/web/office-layout.js` (vị trí phòng, màu, đạo cụ — dữ liệu thuần), `app/web/panels.js` (ngăn kéo, tab, 2D) | Tách để chia việc Claude/Gemini, không hai bên sửa cùng file |
| Hiệu năng | ≤ 60 FPS trên laptop văn phòng; tổng số mesh < 1.500; tắt bóng đổ mềm nếu FPS < 30 | Máy demo phổ thông |
| Truy cập | Mọi thông tin 3D đều có ở chế độ 2D/bảng; nút có nhãn; màu kèm biểu tượng (✓ ! ⏸) | Không chỉ dựa vào màu |

## 6. Chia việc Claude 60 / Gemini 40 (Phase 6)

| Claude | Gemini 4 Argon |
|---|---|
| `office3d.js`: scene, camera, ánh sáng, vòng render, ánh xạ trạng thái → hình, animation bàn giao theo `GRAPH`, polling | `office-layout.js`: đạo cụ trang trí từng khu theo bảng mục 2 (theo schema Claude định nghĩa) |
| Hợp đồng dữ liệu giữa scene và panel (sự kiện `select-task`, `run-updated`) | `panels.js` + phần lớn `dashboard.html`: thanh công cụ, ngăn kéo, tab, chế độ 2D, chữ tiếng Việt |
| Nút Retry/Cancel/Approve gọi API, xử lý lỗi | Kịch bản Playwright chụp 4 trạng thái (đang chạy, lỗi, bị chặn, hoàn tất) theo kịch bản Claude viết |
| Nghiệm thu: chạy thật trên trình duyệt, đo FPS, kiểm chế độ 2D | — |

## 7. Nghiệm thu bổ sung cho Phase 6

1. Mở `/dashboard` không cần Internet (three.js nằm trong `app/web/vendor/`).
2. Bấm Start Demo ở Mock Mode: 13 nhân vật lần lượt đổi trạng thái đúng thứ tự `GRAPH`, có ít nhất 13 lần tài liệu bay bàn giao.
3. Bấm vào một phòng: thấy input/output đúng artifact trong API.
4. Inject `timeout:market`: phòng Market đỏ, các phòng sau mờ (SKIPPED), Retry trong ngăn kéo chạy lại đúng task.
5. Nút Tên/Bong bóng/Tự xoay/Toàn cảnh/Tổng quan hoạt động; Tổng quan hiện đồ thị 2D + bảng.
6. Tắt WebGL (hoặc `?mode=2d`): dashboard vẫn dùng được đủ 10 thành phần DEMO_ONLY.
7. FPS ≥ 30 khi tự xoay trên máy demo (ghi số đo vào `DEMO_TEST_REPORT.md`).
