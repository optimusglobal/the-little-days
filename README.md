# Cập nhật ưu tiên v1.3 — Idea GPT / Idea Gemini

Đọc [Idea pilot v1.3](docs/SHEET_V1_3_IDEA_PILOT.md). C=Idea GPT, D=Idea Gemini, AF=Hook, L5 giữ nguyên. D chỉ nhận bản viết lại thật của Gemini; chưa chạy stage sau idea.

---

# The Little Days

Workflow hiện hành: [Sheet v1.2 và pilot từng bước](docs/SHEET_V1_2_PILOT_WORKFLOW.md).
Sheet: https://docs.google.com/spreadsheets/d/1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM/edit

GPT điều phối; GitHub quản lý code/lượt chạy; Mia thực thi; Gemini hỗ trợ sáng tạo và review thật.

## Trạng thái

- Schema v1.2: 4 tab, production A–AE, L5 canonical, config/status catalog và nhật ký A–X.
- Mặc định runner dùng config.pilot.json. Deployment CHUA_KICH_HOAT, render disabled, workers rỗng.
- Plan hỗ trợ Sheet mới; run bị chặn trước worker/write khi chưa activated.
- Chưa di chuyển IDEA_001/002, chưa chạy AI/browser/render hoặc bật lịch trên Sheet mới.
- Gemini Web là ứng viên pilot, API tùy chọn; adapter Web gửi/nhận/lưu phản hồi chưa được nghiệm thu.
- Render/export v1.2 chưa commissioned và bị chặn; signed-approval guards hiện có giữ nguyên.
- Các tài liệu/checkpoint cũ là lịch sử, không phải bằng chứng runtime hiện tại.

## Kiểm tra offline

```bash
python -m unittest discover -s tests -v
python runner.py plan --config config.pilot.json --snapshot examples/pilot.input.json
```

Action Little Days - plan input dùng config mới, chỉ đọc; chưa dispatch live trong lần cập nhật này.
config.example.json/config.mvp.example.json/examples/input.json chỉ giữ cho tests và compatibility lịch sử.
Không dùng legacy config để bỏ qua stop của chủ dự án.

Tiếp theo chỉ thực hiện một stage khi chủ dự án yêu cầu; lưu output thật/evidence rồi dừng.
Không sửa main, không merge PR #1, không tạo production keys, không tự render/đăng bài.
