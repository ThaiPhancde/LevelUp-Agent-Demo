# Phối hợp Claude Code + Gemini (Antigravity CLI)

Cập nhật: 05/11/2026 (Phase 3). Mẫu: `D:\CRM2\docs\antigravity-workflow.md`. **Tỷ lệ hiện tại: Claude 60 / Gemini 40** (D-15, người dùng 05/11/2026; trước đó 100/0 theo D-13). Tỷ lệ tính trên cả dự án: phase lõi (3, 5) Gemini ít hơn, phase giao diện và nội dung (4, 6, 8) Gemini nhiều hơn.

## 1. Vai trò

| | Claude Code — chỉ đạo, ~60% | Gemini 4 Argon qua `agy -p` — ~40% |
|---|---|---|
| Quyết định | Mọi quyết định: phạm vi, thiết kế, contract, nhận hay bỏ output | Không quyết định |
| Code lõi | `db`, `core/workflow`, `core/graph`, `core/registry`, `core/gateway`, `core/artifacts`, 3 `engines/*`, `llm/deepseek.py`, `compute()` của 13 agent, config, Dockerfile/compose | Không chạm |
| Contract | Pydantic schema artifact, chữ ký `compute()/narrate()`, REST API | Dùng đúng, không sửa |
| UI | Scene 3D `office3d.js` (camera, ánh xạ trạng thái, animation bàn giao), nút Retry/Cancel/Approve | Đạo cụ khu, panel, thanh công cụ, chế độ 2D theo contract Claude đã viết |
| Dữ liệu | Fixture số (giá, đơn, KPI) | Văn bản tự nhiên: hội thoại khách, mô tả sản phẩm, văn bản `mock_llm` theo 13 agent |
| Test | Integration workflow, engine, E2E 5 kịch bản | Test bảng cho hàm thuần đã có chữ ký; script Playwright theo kịch bản Claude viết |
| Rà soát | Review mọi diff, chạy test, nghiệm thu, cập nhật docs | Không tự nghiệm thu |

## 2. Thiết lập (05/11/2026)

- `agy` 1.5.0; `agy -p "Reply with exactly READY. Do not use tools."` → READY. Model: `gemini-4-argon-high`.
- Runner `tools/agy-runner/` copy từ CRM2 (giấy phép MIT).
- Repo chính chưa có git (D-12). Gemini chạy trong **bản sao có git** `D:\LevelUp-Agent-Demo\_gemini-work`, không có `.env` và `data/`. Claude đồng bộ code vào đó, commit baseline, chạy batch, nghiệm thu, rồi tự copy file đạt về repo chính (M-15).
- Checker chạy pytest trong image demo bằng bind mount bản sao.

```bash
cd /d/LevelUp-Agent-Demo/_gemini-work
python -I tools/agy-runner/run_agy.py ai-jobs/<batch>/jobs.json --repo . --logs ai-jobs/<batch>/logs --max-parallel 3
```

## 3. Quy ước giao việc

- Mỗi batch ở `ai-jobs/<phase>-<slug>/`: `work-order.md` (tiếng Anh), `jobs.json`, `prompts/`, `checker.py`, `logs/`.
- Mỗi job có `allowed_paths` đúng một file; không hai job cùng file; không job nào cùng file với Claude.
- Gemini không chạm `.env`, `app/db.py`, `app/core/*`, `app/engines/*`, `app/llm/deepseek.py`, Dockerfile, compose, docs quyết định.
- Không tin báo cáo tự nghiệm thu của Gemini. Claude chạy lại checker + toàn bộ pytest, tự tính lại một phần kỳ vọng, đọc toàn bộ nội dung văn bản.
- Mỗi batch ghi một dòng vào `ai-jobs/LEDGER.md`.

## 4. Việc giao Gemini theo phase

| Phase | Việc | Điều kiện |
|---|---|---|
| 3 | Test bảng `app/core/graph.py`; test bảng `app/mock/data.py`; 12 hội thoại khách giả lập `app/mock/conversations.json` (batch `p3-workflow`) | Claude đã viết hợp đồng thuần + checker |
| 4 | Văn bản `mock_llm` cho 13 agent (tiếng Việt, tham chiếu số từ artifact); test bảng cho `compute()` của từng agent | Claude đã chốt artifact schema + 1 agent mẫu |
| 5 | Test bảng cho quy tắc QA/Audit thuần | Claude đã viết engine |
| 6 | Đạo cụ từng khu (`office-layout.js`), `dashboard.html` + `panels.js` (thanh công cụ, ngăn kéo, tab, chế độ 2D), Playwright chụp 4 trạng thái — theo `DEMO_DASHBOARD_3D.md` §6 | Claude đã có scene `office3d.js` + schema layout + REST Phase 3–5 |
| 8 | Script Playwright S1–S5 theo kịch bản Claude viết | Dashboard xong |

## 5. Không giao Gemini

Workflow engine, 3 engine, gateway và quyền, LLM client, công thức tài chính, quyết định nghiệm thu, cập nhật `DEMO_DECISIONS/STATUS/HANDOFF`.
