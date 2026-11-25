# Kế hoạch nâng cấp LevelUp 13-Agent Demo qua bốn mốc

**Bản 1.0 · 23/11/2026 · CHỦ DỰ ÁN ĐÃ DUYỆT KẾ HOẠCH.** Xem [kế hoạch thực hiện và checklist A0](DEMO_KE_HOACH_THUC_HIEN.md). Chủ dự án quyết định phạm vi, giao phase bắt đầu và quyết định đi tiếp sau mỗi phase. Kết quả kiểm thử kỹ thuật và quyết định nghiệm thu của con người được ghi riêng.

## 1. Mục tiêu và điểm xuất phát

Người điều hành nhập một mục tiêu bán thử, xem đội kiểm tra dữ liệu, theo dõi một sai sót từ lúc phát hiện đến lúc sửa và quyết định có duyệt đề xuất hay giữ chiến dịch ở nháp. Ca mẫu của dự án minh họa vì sao cần cả Marketing lẫn Finance: ROAS 1,62 nhưng lợi nhuận đóng góp sau quảng cáo âm 1.062 PHP. Số liệu là giả lập. Sửa được giá vốn chưa đủ để kết luận nên mở rộng.

Giữ FastAPI, SQLite, Docker Compose, dashboard 3D/2D, 13 vai trò và đồ thị 14 task hiện có. Cả bốn mốc chạy local ở Mock Mode, 0 lời gọi DeepSeek thật trong đợt nâng cấp. Công cụ kinh doanh, phê duyệt qua kênh và ngân sách đều được mô phỏng. Publish, gửi tin thật và thanh toán thật luôn bị chặn, kể cả sau khi người dùng duyệt nháp.

Theo [trạng thái phase](DEMO_PHASE_STATUS.md) và [handoff](DEMO_HANDOFF.md), P0–P9 đã được bàn giao; A0 đang PARTIAL, A1 trở đi chưa triển khai theo sổ. File [kết quả E2E đã lưu](../tests/e2e/results/latest.json) ghi API 7/7, restart đạt, trình duyệt 8/9; ca dock-and-viewport bị đóng trang khi click. Đây là điểm xuất phát lịch sử. A0 phải đo lại trước khi gắn tag.

| Mốc | Phase theo thứ tự đề nghị | Câu hỏi chủ dự án nghiệm thu |
|---|---|---|
| 1. Một lượt chạy đáng tin | A0 → A1 → A2 → A3 | Truy được nguồn số liệu, ai giao việc và tại sao retry chỉ tạo một yêu cầu duyệt? |
| 2. Tự xử lý ngoại lệ | A4 → A5 | Đội phát hiện giá vốn sai, sửa đúng chỗ và giải thích được quyết định cuối? |
| 3. Chẩn đoán phễu bán hàng | F1 → F2 → F3, sau A5 | Với cùng tín hiệu nhiều click, ít đơn, đội phân biệt được lỗi đo lường, sai giá và thiếu bằng chứng? |
| 4. Học có duyệt và bàn giao | A6 → A7 → A8a → A8b → A9 → A10 | Bài học giúp lượt sau tốt hơn, có người duyệt và thu hồi được? |

Các mã A giữ nguyên ý nghĩa, chi tiết và ca S1–S9 trong [phương án A, mục 7–11 và 17](DEMO_PLAN_OPTION_A.md). F1–F3 là phạm vi mới trình duyệt. A8a về kỹ thuật chỉ cần A3; xếp vào mốc 4 để mốc 3 tập trung vào nghiệp vụ. Các bổ sung khác gồm kiểm nguồn chi phí, quyền dừng ở mốc 1 và ca đối chứng khi học ở mốc 4. Giữ các mặc định OA-D/OA-M đã ghi; thay đổi mặc định cần chủ dự án duyệt riêng.

## 2. Quyền điều hành cao nhất thuộc về con người

| Quyết định | Người có quyền | Việc hệ thống được làm | Bằng chứng bắt buộc |
|---|---|---|---|
| Mục tiêu, phạm vi thị trường, nguồn dữ liệu, hạn mức, ngưỡng rủi ro và quyền tự chủ | Chủ dự án hoặc người được ủy quyền rõ phạm vi | Kiểm điều kiện đã duyệt; agent được đề xuất thay đổi | Phiên bản chính sách, phạm vi ủy quyền, người duyệt và thời điểm hiệu lực |
| Giao việc và sửa trong một run | Commander điều phối trong phạm vi được người điều hành cho phép | Workflow kiểm phụ thuộc, số vòng và quyền; QA/Audit/Monitor ghi kết quả độc lập | Ai giao, ai nhận, artifact phiên bản nào, lý do và kết quả |
| Duyệt/từ chối nháp, giữ chiến dịch, quyết định tăng ngân sách hoặc dừng thử nghiệm | Người điều hành có quyền theo phạm vi; chủ dự án giữ quyền cuối | Finance/Commander đưa phương án. Gateway giữ yêu cầu vượt ngưỡng; phê duyệt trong demo chỉ áp cho đúng bản nháp và số tiền đó | Quyết định con người, lý do, đối tượng và phiên bản. Đổi số tiền phải xét lại chính sách |
| Dừng run, dừng khẩn toàn demo, cho phép hoạt động lại | Người điều hành được ủy quyền dừng; chủ dự án hoặc người được ủy quyền rõ ràng cho hoạt động lại | Đề xuất bổ sung chốt dừng bền qua restart. Khi dừng, chặn run mới, retry, dispatch tiếp và hành động mới tại gateway. Tác vụ đang tính có thể kết thúc nhưng không sinh hành động mới sau thời điểm chốt dừng | Nhật ký bật/tắt, tác vụ đang dở, hành động đã ghi trước đó; không tự chạy bù sau khi mở lại |
| Kích hoạt, rút hoặc khôi phục ký ức; chấp nhận rủi ro còn lại; mở phase kế tiếp | Con người có quyền | Agent đề xuất; replay và engine cung cấp bằng chứng. Từ chối, hết hạn, im lặng hoặc quá hạn chờ đều không cấp quyền | Người quyết, bản ghi trước/sau, thời điểm, kết quả replay và lý do |

Quyền trên được mô phỏng trong demo local. Web dùng ngữ cảnh người vận hành, kênh mock dùng vai trò do phía server kiểm theo OA-D13/OA-M15; danh tính kênh mock là tự khai trong môi trường thử. Không coi đây là SSO hoặc bằng chứng định danh production. Không nhận danh tính người duyệt do agent chèn vào payload. Nút dừng từng run hiện có và chốt dừng toàn demo có phạm vi khác nhau. Nếu người điều hành bác đề xuất hoặc dừng, giữ nguyên báo cáo QA/Audit và ghi một quyết định mới để bảo toàn lịch sử. Quyết định của người duyệt không biến dữ liệu sai thành PASS.

**Người được ủy quyền (chủ dự án chốt ngày 24/11/2026):** ngoài chủ dự án có tối đa 3 người được ủy quyền; con số 3 là giới hạn hiện tại, để ở cấu hình và nâng được mà không sửa mã. Không gán tên hay chức danh cố định. Chỉ cần một người được ủy quyền hợp lệ duyệt hoặc từ chối là hệ thống tuân theo, không chờ đủ số người; nếu nhiều người xử lý cùng một yêu cầu thì quyết định ghi nhận trước có hiệu lực, người sau thấy yêu cầu đã xử lý. Nhật ký luôn lưu định danh người bấm. Người được ủy quyền được duyệt/từ chối nháp, dừng khẩn và kích hoạt/thu hồi ký ức; riêng cho hoạt động lại sau dừng khẩn và đổi hạn mức/chính sách thuộc chủ dự án.

## 3. Mốc 1 — Một lượt chạy đáng tin

### A0 · Chốt phạm vi và mốc so sánh

- **Làm:** đối chiếu 13 OA-D và 18 OA-M với [sổ quyết định](DEMO_DECISIONS.md); phân biệt mục người dùng đã duyệt với mặc định. Chốt chủ thể có quyền dừng/mở lại và ba bổ sung F. Đọc handoff, kiểm tra môi trường rồi build và chạy suite mock trong container riêng. A0 là phase tài liệu và baseline.
- **Nghiệm thu:** lưu phiên bản mã, image ID, lệnh, số pass/fail/skip, kết quả API/restart/trình duyệt, kể cả dock-and-viewport. Chỉ gắn tag baseline-v2 khi suite đạt. Nếu lỗi tái hiện, lưu log/ảnh, trình phương án sửa riêng và giữ A0 PARTIAL. Không dùng số 441 hoặc 9/9 lịch sử thay lần đo mới.

### A1 · Giao việc có lý do và xác định nguồn dữ liệu

- **Làm:** mỗi lần task bắt đầu/kết thúc ghi dispatch/dispatch_result với run, task, người giao/nhận, attempt, điều kiện phụ thuộc và lý do. Liên kết tới artifact đầu vào/đầu ra; hiển thị lý do trong nhật ký. Với yêu cầu nhập tay, lưu mục tiêu gốc và phần kịch bản thực sự hiểu được như tên thị trường, sản phẩm, tiền tệ, giá/ngân sách cùng nguồn fixture, trích xuất hoặc mặc định.
- **Nghiệm thu:** happy path có đúng 14 lần giao và 14 kết quả; task bị ngắt có interrupted. Bấm từ quyết định về được đầu vào. Nhập thị trường khác Philippines vẫn thấy rõ mô hình dùng PHP nếu chưa có fixture tiền tệ phù hợp. Đầu vào chưa hiểu hiển thị là giả định cần xem lại.

### A2 · Nâng DB v3 và bảo toàn dữ liệu

- **Làm:** migration bổ sung bảng/cột theo phương án A cho rework, phòng, ký ức, đề xuất và adapter. Bổ sung lưu trạng thái dừng điều hành cùng nhật ký đổi trạng thái. Thử migration trên bản sao DB v2 có run, event và artifact cũ; kiểm đường quay lại bằng image và bản sao trước migration.
- **Nghiệm thu:** migrate hai lần vẫn đọc được cùng lịch sử; giá trị mặc định tương thích; mỗi key có tối đa một ký ức ACTIVE. Reset thường giữ ký ức, làm hết hạn đề xuất mở và giữ bộ đếm. Kiểm riêng reset có include_memory trên DB thử. Khôi phục bản sao và đọc được run đối chứng. Restart hoặc reset dữ liệu nghiệp vụ không vô tình mở chốt dừng.

### A3 · Retry an toàn, số liệu nhất quán và quyền dừng

- **Làm:** gateway xét quyền mỗi lần. Chỉ tái sử dụng kết quả khi run, task, tool, target, nội dung hành động và phán quyết khớp. Audit lọc theo attempt; lịch sử vẫn giữ đủ các lần. Truyền chi tiêu gốc từ Campaign qua báo cáo Leads đến KPI và Finance. Chạy thử chốt dừng ở workflow và ngay trước khi ghi hành động.
- **Nghiệm thu:** happy path vẫn có 8 tool_call. Đặt ngưỡng thử 3.000 PHP, tạo yêu cầu duyệt rồi ép diễn giải rỗng; retry chỉ còn một approval cho hành động đó. Khi ngân sách đổi qua ngưỡng, gateway đánh giá lại. Chọn số lead khiến CPL phải làm tròn; ad_spend downstream vẫn bằng số gốc. Người vận hành dừng khi đang có task, thử retry và restart: không phát sinh tool action sau chốt dừng, log trước đó vẫn xem được. Chỉ sau thao tác mở lại hợp lệ mới nhận run mới. Hai yêu cầu duyệt đồng thời chỉ nhận một quyết định.

**Demo để ký mốc 1:** mở một run, xem nguồn dữ liệu, tái hiện lỗi sau khi tạo approval, bấm retry rồi dừng khẩn. Chủ dự án đối chiếu một approval duy nhất, chi phí gốc và thời điểm chốt dừng trong log.

## 4. Mốc 2 — Đội xử lý một ngoại lệ đến cùng

### A4 · Trả việc theo phát hiện và tính lại kết quả

- **Làm:** khi QA/Audit phát hiện lỗi thuộc danh mục sửa được, Commander giao lại cho vai trò chịu trách nhiệm, ghi finding, artifact bị ảnh hưởng và phiên bản trước sửa. Với bad_cost, đọc lại báo giá mock đúng SKU rồi tính lại các đầu ra phụ thuộc. Bảo toàn bằng chứng cũ. Tách retry của task FAILED khỏi rework của task đã hoàn thành nhưng sai nghiệp vụ.
- **Nghiệm thu:** chạy cùng fixture hai lần, kết quả giống nhau sau khi bỏ ID/timestamp. Với max_rework=2, nhận 9.999 → 180 PHP, QA kiểm lại, report cho thấy biên 226 PHP/đơn, hòa vốn 18 đơn, đóng góp sau quảng cáo âm 1.062 PHP, kết luận HOLD_DRAFT. Với max_rework=0 giữ hành vi cũ. Đạt trần mà lỗi còn tồn tại thì ghi lý do và chuyển người xem xét; vượt miền cấu hình trả 422. Lệnh publish vẫn bị chặn và lưu dấu vết.

### A5 · Phòng thảo luận trình bày bằng chứng

- **Làm:** mở phòng rework hoặc risk theo trigger của A; dùng các vai trò hiện có và lời thoại mẫu, mỗi ý kiến chỉ về finding hoặc số liệu. Đặt giới hạn lượt/tin và lý do kết thúc. Quyết định sửa lấy từ rework_plan; lời thoại không có quyền ra lệnh.
- **Nghiệm thu:** một phòng risk cho mỗi run đủ điều kiện; phòng dừng khi hội tụ hoặc chạm giới hạn. So sánh bật/tắt phòng trên cùng fixture: vẫn 13 agent, 14 task, cùng quyết định, không thêm tool_call, approval hay lời gọi LLM do thảo luận. Người xem thấy Finance nêu số lỗ và sự kiện Commander giữ bản nháp.

**Demo để ký mốc 2:** người điều hành bật lỗi giá vốn, đối chiếu phiên bản trước/sau, xem lý do chiến dịch vẫn ở nháp và có thể dừng ngay cả khi còn lượt sửa.

## 5. Mốc 3 — Chẩn đoán phễu và truy kết quả về phiên bản quảng cáo

Ba phase F là phần mở rộng. Giữ run mặc định và các kỳ vọng S1–S9. Chỉ bật khi chọn kịch bản phễu; tái sử dụng Market, Content, Campaign, Leads, Sales Analyst, Finance, QA và Commander trong đồ thị hiện có. Ngưỡng dữ liệu đủ để kết luận phải do chủ dự án duyệt tại F1.

### F1 · Hợp đồng dữ liệu và bộ ca đối chứng

- **Làm:** định nghĩa fixture theo thị trường, tiền tệ, thời gian quan sát và nguồn. Gắn brief, creative/version, phiên bản trang bán, campaign và SKU. Cho mỗi bước ghi impressions, clicks, lượt vào trang, checkout, đơn, dữ liệu đo độc lập và chi tiêu gốc nếu có. Phân biệt số 0 quan sát được với dữ liệu chưa thu được. Tạo bảng đáp án chuẩn để nghiệm thu, đặt riêng khỏi đầu vào agent.
- **Nghiệm thu:** ít nhất ba fixture có cùng dấu hiệu nhiều click/ít đơn; có bản ghi sự kiện cho lỗi tracking, bằng chứng giá trang lệch offer và ca đo đầy đủ nhưng mẫu nhỏ. Thêm ca sạch để kiểm báo động nhầm. Mỗi mẫu có đúng phiên bản và khoảng thời gian; đổi tiền tệ/SKU không làm lẫn số liệu. Thiếu dữ liệu hiển thị “chưa có”, không tính thành 0.

### F2 · Phân loại nguyên nhân, nêu việc kế tiếp

- **Làm:** Sales Analyst xác định bước rơi và chất lượng đo lường; Content và Offer đối chiếu lời hứa/giá; Finance kiểm tra hạn mức giả lập. Commander xuất nhận định, bằng chứng, giả thuyết còn mở, người nhận việc, điều kiện kiểm tra lại và quyết định đề nghị. Dữ kiện mâu thuẫn chuyển người điều hành xem xét.
- **Nghiệm thu:** (1) tracking hỏng → yêu cầu kiểm tra đo lường, chưa kết luận nhu cầu thấp; (2) giá trang sai → trả đúng bên sửa giá hiển thị và kiểm lại offer; (3) mẫu nhỏ → ghi chưa đủ bằng chứng, nêu điều kiện xem lại; (4) ca sạch → không báo hai lỗi trên. Không ca nào tự tăng ngân sách. Đối chiếu đầu ra với đáp án F1, ghi số đúng/tổng số ca, từng lỗi phân loại và sự can thiệp của con người.

### F3 · Phiên bản creative và quyết định thử tiếp

- **Làm:** Content tạo bản nháp theo brief, lưu điểm cần sửa, tham chiếu và phiên bản cha. Campaign liên kết phiên bản với nhóm kết quả giả lập. QA rà giá, claim và tính nhất quán. Dashboard hiện hai phiên bản cạnh nhau, cửa sổ đo, đơn ròng, chi tiêu và đóng góp sau quảng cáo. Ghi rõ khi không thể so sánh hai nhóm.
- **Nghiệm thu:** cùng một SKU có hai creative và hai phiên bản trang; truy ngược mỗi chỉ số về đúng bộ dữ liệu. Chỉnh creative không ghi đè bản cũ. Đổi đồng thời trang bán và creative thì báo chưa thể quy hiệu quả cho riêng creative. Bộ test có ca điểm review nội dung tốt nhưng tài chính âm: kết luận giữ nháp vẫn đúng. Chỉ người điều hành chọn tiếp tục thử, yêu cầu sửa hoặc dừng.

**Demo để ký mốc 3:** người điều hành chọn ca ẩn nhãn đáp án, theo nguồn dữ liệu đến nhận định, rồi xem ca đối chứng. Bằng chứng nghiệm thu là run ID, bảng đáp án, kết quả thực tế và lịch sử quyết định; số liệu thử không được dùng để cam kết doanh thu thực.

## 6. Mốc 4 — Ký ức có người duyệt và bàn giao vận hành

### A6 · Ký ức có phạm vi và phiên bản

- **Làm:** ghim snapshot ký ức tại đầu run khi bật cả use_memory và MEMORY_READ. Gắn vai trò, task, SKU và phạm vi thị trường khi có; lưu nguồn, phiên bản và thay đổi trước/sau. Bài học về báo giá hướng dẫn kiểm lại nguồn, không đóng đinh giá 180 PHP. Người có quyền được rút/khôi phục phiên bản.
- **Nghiệm thu:** tắt ký ức cho kết quả giống baseline. Bật đúng phạm vi thì ca bad_cost qua QA lượt đầu, Monitor ghi memory_override. SKU/thị trường khác không bị áp nhầm; báo giá hợp lệ cập nhật được chấp nhận. Rút giữa run vẫn giữ snapshot để replay; run mới không dùng bản bị rút. Nếu cần ngăn áp dụng ngay trong run đang chạy, người điều hành dùng quyền dừng.

### A7 · Học bằng đề xuất và phát lại

- **Làm:** sau run đủ điều kiện, tạo đề xuất cho phép kiểm thuộc danh mục learnable. Replay trên run nguồn và ca đối chứng F1/A6, so quyết định, số liệu và quyền. Hộp duyệt ghi thay đổi dự kiến, bằng chứng, người quyết. Chỉ người có quyền kích hoạt đề xuất đã replay đạt và còn đúng phiên bản. Cấm học cách thay hạn mức, mở quyền hoặc bỏ qua Audit.
- **Nghiệm thu:** replay hai lần cùng dữ liệu cho cùng kết quả, không sinh hành động hay approval. Replay FAIL, replay cũ sau thay đổi ký ức hoặc duyệt lại đều bị từ chối. Sau khi chủ dự án duyệt, run sau dùng đúng bản; rút rồi chạy lại trở về hành vi trước. Cancel không thành bằng chứng học; lỗi ở bước học không đổi trạng thái run đã hoàn tất. Giữ nguyên kỳ vọng kịch bản gốc S7.

### A8a · Cổng kết nối mock và định danh người duyệt

- **Làm:** dựng adapter kênh, second brain, runtime và driver ngoài theo OA. Duyệt hành động qua thẻ mock có phạm vi vai trò. Chặn chế độ live khi khởi động, fallback runtime nội bộ theo thiết kế. Nội dung từ kênh ngoài lưu nguồn external.
- **Nghiệm thu:** đủ S9 trừ thẻ học; vai trò sai trả 403, đúng quyền mới được quyết một lần. Driver không gọi mạng/subprocess. Đọc kho tri thức ngoài phạm vi bị từ chối. Dữ liệu mock từ bên ngoài không thành chỉ thị hoặc ký ức có hiệu lực. Fallback giữ nguyên kết quả nghiệp vụ.

### A8b · Thẻ duyệt đề xuất học qua kênh mock

- **Làm:** sau A7 và A8a, dựng thẻ lp: khi đọc outbox. Callback kiểm quyền owner, trạng thái và phiên bản trước khi gọi cùng đường quyết định như trên web; server ghi kênh và người quyết.
- **Nghiệm thu:** đọc outbox không thêm dòng DB. Owner quyết xong thẻ biến mất; non-owner nhận 403. Gửi đồng thời từ web và kênh chỉ có một quyết định hiệu lực, lần sau trả 409. Không gửi tin thật.

### A9 · Dashboard cho người điều hành

- **Làm:** ghép phòng thảo luận, làm lại, ký ức, hộp duyệt, adapter mock và kết quả F. Trình bày riêng trạng thái task, quyền thực hiện hành động và kết luận kinh doanh. Cho xem nguồn, so phiên bản, từ chối, dừng và thu hồi trên 2D/3D. Chỉ tải chi tiết khi mở tab; API mặc định vẫn tắt rework, rooms và use_memory theo OA.
- **Nghiệm thu:** người dùng hoàn tất kịch bản A4 và F2 ở chế độ 2D, làm lại thao tác chính ở 3D, nhìn thấy quyền dừng và lịch sử từ chối. So payload get_run với mốc cơ sở theo OA-M16, phần tóm tắt bổ sung ≤ 2 KB; chi tiết phễu/creative lấy qua truy vấn riêng. Chạy lại toàn bộ ca trình duyệt hiện có, gồm dock-and-viewport; không lỗi console trong các ca nghiệm thu.

### A10 · Kiểm thử toàn luồng và bàn giao

- **Làm:** chạy suite trong container thử, E2E S1–S9, ca F1–F3, migration v2→v3, restart giữa task, retry sau lỗi, dừng khẩn, tranh chấp phê duyệt và thu hồi ký ức. Diễn tập khôi phục trên DB thử. Bàn giao cách chạy/dừng, bản sao, cách đọc log và danh sách giới hạn.
- **Nghiệm thu:** latest.json tổng hợp ok=true hoặc kèm báo cáo ca bổ sung có liên kết tới run ID; bắt buộc tất cả nhóm đạt, không thêm skip để che lỗi. Trong bộ ca nghiệm thu: 0 hành động trái quyền được thực thi, 0 hiệu ứng ghi trùng, 100% hành động/duyệt có dấu vết, dừng khẩn đạt và 0 lời gọi DeepSeek thật mới. Ghi cả tử số, mẫu số và phạm vi kiểm tra. Người điều hành tự chạy lại một ca lỗi và một ca thu hồi rồi ký biên bản bàn giao.

## 7. Cách nghiệm thu, dừng và bàn giao từng phase

1. Trước phase, người triển khai trình đầu vào, file dự kiến đổi, ca kiểm thử và điều kiện quay lại. Chủ dự án duyệt phạm vi phase. Tính năng mới chỉ bật trong ca thử được chọn.
2. Sau phase, ghi lệnh và phiên bản đã chạy, run ID, fixture, quyết định mong đợi/thực tế, ảnh 2D/3D nếu thay UI, số pass/fail/skip và lỗi còn mở. Cập nhật [TEST_REPORT](DEMO_TEST_REPORT.md), [STATUS](DEMO_PHASE_STATUS.md) và [HANDOFF](DEMO_HANDOFF.md) khi thực sự triển khai. Dùng volume thử; thao tác xóa/restore phải xác định đúng DB thử.
3. Chạy suite mock bằng `docker compose run --rm -T demo pytest -p no:cacheprovider -q`; kiểm toàn luồng bằng `python tools/e2e/run_e2e.py` tại A0, A10 và khi thay đổi luồng liên quan. So kết quả với baseline cùng cấu hình. Không đánh dấu DONE khi có ca bắt buộc FAIL/BLOCKED. Nếu dừng khẩn, lỗi phân quyền, ghi trùng hoặc migration làm mất dữ liệu: ngừng nghiệm thu, giữ log, phục hồi bản thử và trình chủ dự án quyết định.
4. Biên bản mỗi phase ghi **phase / phiên bản / bằng chứng / giới hạn / quyết định của người duyệt / người duyệt / ngày / phase được phép mở**. Trạng thái kỹ thuật PASS không tự mở phase kế tiếp. Phê duyệt kế hoạch khác với phê duyệt từng hành động nghiệp vụ.

## 8. Quyết định của chủ dự án ngày 23/11/2026

| Nội dung cần quyết | Phương án đề nghị | Trạng thái |
|---|---|---|
| Phạm vi bản demo | Giữ 13 vai trò, 14 task, Mock Mode; bổ sung F1–F3 sau A5; demo mốc 1–2 trước | Đã duyệt khung kế hoạch |
| Quyền điều hành | Chủ dự án giữ quyền cuối; ghi tên/vai trò được ủy quyền duyệt nháp, dừng, mở lại, duyệt và thu hồi ký ức. Trong demo một người có thể đảm nhiệm nhiều vai trò | Đã duyệt nguyên tắc; 24/11/2026 chốt tối đa 3 người được ủy quyền, không gán tên/chức danh, một người duyệt hợp lệ là đủ (xem mục 2) |
| Hạn mức và chính sách | Giữ mặc định A; 3.000 PHP chỉ là ngưỡng fixture để ép ca HITL. Chủ dự án chốt tiêu chuẩn dữ liệu đủ/thiếu tại F1; thay đổi về sau có phiên bản và người duyệt | Đã duyệt khung kế hoạch |
| Mở triển khai | Sau khi duyệt tài liệu, chỉ giao A0 để xác lập baseline. Chốt từng phase theo biên bản ở mục 7 | A0 là phase đầu tiên trong kế hoạch thực hiện |

## 9. Tài liệu đối chiếu

- [Phương án A](DEMO_PLAN_OPTION_A.md), [quyết định và mặc định](DEMO_DECISIONS.md), [quy tắc dự án](../AGENTS.md), [phạm vi demo](../../DEMO_ONLY.md). Câu hỏi chi tiết về S6–S9, hợp đồng API, điều kiện replay và phân công triển khai tra phương án A.
- [BA Brief](<D:/Docs - LevelUP AI BOS/Level_Up_AI_Business_Operating_System_Brief_for_BA.docx>) quy định Human Control & Governance, owner mỗi workflow, idempotency, kill switch và người phê duyệt thay đổi hạn mức. [Blueprint 2026](<D:/Docs - LevelUP AI BOS/Level_Up_Technology_OS_AI_Agent_Blueprint_2026.docx>) đặt quyền xác định mục tiêu và mức tự động hóa ở CEO. [OS Overview](<D:/Docs - LevelUP AI BOS/LevelUp_OS_Overview.docx>) nối creative ID, phiên bản, quyền sử dụng, duyệt và kết quả. Bốn mốc chỉ mô phỏng trong demo local.
- [Kinh nghiệm bàn giao giữa 9 agent](https://www.reddit.com/r/ClaudeAI/comments/1thi16y/how_i_built_a_9agent_team_where_my_agents/) gợi ý liên kết người nhận với artifact. [GoClaw](https://goclaw.sh/vi/blog/ai-agent-team) gợi ý kiểm lỗi âm thầm và phân cấp tự chủ. [Thí nghiệm 5 agent](https://homus.dev/talks/i-gave-5-ai-agents-100-to-start-a-business) gợi ý ca có click nhưng chưa có đơn; [talk marketing](https://homus.dev/talks/ai-agents-are-too-good-at-marketing-now) gợi ý truy theo phiên bản creative. Đây là nguồn xây tình huống kiểm thử. Bài Facebook của Nguyễn Tiệp chưa xác minh toàn văn, không dùng làm căn cứ đặt ngưỡng.
