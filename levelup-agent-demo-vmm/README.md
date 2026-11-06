# Level Up — Demo 13 AI Agents (DEMO ONLY)

Bản demo chạy trên máy local: 13 AI agent của một phòng kinh doanh giả lập nhận nhiệm vụ, phối hợp theo thứ tự phụ thuộc, dùng dữ liệu giả lập, được ba engine kiểm tra bằng code và hiển thị trên một **văn phòng 3D** trong trình duyệt.

**Đây chỉ là demo.** Không kết nối quảng cáo, CRM, POS, nhà cung cấp hay thanh toán thật. Mọi số liệu đều giả lập (`synthetic: true`). Chiến dịch luôn ở trạng thái DRAFT; lệnh publish thật luôn bị chặn.

## Chạy

Cần Docker Desktop (Linux containers; đã thử với Docker VMM trên Windows).

```powershell
cd D:\LevelUp-Agent-Demo\levelup-agent-demo-vmm
Copy-Item .env.example .env        # chỉ lần đầu; khóa DeepSeek là tùy chọn
docker compose up -d --build
```

Mở **http://localhost:8088/dashboard** → bấm **Start Demo ▶**. Mock Mode là mặc định, không cần khóa DeepSeek và không tốn phí.

- Chọn lỗi giả lập ở form trái để xem QA/Audit/Monitor bắt lỗi.
- Bấm vào một phòng để xem đầu vào, đầu ra, lỗi và nút **Retry** của agent đó.
- **Tổng quan (2D)** hoặc `http://localhost:8088/dashboard?mode=2d` khi máy không chạy được 3D.
- Tài liệu API: `http://localhost:8088/docs` và [docs/DEMO_API.md](docs/DEMO_API.md).

Dừng: `docker compose down` (giữ dữ liệu trong volume `demo_data`).

## 13 agent

| # | Agent | Kết quả (artifact) |
|---|---|---|
| 01 | Sales Director / Commander | Kế hoạch 14 bước, báo cáo cuối (DRAFT_READY · HOLD_DRAFT · NEEDS_REVIEW) |
| 02 | Market Intelligence | Báo cáo thị trường: phễu và tỷ lệ |
| 03 | Product Scout | Danh sách sản phẩm, biên lợi nhuận, SKU được chọn |
| 04 | Offer & Strategy | Giá, biên, điểm hòa vốn |
| 05 | Content & Creative | Brief và 3 mẫu quảng cáo DRAFT |
| 06 | Campaign Operator | Kế hoạch chiến dịch DRAFT |
| 07 | Lead & Sales | Báo cáo lead, câu trả lời nháp |
| 08 | Customer Success | Giao hàng, đổi trả, ticket |
| 09 | Sales Analyst | KPI: ROAS, CPA |
| 10 | Finance & Risk | Lợi nhuận sau quảng cáo, rủi ro |
| 11 | QA Tester | Báo cáo từ QA Engine |
| 12 | Auditor | Báo cáo từ Audit Engine |
| 13 | Monitor | Báo cáo từ Monitoring Engine |

## Chế độ DeepSeek

Điền `DEEPSEEK_API_KEY` trong `.env`, khởi động lại (`docker compose up -d`), chọn **DeepSeek** trên form. Một run gọi tối đa 14 lần (mỗi task một lời diễn giải), giới hạn `LLM_RUN_TOKEN_BUDGET` token; hết hạn mức thì dùng văn bản mẫu. **Có tính phí.** LLM chỉ viết lời diễn giải, không bao giờ thay số liệu.

## Xóa dữ liệu demo

Xóa toàn bộ run nhưng giữ cấu trúc (từ chối nếu còn run đang chạy):

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8088/admin/reset-demo -ContentType 'application/json' -Body '{"confirm": true}'
```

Xóa sạch cả volume (không khôi phục được): `docker compose down -v`.

## Kiểm thử

```powershell
docker compose run --rm -T demo pytest -p no:cacheprovider -q     # unit + integration (DB tạm, không khóa DeepSeek)
python tools/e2e/run_e2e.py                                       # E2E: API, khởi động lại container, trình duyệt
```

E2E chạy trên container riêng ở cổng 8090/8091, không đụng container và dữ liệu chính. Kết quả: `tests/e2e/results/latest.json` và ảnh chụp trong `tests/e2e/results/shots/`.

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [docs/DEMO_FINAL_REPORT.md](docs/DEMO_FINAL_REPORT.md) | Báo cáo bàn giao: kết quả, phân biệt code/mock/LLM, hạn chế |
| [docs/DEMO_ARCHITECTURE.md](docs/DEMO_ARCHITECTURE.md) | Kiến trúc và sơ đồ |
| [docs/DEMO_API.md](docs/DEMO_API.md) | API và biến môi trường |
| [docs/DEMO_TEST_REPORT.md](docs/DEMO_TEST_REPORT.md) | Biên bản nghiệm thu từng phase |
| [docs/DEMO_DASHBOARD_3D.md](docs/DEMO_DASHBOARD_3D.md) | Thiết kế văn phòng 3D |
| [docs/DEMO_ARIS_EVALUATION.md](docs/DEMO_ARIS_EVALUATION.md) | Đánh giá ARIS |
| [docs/DEMO_DECISIONS.md](docs/DEMO_DECISIONS.md) · [DEMO_PHASE_STATUS.md](docs/DEMO_PHASE_STATUS.md) · [DEMO_HANDOFF.md](docs/DEMO_HANDOFF.md) | Quyết định, trạng thái, bàn giao cho phiên sau |
| [AGENTS.md](AGENTS.md) | Quy tắc cho agent lập trình làm tiếp |

## An toàn

- Cổng chỉ mở trên `127.0.0.1`; container chạy user không root, `cap_drop: ALL`, giới hạn RAM/CPU.
- Không đưa `.env` lên git; khóa không bao giờ xuất hiện trong log, artifact hay tài liệu.
- Không công khai demo ra Internet.
