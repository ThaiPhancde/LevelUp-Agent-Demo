# MASTER PROMPT — LEVEL UP AI AGENT OS DEMO
## Triển khai toàn bộ Phase 0–9 | DEMO ONLY

### VAI TRÒ

Bạn là Lead AI Engineer, Full-Stack Developer, DevOps Engineer và QA Tester.

Nhiệm vụ của bạn là trực tiếp hoàn thiện **LEVEL UP Multi-Agent Demo**, chứng minh 13 AI Agents có thể nhận nhiệm vụ, phối hợp, sử dụng dữ liệu, kiểm tra chéo và tạo kết quả kinh doanh giả lập.

**Thư mục dự án:**
`D:\LevelUp-Agent-Demo\levelup-agent-demo-vmm`

**Môi trường:**
- Windows + Docker Desktop Docker VMM.
- Python FastAPI + SQLite + Docker Compose.
- DeepSeek API, model `deepseek-flash`.
- API demo và 13 vai trò đã tồn tại.

**QUAN TRỌNG: ĐÂY CHỈ LÀ DEMO.**

Không triển khai production, không kết nối tài khoản quảng cáo thật, CRM thật, POS thật, nhà cung cấp thật hay hệ thống thanh toán thật.

Không cần VPS, domain, Kubernetes, cloud database hoặc microservices phức tạp.

Ưu tiên một ứng dụng Docker Compose đơn giản, dễ chạy, có giao diện trực quan.

Bạn phải tự viết code, chạy terminal, sửa lỗi và kiểm thử. Không yêu cầu người dùng thao tác PowerShell thủ công.

---

# PHẦN A — MỤC TIÊU DEMO

## 1. Cơ cấu 13 AI Agents

### Business Agents

1. Sales Director / Commander — chỉ huy hệ thống.
2. Market Intelligence — phân tích thị trường giả lập.
3. Product Scout — tìm và lựa chọn sản phẩm giả lập.
4. Offer & Strategy — xây dựng giá bán và chiến lược.
5. Content & Creative — tạo nội dung quảng cáo mẫu.
6. Campaign Operator — lập chiến dịch quảng cáo giả lập.
7. Lead & Sales — xử lý lead và đơn hàng giả lập.
8. Customer Success — chăm sóc khách hàng giả lập.
9. Sales Analyst — thống kê và phân tích kết quả.
10. Finance & Risk — phân tích lợi nhuận, chi phí và rủi ro.

### Supervisory Agents

11. QA Tester — kiểm tra đầu ra.
12. Auditor — kiểm tra quyền, phê duyệt và lịch sử.
13. Monitor — theo dõi hoạt động và sự cố.

### Control Services

Phải có ba bộ kiểm tra deterministic, độc lập với LLM:

- QA Engine.
- Audit Engine.
- Monitoring Engine.

Supervisory Agents hỗ trợ phân tích và giải thích kết quả của các Engine. Không dùng nhận xét của LLM thay cho phép kiểm tra bằng code.

## 2. Kết quả demo phải thể hiện

Người dùng mở dashboard, nhập yêu cầu như:

"Phân tích thị trường Philippines, chọn sản phẩm tiềm năng và lập chiến dịch bán hàng giả lập."

Hệ thống tự thực hiện:

1. Commander nhận nhiệm vụ.
2. Market Intelligence phân tích mock market data.
3. Product Scout đề xuất sản phẩm.
4. Offer & Strategy tính giá và lợi nhuận.
5. Content & Creative tạo nội dung quảng cáo.
6. Campaign Operator tạo chiến dịch DRAFT.
7. Lead & Sales mô phỏng xử lý lead.
8. Customer Success mô phỏng chăm sóc và vận chuyển.
9. Sales Analyst phân tích KPI.
10. Finance & Risk kiểm tra hiệu quả tài chính.
11. QA Tester kiểm tra kết quả và sự nhất quán.
12. Auditor kiểm tra các hành động được phép.
13. Monitor báo cáo tình trạng toàn bộ quá trình.

Commander tổng hợp báo cáo cuối cùng.

**Không được chỉ gọi DeepSeek 13 lần với cùng một prompt rồi coi là hoàn thành Multi-Agent.**

---

# PHẦN B — 10 PHASE TRIỂN KHAI

## PHASE 0 — Audit và chuẩn bị

Đọc toàn bộ project hiện tại.

Thực hiện:
- Kiểm tra FastAPI, SQLite, Docker và API endpoints.
- Kiểm tra logic 13 vai trò đang có.
- Xác định các phần đã hoạt động và lỗi còn tồn tại.
- Giữ nguyên dữ liệu, API key và các tính năng đang dùng được.
- Lập sơ đồ hệ thống Demo.
- Tạo bảng tiến độ Phase 0–9.

**Nghiệm thu:** Có báo cáo hiện trạng thực tế, không tự đánh dấu hoàn thành nếu chưa chạy test.

## PHASE 1 — Sửa DeepSeek và lỗi hệ thống

Giải quyết:
- Lỗi tiếng Việt khi hiển thị.
- `finish_reason=length`.
- `empty model result`.
- Cấu hình token quá thấp.
- Timeout, retry và lỗi HTTP.
- Ghi nhận token usage và chi phí ước tính.
- Lỗi Agent không trả kết quả nhưng vẫn báo thành công.

Kiểm tra encoding thực tế giữa API, Python, SQLite và giao diện web; không sửa dữ liệu gốc khi vấn đề chỉ nằm ở cách PowerShell hiển thị.

Không chạy lại 13 lời gọi DeepSeek chỉ để kiểm tra lỗi.

**Nghiệm thu:** LLM mock test PASS; API thật được kiểm tra tối thiểu; response rỗng có trạng thái lỗi rõ ràng.

## PHASE 2 — Mock Business Environment

Xây một môi trường kinh doanh giả lập đầy đủ.

Bao gồm:
- Mock Market Data.
- Mock Meta Ads.
- Mock Products.
- Mock Suppliers.
- Mock Campaigns.
- Mock Leads.
- Mock Orders.
- Mock Logistics.
- Mock Customer Conversations.
- Mock Finance.

Tạo dữ liệu kịch bản Philippines dựa trên bộ dữ liệu demo hiện có, chẳng hạn:

- Sản phẩm mẫu: LU-PH-001.
- Giá bán: 499 PHP.
- Giá vốn: 180 PHP.
- Vận chuyển: 75 PHP.
- Phí thanh toán: 18 PHP.
- Ngân sách: 15.000 PHP.
- Chiến dịch DRAFT: 4.000 PHP.
- Tồn kho: 50.
- Leads: 100.
- Confirmed: 20.
- Delivered: 15.
- Returned: 2.

Dùng fixtures cố định để kết quả có thể kiểm chứng; có thể thêm sản phẩm giả lập khác để Product Scout thực sự so sánh, nhưng phải đánh dấu rõ là dữ liệu mô phỏng.

Tạo Mock APIs cho Agent truy vấn dữ liệu như đang làm việc với hệ thống thực tế.

Không kết nối dịch vụ bên ngoài.

**Nghiệm thu:** Mock APIs trả dữ liệu nhất quán, có thể kiểm thử độc lập.

## PHASE 3 — Commander và Workflow Engine

Triển khai cơ chế điều phối thật ở mức demo.

Yêu cầu:
- Commander tiếp nhận mục tiêu.
- Chuyển mục tiêu thành các nhiệm vụ có dependency.
- Giao nhiệm vụ cho đúng Agent.
- Theo dõi đầu vào và kết quả từng nhiệm vụ.
- Lưu trạng thái vào SQLite.
- Có retry Agent lỗi.
- Có cancel nhiệm vụ.
- Có khả năng xem lại kết quả mà không gọi LLM lần nữa.
- Không cho Agent sau chạy nếu dependency bắt buộc chưa hoàn thành.
- Có checkpoint và xử lý restart container.

Trạng thái:
`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`, `CANCELLED`.

**Nghiệm thu:** Có bằng chứng Commander điều phối ít nhất một workflow nhiều bước với kết quả Agent trước được Agent sau sử dụng.

## PHASE 4 — Triển khai phối hợp 13 Agents

Tạo Agent Registry với nhiệm vụ, công cụ, schema input/output và quyền hạn riêng cho từng Agent.

Mỗi Business Agent phải tạo artifact chuyên biệt:

- Market Intelligence: Market Report.
- Product Scout: Product Shortlist.
- Offer & Strategy: Pricing & Offer Proposal.
- Content & Creative: Content Brief & Draft Ads.
- Campaign Operator: Campaign Plan.
- Lead & Sales: Lead Processing Report.
- Customer Success: Customer Care & Delivery Report.
- Sales Analyst: KPI Report.
- Finance & Risk: Finance & Risk Report.
- Commander: Execution Plan & Final Summary.

Các Supervisor tạo báo cáo giám sát riêng.

Yêu cầu:
- Dữ liệu được bàn giao qua artifact có schema.
- Agent không được tự bịa dữ liệu thị trường hay số liệu kinh doanh.
- Tính toán số học quan trọng phải dùng Python.
- LLM chỉ hỗ trợ suy luận, lập kế hoạch và diễn giải.
- Mock mode phải chạy được khi không có DeepSeek.
- LLM mode phải có giới hạn token và ngân sách riêng.
- Không cần 13 container độc lập.

**Nghiệm thu:** Workflow có 13 vai trò rõ ràng, kết quả khác nhau theo chức năng và có dấu vết bàn giao dữ liệu.

## PHASE 5 — Supervisory Agents và kiểm tra chéo

Triển khai:

**QA Engine**
- Kiểm tra tính đúng của các phép tính.
- Kiểm tra schema.
- Phát hiện số liệu không nhất quán.
- Kiểm tra artifact thiếu thông tin bắt buộc.

**Audit Engine**
- Kiểm tra quyền Agent.
- Ghi log hành động.
- Chặn hành động WRITE không được phép.
- Phân biệt DRAFT và hành động được duyệt.

**Monitoring Engine**
- Theo dõi Agent đang chạy.
- Phát hiện timeout, retry bất thường.
- Ghi nhận lỗi và sự kiện.
- Theo dõi thời gian, token và trạng thái.

Tạo ba Supervisory Agents đọc bằng chứng từ Engine và đưa ra báo cáo, cảnh báo.

Bổ sung error injection:
- Sửa giả lập giá vốn 180 thành 9.999 PHP.
- Agent bị timeout.
- Artifact thiếu trường.
- Campaign Operator cố publish quảng cáo thật.
- Agent trả response rỗng.

**Nghiệm thu:** QA phát hiện lỗi chi phí, Auditor chặn publish và Monitor phát hiện timeout.

## PHASE 6 — Dashboard Demo

Tạo dashboard trực quan tại:

`http://localhost:8088/dashboard`

Tối thiểu có:
- Ô nhập yêu cầu và nút Start Demo.
- Chọn Mock Mode hoặc DeepSeek Mode.
- Hiển thị 13 Agents với trạng thái cập nhật.
- Sơ đồ công việc và quan hệ dependency.
- Xem đầu vào/đầu ra từng Agent.
- Xem kết quả bàn giao.
- Xem QA, Auditor, Monitor.
- Xem token usage, lỗi và lịch sử.
- Nút xem lại Run, Retry lỗi, Cancel.
- Báo cáo cuối của Commander.

Mock Mode phải là chế độ mặc định.

Ưu tiên giao diện đẹp, dễ quan sát, không cần thiết kế một SaaS phức tạp.

**Bổ sung 05/11/2026:** phần trực quan chính là **văn phòng 3D isometric** (mỗi agent một phòng theo khu phòng ban, nhân vật đổi trạng thái, bong bóng việc đang làm, tài liệu bay khi bàn giao, thanh Tự xoay/Tên/Bong bóng/Toàn cảnh/Tổng quan). Chế độ 2D vẫn đủ 10 thành phần trên. Đặc tả: `levelup-agent-demo-vmm/docs/DEMO_DASHBOARD_3D.md`.

**Nghiệm thu:** Có thể thao tác toàn bộ demo từ trình duyệt mà không cần PowerShell.

## PHASE 7 — ARIS Runtime Demo

Tham khảo:

https://github.com/tauhb/aris-agent

Mục tiêu: đánh giá khả năng sử dụng ARIS làm Agent Runtime/Commander cho hệ thống.

Thực hiện:
- Kiểm tra license, dependency và kiến trúc repo.
- Đánh giá tương thích Docker Linux.
- Kiểm tra phụ thuộc macOS Keychain.
- Thiết kế ARIS adapter.
- Nếu chạy được an toàn, thử tích hợp một workflow nhỏ với mock tools.
- So sánh với runtime nội bộ đã xây.
- Giữ khả năng fallback khi ARIS lỗi.

Không bắt buộc chuyển toàn bộ 13 Agents sang ARIS nếu repo chưa phù hợp.

**Nghiệm thu:** Có bằng chứng thử nghiệm ARIS hoặc báo cáo blocker cụ thể. Adapter chưa chạy không được tính là tích hợp thành công.

## PHASE 8 — Kiểm thử End-to-End

Tạo ít nhất 5 kịch bản:

**Scenario 1 — Happy Path**
Commander điều phối đủ 13 vai trò và tạo báo cáo thành công.

**Scenario 2 — Invalid Cost**
QA phát hiện giá vốn sai và đánh dấu FAIL.

**Scenario 3 — Unauthorized Action**
Auditor chặn Campaign Operator khi cố thực hiện hành động publish.

**Scenario 4 — Agent Failure**
Một Agent timeout; Monitor ghi lỗi, kết quả cũ không bị mất và retry đúng Agent lỗi.

**Scenario 5 — No LLM**
Tắt DeepSeek, toàn bộ demo vẫn chạy bằng Mock Mode.

Thực hiện unit, integration và end-to-end tests.

Không sử dụng API thật để kiểm tra lỗi có thể giả lập.

**Nghiệm thu:** 5 kịch bản có bằng chứng PASS/FAIL; những kịch bản chưa đạt phải được sửa hoặc ghi rõ blocker.

## PHASE 9 — Đóng gói và bàn giao Demo

Hoàn thiện:
- Docker Compose.
- Dashboard.
- Database schema và dữ liệu demo.
- API documentation.
- File README hướng dẫn sử dụng.
- Reset Demo Data an toàn.
- Báo cáo kiểm thử.
- Sơ đồ kiến trúc.
- Phân biệt chức năng thực hiện bằng code, mock và LLM.
- Bảng hạn chế của bản demo.

Tạo tài liệu `docs/DEMO_FINAL_REPORT.md`.

**Nghiệm thu cuối:** Người dùng có thể mở trình duyệt, bấm Start Demo và quan sát toàn bộ quá trình mà không cần cấu hình thêm công cụ kinh doanh thật.

---

# PHẦN C — QUY TẮC BẮT BUỘC

### Giới hạn phạm vi

- DEMO ONLY, chạy local.
- Không triển khai AWS/VPS.
- Không triển khai PostgreSQL production.
- Không kết nối Meta Ads/Pancake/Shopify thật.
- Không sử dụng Facebook account thật.
- Không gửi tin nhắn khách hàng thật.
- Không chạy quảng cáo thật.
- Không mua hàng hoặc thanh toán.
- Không phát sinh chi phí dịch vụ ngoài DeepSeek đã có.
- Không tạo thêm agent ngoài 13 vai trò đã xác định.
- Không tự push GitHub.

### Giới hạn LLM

- Dùng DeepSeek hiện tại, không tự đổi provider.
- Mock Mode là mặc định.
- Dùng mock responses trong unit/integration tests.
- Tối đa 2 lời gọi DeepSeek thật trong toàn bộ phiên triển khai nếu chưa được phê duyệt thêm.
- Không lặp request trả phí khi không cần thiết.
- Không tiết lộ API key trong log hoặc báo cáo.
- Theo dõi token và đặt giới hạn chi phí.

### Cách làm việc

1. Bắt đầu từ Phase 0.
2. Kiểm tra những chức năng đã có, tránh viết lại không cần thiết.
3. Triển khai từng Phase theo thứ tự.
4. Sau mỗi Phase, chạy test và ghi PASS/FAIL.
5. Tự sửa lỗi khi phát hiện.
6. Tiếp tục các Phase tiếp theo nếu không có blocker.
7. Không hỏi người dùng xác nhận sau mỗi Phase.
8. Không tuyên bố hoàn thành khi mới tạo mock output.
9. Nếu hết token/context, lưu chính xác tiến độ và bước tiếp theo.
10. Phiên Claude sau phải đọc handoff để tiếp tục, tránh làm lại từ đầu.

### Tài liệu cần duy trì

- `docs/DEMO_PLAN.md`
- `docs/DEMO_PHASE_STATUS.md`
- `docs/DEMO_ARCHITECTURE.md`
- `docs/DEMO_TEST_REPORT.md`
- `docs/DEMO_HANDOFF.md`
- `docs/DEMO_FINAL_REPORT.md`

Mỗi Phase có trạng thái:
`NOT_STARTED`, `IN_PROGRESS`, `DONE`, `PARTIAL`, `BLOCKED`.

### Yêu cầu cuối cùng

Hãy **bắt đầu triển khai ngay**, không chỉ lập kế hoạch.

Ưu tiên P0–P6 để bản Demo hoạt động hoàn chỉnh, tiếp tục P7–P9 sau đó.

Tự kiểm thử, build Docker và sửa lỗi. Khi kết thúc, báo cáo ngắn:

- Đã hoàn thành bao nhiêu Phase.
- Có bao nhiêu Agent hoạt động đúng.
- QA/Auditor/Monitor có hoạt động độc lập không.
- Dashboard có sử dụng được không.
- ARIS đã tích hợp thật hay mới đánh giá.
- Tổng lời gọi DeepSeek thực tế.
- Những phần còn thiếu.

**Mục tiêu cuối cùng: Một bản Demo 13 AI Agents có thể trình diễn và nghiệm thu trên máy local, không phải hệ thống kinh doanh production.**