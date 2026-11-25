# Kế hoạch thực hiện nâng cấp LevelUp Agent Demo

Ngày 23/11/2026, chủ dự án đã duyệt [phạm vi bốn mốc và tiêu chí nghiệm thu](DEMO_KE_HOACH_NANG_CAP_4_MOC.md). Bảng dưới dùng để giao việc theo thứ tự. Tình trạng thực tế và kết quả chạy được ghi tại [sổ phase](DEMO_PHASE_STATUS.md) và [báo cáo kiểm thử](DEMO_TEST_REPORT.md).

## Phiếu công việc đầu tiên — hoàn tất A0

**Đầu vào:** A0 đang PARTIAL theo [handoff](DEMO_HANDOFF.md). Tài liệu A0 đã có. Việc còn lại là xác lập mốc cơ sở có thể chạy lại.

- [ ] Ghi Git HEAD và trạng thái working tree, cấu hình mock, phiên bản Docker/Compose và thời điểm đo. Kiểm tra Docker daemon trước khi build. Ghi nhận người có quyền cuối là chủ dự án; người được ủy quyền chỉ ghi khi có chỉ định.
- [ ] Trong thư mục ứng dụng, chạy `docker compose build -q`, sau đó `docker compose run --rm -T demo pytest -p no:cacheprovider -q`. Lưu số passed/failed/skipped và nguyên nhân nếu bị chặn.
- [ ] Chạy `python tools/e2e/run_e2e.py` với môi trường thử tách biệt. Lưu bản kết quả theo lần chạy và kiểm riêng API, restart, trình duyệt, đặc biệt thao tác mở rộng thanh dưới trong dock-and-viewport.
- [ ] Nếu một ca bắt buộc lỗi, lưu bước tái hiện, log và ảnh nếu có. Giữ A0 PARTIAL và xác định lỗi môi trường hay ứng dụng trước khi trình phương án xử lý.
- [ ] Khi các nhóm đều đạt, gắn tag image đã kiểm thử là `levelup-vmm-demo:baseline-v2`, lưu image ID, báo cáo, đường dẫn bằng chứng và cập nhật handoff. Bàn giao cho chủ dự án quyết định mở A1.

## Thứ tự giao việc và bằng chứng bàn giao

Mỗi dòng là một phase. Người triển khai dùng tiêu chí chi tiết ở mục 3–6 của kế hoạch đã duyệt. Mỗi phase bàn giao cho chủ dự án một kết quả có thể tự kiểm lại.

| Mốc | Phase | Đầu ra để nghiệm thu |
|---|---|---|
| 1 | A0 | Image baseline và kết quả API, restart, trình duyệt của cùng phiên bản. |
| 1 | A1 | Một run có đủ 14 lượt giao và nhận kết quả; từ quyết định truy về được nguồn dữ liệu. |
| 1 | A2 | DB v2 mẫu nâng lên v3 hai lần vẫn đọc được lịch sử; có bằng chứng khôi phục bản sao. |
| 1 | A3 | Ca retry chỉ tạo một approval; chi phí khớp số gốc; chốt dừng còn hiệu lực sau restart. |
| 2 | A4 | Run giá vốn sai có báo cáo trước/sau sửa, tác động đến Finance và quyết định giữ nháp. |
| 2 | A5 | Phòng thảo luận dẫn đến đúng bằng chứng, kết thúc đúng giới hạn và không phát sinh hành động. |
| 3 | F1 | Bộ dữ liệu ba ngoại lệ và một ca sạch, đáp án tách khỏi dữ liệu agent; chủ dự án chốt ngưỡng mẫu. |
| 3 | F2 | Bảng đối chiếu chẩn đoán với đáp án, người nhận việc và điều kiện kiểm tra lại cho từng ca. |
| 3 | F3 | Truy từ từng phiên bản creative/trang bán về chi phí và đơn ròng; đánh dấu trường hợp chưa đủ căn cứ so sánh. |
| 4 | A6 | Snapshot ký ức có phạm vi; chạy ca đúng SKU, khác SKU và ca đã thu hồi. |
| 4 | A7 | Đề xuất học qua replay và ca đối chứng; lưu quyết định duyệt hoặc từ chối của con người. |
| 4 | A8a | Adapter mock kiểm quyền, chặn chế độ live và chạy được đường dự phòng nội bộ. |
| 4 | A8b | Web và kênh mock cùng duyệt một thẻ vẫn chỉ có một quyết định hiệu lực. |
| 4 | A9 | Có thể đối chiếu dữ liệu, dừng và duyệt trên dashboard; kiểm cả 2D, 3D và dock. |
| 4 | A10 | Bộ bằng chứng toàn luồng, diễn tập khôi phục và biên bản chủ dự án nghiệm thu bàn giao. |

## Quyết định sau từng phase

Người triển khai ghi phase, phiên bản, lệnh chạy, kết quả mong đợi/thực tế, đường dẫn bằng chứng và lỗi còn mở. Chủ dự án ghi quyết định **mở phase kế tiếp**, **trả về sửa** hoặc **dừng**, kèm ngày và phạm vi. Chủ dự án giữ quyền điều hành cuối cùng về ngân sách, quyền thực thi, dừng/mở lại và kích hoạt/thu hồi ký ức. Kết quả PASS của engine chỉ là bằng chứng kỹ thuật.
