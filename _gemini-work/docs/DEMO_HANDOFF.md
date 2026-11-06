# Handoff

Trạng thái từng phase: `DEMO_PHASE_STATUS.md` (nguồn duy nhất). Checkpoint bên dưới là mốc lịch sử, mới nhất ở trên. Phiên sau bắt đầu bằng prompt ở `DEMO_PLAN.md` mục 9.

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
