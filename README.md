# The Little Days

Workflow hoạt hình gia đình 3D hướng tới khán giả Mỹ. Bản nháp đang hoàn thiện.

- [Workflow chuẩn](WL.optimus.md)
- [Thiết lập đọc Sheets / bộ điều phối](RUNNER_SETUP.md)
- [Chạy video Gemini trên Chrome máy bạn](BROWSER_SETUP.md)

## Trạng thái đã xác minh

GitHub Actions đọc được sheet thật (1 hàng hợp lệ). Commander kết nối máy Mia. Playwright extension đọc được tab Gemini và tải được video MP4. Kết quả hiện có: 720×1280, khoảng 10 giây; chưa QA sáng tạo/phụ đề.

## Chạy thử không dùng credit

```bash
python -m unittest discover -s tests -v
python runner.py plan --snapshot examples/input.json
```

## Chạy trên Chrome local

Đọc BROWSER_SETUP.md, khởi động `start-browser.cmd` rồi cấu hình quyền Sheets/Drive trên máy. `run_browser.py` dùng hàng đã có Frame 0 và prompt; hỗ trợ prepare-only, submit một lần, khôi phục conversation và tải raw.

**Chưa hoàn tất tự động sáu bước:** worker phân tích video, viết idea/script, tạo Frame 0 và review Gemini chưa được kết nối trong runner. Grok chưa có adapter đã kiểm chứng. Cài extension hoặc lưu code không đồng nghĩa job render mới đã chạy xuyên suốt. Không có lịch render/self-hosted runner mới được bật.

Không commit credential, cookie, token, runtime hay video riêng tư. Không có bước đăng công khai tự động.
