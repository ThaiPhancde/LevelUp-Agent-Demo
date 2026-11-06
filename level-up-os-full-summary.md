# TỔNG QUAN HỆ THỐNG LEVEL UP OS & BLUEPRINT TRIỂN KHAI 2026

## 1. Bối cảnh & Mục tiêu Chiến lược

Level Up OS được định vị là Hệ điều hành Công nghệ (Technological Operating System) tích hợp và tự động hóa toàn bộ hoạt động vận hành Thương mại Điện tử (E-commerce) đa thị trường, đa ngôn ngữ và đa pháp nhân. Hệ thống giải quyết các thách thức kinh doanh cố hữu như dữ liệu phân tán, báo cáo sai lệch giữa các bộ phận, phụ thuộc lớn vào nhân sự thủ công và rủi ro thất thoát khi mở rộng quy mô.

Mục tiêu trung tâm của Level Up OS là thiết lập một **Nguồn Dữ liệu Chuẩn duy nhất (Single Source of Truth)**, chuyển đổi mô hình vận hành từ phụ thuộc con người sang mô hình tự động hóa có giám sát, tạo tiền đề vận hành **Phòng Kinh doanh Ảo với 10 AI Agents** chuyên môn hóa dưới sự kiểm soát chặt chẽ của hệ thống quy tắc nghiệp vụ (Rules First, AI Second).

---

## 2. 8 Nguyên tắc Kiến trúc Cốt lõi

Mọi thành phần kỹ thuật và quy trình vận hành của Level Up OS đều phải tuân thủ nghiêm ngặt 8 nguyên tắc kiến trúc:

1. **One Source of Truth (Nguồn dữ liệu chuẩn duy nhất):** Mọi chỉ số tài chính, đơn hàng, chi phí quảng cáo và khách hàng được định nghĩa nhất quán tại kho dữ liệu trung tâm BigQuery, triệt tiêu tình trạng sai lệch số liệu giữa Marketing, Sales và Kế toán.
2. **Rules First, AI Second (Quy tắc trước, AI sau):** AI Agent chỉ hoạt động trong phạm vi rào chắn (guardrails) do các quy tắc nghiệp vụ cứng quy định; không cho phép AI tự quyết định ngoài khuôn khổ logic kinh doanh.
3. **Human-in-the-Loop (Con người kiểm soát điểm trọng yếu):** Tất cả các hành động có mức độ rủi ro cao hoặc vượt hạn mức ngân sách bắt buộc phải qua bước phê duyệt trực tiếp của nhân sự cấp quản lý.
4. **Think ≠ Act ≠ Learn (Tách biệt Suy nghĩ, Thực thi và Học tập):** Mô hình AI lập kế hoạch (Think) độc lập với cổng thực thi API (Act) và quy trình cập nhật tri thức/mô hình (Learn) nhằm bảo đảm an toàn hệ thống.
5. **Observable by Design (Khả năng giám sát toàn diện):** Mọi quyết định, câu lệnh, chi phí token và vết thực thi của hệ thống cũng như AI Agent đều phải được ghi log đầy đủ vào nhật ký kiểm toán (Audit Log).
6. **Loose Coupling, High Cohesion (Đóng gói linh hoạt, gắn kết cao):** Kiến trúc các module nghiệp vụ và tích hợp API được thiết kế độc lập, cho phép thay thế hoặc nâng cấp từng phần mà không ảnh hưởng toàn hệ thống.
7. **Security & RBAC at Core (Bảo mật và phân quyền từ gốc):** Định danh tập trung (SSO) và phân quyền dựa trên vai trò (RBAC) đến từng cấp độ dự án, dự án con và thị trường.
8. **Scalable Infrastructure (Hạ tầng mở rộng linh hoạt):** Thiết kế chịu tải đa thị trường, sẵn sàng xử lý hàng triệu sự kiện (events) và giao dịch thời gian thực mà không làm giảm hiệu năng.

---

## 3. Khung Kiến trúc Hệ thống 6 Lớp (6-Layer Architecture)

Kiến trúc Level Up OS được tổ chức thành 6 lớp kỹ thuật phân tầng rõ ràng từ giao diện người dùng đến tầng quản trị:

* **Lớp 1: Experience Layer (Giao diện Tương tác & Điều hành)**  
  Màn hình trung tâm điều hành CEO Command Center, Dashboard quản lý chuyên biệt cho các phòng ban (Marketing, Sales, Operations, Finance) và cổng phê duyệt tức thì qua Telegram/Slack Bot.
* **Lớp 2: Business Applications Layer (Ứng dụng Nghiệp vụ Lõi)**  
  Tập hợp các hệ thống quản trị chuyên sâu bao gồm Marketing OS (quản lý chiến dịch, chi phí), CRM & Sales Pipeline (quản lý lead, hội thoại), Supply Chain & Operations OS (tồn kho, vận chuyển 3PL) và Finance/HRM OS (dòng tiền, đối soát).
* **Lớp 3: Orchestration Layer (Hệ thần kinh Điều phối n8n Engine)**  
  Trái tim điều phối hệ thống chạy trên nền tảng n8n Workflow Engine, chịu trách nhiệm định tuyến công việc, quản lý trạng thái (state machine), điều phối 10 AI Agent và xử lý quy trình phê duyệt Human-in-the-Loop.
* **Lớp 4: Data Platform Layer (Nền tảng Dữ liệu Dùng chung)**  
  Kho dữ liệu BigQuery đóng vai trò bộ nhớ trung tâm với mô hình phân lớp dữ liệu chuẩn hóa (RAW ➔ STAGING ➔ CORE ➔ MART), kết hợp với CSDL giao dịch PostgreSQL (OLTP) và Redis Cache xử lý thời gian thực.
* **Lớp 5: Integration Layer (Cổng Tích hợp & MCP Gateway)**  
  Cổng kết nối Model Context Protocol (MCP Tool Gateway) bảo mật, chịu trách nhiệm trao đổi dữ liệu và gọi API hai chiều với các nền tảng bên ngoài: Meta Ads, TikTok Shop, Shopify, Pancake POS, các đơn vị vận chuyển 3PL (GHN, GHTK, NinjaVan) và Google Sheets.
* **Lớp 6: Governance Layer (Quản trị & An toàn Hệ thống)**  
  Hệ thống định danh tập trung SSO/RBAC, bộ công cụ ghi vết Audit Log (`decision_log`), các rào chắn tự động phê duyệt và hệ thống ngắt mạch tự động khi phát hiện bất thường.

---

## 4. Mô hình Phòng Kinh doanh Ảo 10 AI Agents & Cấp độ Tự chủ

### Danh mục 10 AI Agent Chuyên môn
Hệ thống phòng kinh doanh ảo được điều phối bởi **Sales Director Orchestrator** cùng 9 Agent chuyên trách:
1. **Sales Director Orchestrator:** Phân rã mục tiêu kinh doanh tổng thể, giao việc và điều phối phối hợp giữa các Agent.
2. **Market Intelligence Agent:** Phân tích xu hướng thị trường, đối thủ cạnh tranh và hành vi người tiêu dùng.
3. **Product Scout Agent:** Tìm kiếm, đánh giá và đề xuất sản phẩm tiềm năng (Winning Products).
4. **Offer & Angle Agent:** Xây dựng thông điệp bán hàng, cấu trúc giá và các chương trình ưu đãi hấp dẫn.
5. **Content Creator Agent:** Tự động tạo kịch bản, hình ảnh, văn bản quảng cáo và nội dung bán hàng đa kênh.
6. **Campaign Operator Agent:** Khởi tạo, cấu trúc và theo dõi tiến độ các chiến dịch quảng cáo.
7. **Lead & Sales Agent:** Tiếp nhận lead, phân loại tiềm năng và hỗ trợ tư vấn chốt đơn tự động.
8. **Customer Success Agent:** Chăm sóc khách hàng sau bán, xử lý khiếu nại và tối ưu tỷ lệ mua lại.
9. **Performance Analyst Agent:** Phân tích hiệu quả chiến dịch, tối ưu hóa chỉ số ROAS, CPA và đề xuất điều chỉnh.
10. **Finance & Risk Agent:** Kiểm soát rủi ro tài chính, dòng tiền, hạn mức chi tiêu và phát hiện bất thường.

### Phân cấp Tự chủ (Autonomy Levels) & Rào chắn An toàn (Guardrails)
* **Khởi điểm vận hành:** Hệ thống áp dụng cấp độ tự chủ **L0 (Manual)**, **L1 (Assisted)** và **L2 (Conditional Autonomous)**. Các cấp độ cao hơn như L3 (Bounded Autonomous) chỉ kích hoạt khi từng Agent qua thử nghiệm.
* **Rào chắn Phê duyệt Ngân sách:**
  * Đơn hàng hoặc giao dịch có giá trị **≤ 2.000.000 VNĐ**: Hệ thống cho phép tự động phê duyệt (Auto-approve).
  * Đơn hàng hoặc giao dịch có giá trị **> 2.000.000 VNĐ**: Bắt buộc tạm dừng luồng và gửi yêu cầu phê duyệt Human-in-the-Loop qua Telegram/Slack.
* **Bộ Ngắt mạch Tự động (Circuit Breakers):**
  * **Daily Cap (Ngưỡng ngày):** Giới hạn chi tiêu không vượt quá 130% ngân sách kế hoạch ngày.
  * **Hourly Spike (Ngưỡng giờ):** Tự động ngắt chiến dịch nếu chi phí theo giờ tăng đột biến vượt +20% so me với trung bình lịch sử mà không tạo ra doanh thu tương ứng.

---

## 5. Phân công Trách nhiệm Chi tiết: BA/Dev A vs. BA/Dev B

Dự án được triển khai bởi đội ngũ nòng cốt gồm 2 thành viên đảm nhận hai trục năng lực chuyên biệt:

### BA/Dev A: Business & Data Specialist (Chủ trì Nghiệp vụ & Dữ liệu)
* **Phân tích Nghiệp vụ (BA):** Khảo sát quy trình hiện tại (AS-IS), thiết kế quy trình mục tiêu (TO-BE), viết tài liệu PRD, xây dựng User Stories và lập bộ tiêu chí nghiệm thu (Acceptance Criteria).
* **Quản trị Dữ liệu (Data Lead):** Thiết kế mô hình dữ liệu ERD, xây dựng Từ điển Dữ liệu (Data Dictionary), chuẩn hóa danh mục chỉ số (Metric Dictionary) và xây dựng hệ thống báo cáo BI (CEO Command Center) trên BigQuery.
* **Kiểm thử Nghiệp vụ (QA/QC):** Lập kịch bản kiểm thử, đối soát số liệu đa kênh và tổ chức nghiệm thu tính năng với các phòng ban.

### BA/Dev B: Platform & Integration Engineer (Chủ trì Hạ tầng & Tích hợp)
* **Hạ tầng & Kiến trúc (Tech Lead):** Rà soát mã nguồn (Codebase Audit), thiết kế mô hình Backend (Modular Monolith), quản lý CSDL OLTP (PostgreSQL) và thiết lập đường ống triển khai tự động CI/CD.
* **Tích hợp & Điều phối (Integration Lead):** Triển khai hệ thống n8n Workflow Engine, xây dựng Cổng tích hợp an toàn MCP Tool Gateway, lập trình kết nối API với Meta, TikTok, Shopify, Pancake và 3PL.
* **Bảo mật & Giám sát (DevOps/Sec):** Triển khai phân quyền định danh SSO/RBAC, xây dựng hệ thống thu gom log tập trung (`decision_log`) và thiết lập cơ chế cảnh báo sự cố tức thì.

---

## 6. Triển khai Hệ thống trên n8n Workflow Engine

n8n giữ vai trò là hệ thần kinh điều phối ở Lớp L3 với 4 nhóm luồng công việc (workflows) tiêu chuẩn:

1. **Ingestion & Data Pipelines Workflows:** Tiếp nhận sự kiện từ Webhook (đơn hàng, trạng thái 3PL) hoặc chạy Cron định kỳ lấy dữ liệu chi phí quảng cáo. Thực hiện chuẩn hóa về Canonical Schema và lưu trữ vào BigQuery.
2. **Business Logic & Guardrails Workflows:** Thực thi logic quy tắc nghiệp vụ cứng, kiểm tra hạn mức tồn kho/ngân sách và điều phối luồng phê duyệt Human-in-the-Loop qua Telegram.
3. **AI Agent Orchestration & MCP Gateway Workflows:** Tiếp nhận lệnh từ Agent, kiểm tra quyền RBAC và thực thi lệnh thông qua cổng MCP Gateway an toàn.
4. **Error Handling & Observability Workflows:** Thu gom lỗi hệ thống, tự động thử lại (Retry) với cơ chế Exponential Backoff, đẩy dữ liệu lỗi vào hàng đợi Dead-Letter Queue (DLQ) và ghi nhật ký kiểm toán vào BigQuery.

---

## 7. Quy trình Vận hành 1 Đơn hàng (Order Lifecycle Flow)

Luồng xử lý đơn hàng End-to-End được thực thi xuyên suốt 6 lớp kiến trúc:
1. **Tiếp nhận (L1 & L5):** Khách hàng tạo tương tác/đơn hàng trên kênh bán lẻ; API Webhook đẩy Payload thô về hệ thống.
2. **Chuẩn hóa (L3 & L4):** n8n chuyển đổi Payload về Canonical Schema và lưu bản ghi thô vào BigQuery `STAGING`.
3. **Kiểm tra Quy tắc (L3 & L6):** Hệ thống kiểm tra tồn kho và hạn mức giá trị. Nếu đơn hàng > 2.000.000 VNĐ, kích hoạt nút chờ phê duyệt qua Telegram; nếu ≤ 2.000.000 VNĐ, cho phép đi tiếp.
4. **Tạo Đơn nháp (L3 & L2):** AI Lead & Sales Agent làm giàu dữ liệu và gọi cổng MCP Gateway tạo đơn `DRAFT` trên Pancake POS / Shopify.
5. **Thực thi Giao vận (L2 & L5):** Hệ thống khóa tồn kho (Stock Allocation), đẩy thông tin sang nhà vận chuyển 3PL lấy mã vận đơn và cập nhật đơn sang trạng thái `CONFIRMED`.
6. **Kiểm toán & Báo cáo (L4 & L1):** Lớp Governance ghi log `decision_log` vào BigQuery, cập nhật chỉ số lên CEO Command Center và kích hoạt AI CS Agent chăm sóc sau bán.

---

## 8. Lộ trình Triển khai 90 Ngày & 7 Sản phẩm Bàn giao

### 6 Giai đoạn Triển khai
* **Phase 0 – Discovery (1–2 tuần):** Khảo sát hiện trạng, chốt tài liệu kiến trúc, backlog và phân công nhiệm vụ.
* **Phase 1 – Foundation (2–4 tuần):** Xây dựng hạ tầng SSO/RBAC, BigQuery Data Platform và n8n Integration Framework.
* **Phase 2 – Control Tower MVP (3–5 tuần):** Kết nối dữ liệu chi phí, lead, đơn hàng và phát hành CEO Command Center.
* **Phase 3 – CRM & Sales Workflow (4–6 tuần):** Hoàn thiện hệ thống quản lý lead, hội thoại và pipeline chốt đơn.
* **Phase 4 – Agent Sales Pilot (3–5 tuần):** Thử nghiệm 10 AI Agent ở cấp độ L0–L2 trên 1 thị trường/dự án mục tiêu.
* **Phase 5 – Controlled Execution (Mở rộng):** Kích hoạt cấp độ tự chủ L3 có hạn mức và mở rộng toàn bộ các thị trường còn lại.

### 7 Sản phẩm Bàn giao Bắt buộc sau Phase 0
1. **System Inventory:** Danh mục toàn bộ hệ thống, repo, API, database và trạng thái rủi ro.
2. **AS-IS / TO-BE Architecture:** Bản vẽ chi tiết sơ đồ kiến trúc hiện tại và kiến trúc mục tiêu 6 lớp.
3. **Business Process Map:** Bản đồ 3–5 quy trình nghiệp vụ ưu tiên hàng đầu kèm tác nhân và ngoại lệ.
4. **Data Dictionary & ERD:** Mô hình dữ liệu logic, sơ đồ quan hệ ERD và từ điển chỉ số chuẩn.
5. **Product Backlog:** Danh mục Epic, Feature, User Story phân cấp kèm ưu tiên và tiêu chí nghiệm thu.
6. **Agent Blueprint:** Bản thiết kế chi tiết 10 AI Agent (vai trò, công cụ MCP, hạn mức, cơ chế giám sát).
7. **90-day Execution Plan:** Kế hoạch hành động 90 ngày chi tiết theo tuần kèm mốc Milestone và phân công nhân sự.

---

## 9. Tiêu chuẩn Nghiệm thu (Definition of Done - DoD) & Bộ KPI

### 8 Tiêu chuẩn Nghiệm thu Bắt buộc (DoD)
1. **Trắc nghiệm Quy tắc:** 100% logic kinh doanh cứng được cấu hình bằng quy tắc quy trình trước khi gọi AI.
2. **Bảo mật & Định danh:** Phân quyền RBAC và kiểm tra SSO thành công trên toàn bộ các Endpoint API.
3. **Chuẩn hóa Dữ liệu:** 100% dữ liệu từ các kênh được ánh xạ thành công về Canonical Data Model.
4. **Kiểm toán Toàn diện:** Mọi hành động của AI Agent đều phát sinh bản ghi nhật ký `decision_log` đầy đủ.
5. **Human-in-the-Loop:** Cơ chế tạm dừng và duyệt qua Telegram/Slack hoạt động tin cậy, không thất thoát lệnh.
6. **Xử lý Lỗi & Tự phục hồi:** Hệ thống tự động thử lại (Retry) và chuyển lỗi vào Dead-Letter Queue khi mất kết nối API.
7. **Báo cáo Tự động:** Các chỉ số trên CEO Command Center đối soát khớp 100% với dữ liệu gốc của các nền tảng.
8. **Tài liệu Vận hành:** Hoàn thiện đầy đủ bộ tài liệu hướng dẫn vận hành (Runbook) cho Tech Team và phòng nghiệp vụ.

### Bộ Chỉ số Đánh giá Hiệu quả (KPIs)
* **Chất lượng Dữ liệu:** Tỷ lệ đối soát dữ liệu thành công đạt > 99.5%.
* **Độ Tin cậy Hệ thống:** Thời gian hoạt động liên tục (Uptime) đạt > 99.9%, tỷ lệ xử lý lỗi tự động đạt > 95%.
* **Tốc độ Xử lý:** Thời gian phản hồi API trung bình < 500ms, thời gian đồng bộ dữ liệu thời gian thực < 5 giây.
* **Hiệu quả Tự động hóa:** Giảm > 70% thời gian thao tác thủ công của nhân sự Marketing và Sales.
