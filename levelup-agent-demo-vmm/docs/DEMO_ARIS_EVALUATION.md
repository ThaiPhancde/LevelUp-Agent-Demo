# Đánh giá ARIS làm Agent Runtime / Commander (Phase 7)

05/11/2026. Repo: `https://github.com/tauhb/aris-agent`, commit `067695907ffa776afdf42595b08a7587e0c00424` (01/11/2026), clone vào `D:\LevelUp-Agent-Demo\_aris\aris-agent` (ngoài repo demo, coi là mã không tin cậy).

**Kết luận ngắn:** ARIS **không thay** runtime nội bộ cho bản demo. Một phần lõi của ARIS (giao việc `dispatch` và chia thẻ `planCards`) **đã chạy thật trên Docker Linux** qua adapter, điều khiển agent của demo bằng mock tool, không gọi LLM. Toàn bộ ARIS như một runtime (daemon, Web UI, Commander bằng LLM) chưa tích hợp: xem mục 5. Runtime nội bộ vẫn là đường chính và là đường dự phòng (đã kiểm).

## 1. Giấy phép, trạng thái, kiến trúc

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| Giấy phép | MIT © 2026 Hoàng Bá Tầu — dùng, sửa, tích hợp được, giữ thông báo bản quyền | `LICENSE` |
| Trạng thái | Tác giả **đã dừng phát triển**, mở mã cho cộng đồng | `README.md` mục "Trạng thái" |
| Ngôn ngữ, yêu cầu | TypeScript monorepo pnpm, 34 gói `packages/aris-*`, Node ≥ 22.19, pnpm 10.33 | `package.json` |
| Nền tảng | Plugin trên **DeepSeek Harness (dsh)** `@deepseek-ai/dsh*` bản `0.2.1-rc.2` (release candidate) qua Cordis; ARIS không fork dsh | `package.json`, `docs/phan-tich-kien-truc.md` §2 |
| Commander | Commander là **một phiên LLM** dùng công cụ `giao_viec`, `tao_the`, `giao_phong`; mỗi bot là thành viên Agent Team của dsh; bảng việc Kanban có thẻ chờ thẻ | `docs/specs/aris-commander.md`, `packages/aris-commander/src/dispatch.ts` |
| Bảo mật | Sandbox của dsh chặn ghi file, **không chặn mạng**; tác giả khuyên chạy daemon trong container có egress allowlist | `docs/phan-tich-kien-truc.md` §2 điểm 5 |

## 2. Tương thích Docker Linux và phụ thuộc macOS

| Chỗ phụ thuộc macOS | Ảnh hưởng trên Linux | Cách xử lý |
|---|---|---|
| `@aris/keychain` gọi `/usr/bin/security` | Không sập: lệnh không có → `get()` trả rỗng; khóa bí mật không đọc được | Gói có interface `KeychainRunner` để thay: viết runner đọc biến môi trường / Docker secret (mục 4) |
| `@aris/backup` dùng `osascript` | Một số thao tác sao lưu không chạy | Không cần cho demo |
| `@aris/computer` (`cua.ts`) chỉ chạy `darwin` | Tính năng điều khiển máy tắt | Không cần cho demo |
| `@aris/brain/native.ts`, `@aris/channels/media.ts` (giọng nói) chỉ macOS | Ném lỗi khi gọi | Không cần cho demo |
| Sandbox tiến trình dsh | dsh hỗ trợ cả macOS Seatbelt và Linux bwrap/Landlock | — |

Build và test toàn repo trên `node:22-bookworm`: xem mục 6 (kết quả chạy thật).

## 3. Thử tích hợp: ARIS dispatch điều khiển agent LevelUp (đã chạy)

Script: `tools/aris-adapter/spike.mjs`. Kết quả: `tools/aris-adapter/spike-result.json`, `spike-fallback-result.json`.

```bash
docker run --rm -v D:/LevelUp-Agent-Demo/_aris/aris-agent:/aris:ro \
  -v D:/LevelUp-Agent-Demo/levelup-agent-demo-vmm/tools/aris-adapter:/spike:ro \
  -e DEMO_URL=http://host.docker.internal:8088 node:22-bookworm node /spike/spike.mjs
```

- Nạp **mã thật** `packages/aris-commander/src/dispatch.ts` (không import gì, không I/O; Node 22.23 tự bỏ kiểu TypeScript) trên **Linux**.
- `planCards` của ARIS tạo 4 thẻ có thứ tự chờ: thị trường → chọn sản phẩm → tính giá → QA.
- Commander của demo (vòng lặp tất định, thay Commander LLM của ARIS) gọi `dispatch` của ARIS cho từng thẻ sẵn sàng. `LevelUpTeamPort` thực hiện `TeamPort` của ARIS: "đồng đội" = agent trong registry LevelUp, làm việc bằng cách gọi đúng mock tool của mình qua `GET /mock/*` của demo.
- Kết quả: 4/4 thẻ `completed`, đúng agent `02 → 03 → 04 → 11`, đúng thứ tự.
- Luật của ARIS vẫn hiệu lực: giao sớm thẻ đang chờ → ARIS từ chối "Thẻ task-2 đang chờ thẻ khác xong.", không bot nào được gọi.
- **Dự phòng:** trỏ sai đường dẫn ARIS → adapter tự chuyển sang runtime nội bộ (`POST /runs?wait=true`) → run `COMPLETED`.
- Lời gọi DeepSeek: **0**.

Lỗi tìm thấy khi thử: đồng đội bắt đầu làm trước khi ARIS kịp gán thẻ (agent QA không gọi tool nào nên xong ngay) → thẻ cuối kẹt `in_progress`. Sửa: đồng đội chỉ bắt đầu sau khi `dispatch()` trả về, đúng cách dsh giao lượt.

## 4. Thiết kế adapter đầy đủ (chưa làm)

| Tầng ARIS | Ánh xạ sang demo |
|---|---|
| `TeamPort.createTask(blockedBy)` | một task trong `tasks` với `depends_on` (đồ thị `graph.py`) |
| `TeamPort.spawnTeammate` / `sendMessage` | `workflow` chạy đúng task của agent đó (`app/agents/handle`), artifact là kết quả trả về |
| `TeamPort.updateTask(complete)` | task `COMPLETED` + artifact; lỗi → `FAILED`, ARIS thấy thẻ chưa xong |
| Duyệt tập trung của ARIS | `approvals` + `POST /runs/{id}/approvals/{aid}` (HITL đã có) |
| `KeychainRunner` | `EnvKeychainRunner`: đọc `DEEPSEEK_API_KEY` từ biến môi trường / Docker secret, `set()` từ chối |
| Commander LLM của ARIS | chỉ bật khi được duyệt thêm ngân sách DeepSeek; mặc định Commander tất định của demo |

Cần thêm ở demo: một endpoint chạy **một task** (hiện chỉ chạy cả run), và chạy ARIS như một service Node thứ hai trong compose với egress allowlist.

## 5. Vì sao không chuyển cả 13 agent sang ARIS

1. Commander của ARIS là LLM: mỗi lần chia/giao là lời gọi DeepSeek; 13 bot × nhiều lượt vượt xa hạn mức 2 lời gọi thật (D-06) và phá yêu cầu "Mock Mode chạy không cần DeepSeek".
2. dsh là bản **release candidate** `0.2.1-rc.2`; ARIS đã ngừng phát triển → rủi ro bảo trì.
3. Thêm một stack Node/pnpm 34 gói vào demo Python một container, trái D-02 (giữ stack).
4. Guardrail của demo (QA/Audit/Monitor tất định, gateway chặn WRITE_EXTERNAL) nằm ở runtime nội bộ; với ARIS phải viết lại thành plugin dsh.

## 6. So sánh với runtime nội bộ

| Tiêu chí | Runtime nội bộ (Phase 3–6) | ARIS |
|---|---|---|
| Chạy không cần LLM | Có (Mock Mode) | Không cho Commander; có cho phần `dispatch` đã thử |
| Đồ thị phụ thuộc, retry, cancel, khôi phục sau restart | Có, có test | Có thẻ chờ thẻ; khôi phục việc lớn sau khởi động lại (theo đặc tả) |
| Engine kiểm tra tất định | Có (QA/Audit/Monitor) | Không có sẵn tương đương |
| Chạy Docker Linux | Có | Một phần đã chạy; toàn repo xem kết quả build bên dưới |
| Bảo trì | Trong tầm tay nhóm | Tác giả đã dừng |

**Kết quả build toàn repo trên Linux** (`node:22-bookworm`, Node 22.23, pnpm 10.33, mã nguồn mount chỉ đọc, không truyền khóa nào; script `D:\LevelUp-Agent-Demo\_aris\build.sh`, log `_aris\logs\build.log`):

| Bước | Kết quả |
|---|---|
| `pnpm install --frozen-lockfile` | **Thành công** 11,7 s; các gói `@deepseek-ai/dsh*` `0.2.1-rc.2` có trên npm; pnpm tự chặn script cài đặt của `@google/genai`, `protobufjs` |
| `pnpm build` (tsc 30 gói + client UI) | **Thành công** |
| `pnpm test` (vitest) | 137/140 file, **1.206/1.209 ca qua**, 2 ca lỗi, 1 bỏ qua, 2 lỗi `EPIPE` khi `packages/aris-brain/src/git.ts` ghi vào stdin của `git` (test "commit thay đổi của aris") |

Phân tích lỗi test: xem mục 6b.

## 6b. Lỗi test trên Linux

- Lần chạy đầy đủ: 3/140 file test lỗi, 2/1.209 ca lỗi, đều quanh `packages/aris-brain` khi gói này gọi `git` qua tiến trình con và ghi stdin (`git.ts:35`) → `EPIPE`. Đây là phần "brain" (ký ức có phiên bản bằng git), không thuộc Commander, `dispatch` hay keychain.
- Lần chạy lại để tách file lỗi (thêm/không danh tính git) **treo hơn 14 phút** và bị dừng: vitest không thoát sau lỗi `EPIPE` chưa bắt. Chưa xác định được lỗi do thiếu cấu hình git trong container hay do khác biệt nền tảng.
- Ảnh hưởng tới demo: không. Adapter không dùng `aris-brain`. Nếu sau này tích hợp ARIS đầy đủ, cần sửa `git.ts` (bắt lỗi stdin) và cấu hình git trong image.

## 7. Nghiệm thu Phase 7

| Tiêu chí (DEMO_ONLY P7) | Kết quả |
|---|---|
| Kiểm tra license, dependency, kiến trúc | **Đạt** (mục 1) |
| Tương thích Docker Linux, phụ thuộc macOS Keychain | **Đạt** (mục 2, 3, 6): cài và build thành công, 1.206/1.209 test qua trên Linux |
| Thiết kế ARIS adapter | **Đạt** (mục 4) |
| Thử tích hợp một workflow nhỏ với mock tools nếu an toàn | **Đạt, giới hạn**: workflow 4 thẻ qua `dispatch`/`planCards` thật của ARIS; không phải ARIS runtime đầy đủ |
| So sánh với runtime nội bộ | **Đạt** (mục 6) |
| Giữ khả năng fallback khi ARIS lỗi | **Đạt** (mục 3, đã chạy) |
| Adapter chưa chạy không được tính là tích hợp | Tuân thủ: chỉ phần đã chạy được ghi là đã tích hợp |
