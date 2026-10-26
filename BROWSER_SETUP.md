# Chạy Gemini trên Chrome máy bạn — v0.2

Phần này bổ sung cho WL.optimus.md; không thay đổi kịch bản, Frame 0 hoặc cổng admin.

## Đã kiểm chứng trên máy Mia

- Commander Remote kết nối Windows.
- Playwright MCP + extension truy cập đúng tab Gemini bằng phiên đăng nhập hiện có.
- Gemini có kết quả trong conversation `14db0bc9fa718837`; metadata DOM: 720×1280, 10.005s.
- Nút tải đã lưu file MP4 vào Downloads. Đây là raw, chưa phải video final đã QA/phụ đề.

## Phạm vi tự động hiện có

Code đọc **hàng đã có Frame 0 + prompt** → tải đúng ảnh L/M từ Drive → gắn hash → chọn Gemini Video/9:16 → upload Frame 0 → dán một prompt → gửi một lần → lưu conversation/job → chờ → tải raw → giữ trạng thái QA pending.

Các worker phân tích nguồn, viết idea/script, tạo ảnh và phản biện Gemini trong `runner.py` vẫn chưa kết nối tự động. ChatGPT thực hiện các bước này trong phiên làm việc theo skill rồi điền sheet. Không coi bản v0.2 là hệ thống sáu bước chạy không giám sát.

Grok chưa có adapter đã kiểm chứng; chọn Grok sẽ báo thiếu, không tự đổi sang Gemini. Giao diện khác ngôn ngữ/nhãn có thể khiến adapter dừng. Không tự đăng nhập, xử lý CAPTCHA, đăng công khai hoặc đổi gói thanh toán.

## Cài đặt trên máy bạn

1. Clone repo (hoặc tải ZIP và giải nén). Cài dependency:

```powershell
python -m pip install -r requirements.txt
```

2. Cài Playwright Extension từ link trong tài liệu Microsoft: https://github.com/microsoft/playwright/blob/main/packages/extension/README.md
3. Chạy `start-browser.cmd` trong thư mục dự án. **Phải khởi động từ thư mục dự án** để upload ảnh trong allowed roots. Không bật `--allow-unrestricted-file-access`, không mở cổng ra Internet.
4. Giữ cửa sổ chạy; chọn đúng tab Gemini khi extension hỏi. Cho phép kết nối trong UI. Không copy token extension vào chat hoặc repo.
5. Đặt Google credential trên máy bằng biến môi trường `GOOGLE_APPLICATION_CREDENTIALS` trỏ file riêng tư. GitHub Secret không tự có trên máy. Chia sẻ sheet và hai ảnh L/M cho service account quyền Reader; bật Drive API trong Google Cloud bên cạnh Sheets API. Export chỉ cần đọc, không sửa sheet.

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\private\little-days-service-account.json"
python run_browser.py --idea IDEA_001 --prepare-only
```

`--prepare-only` là chế độ kiểm tra kỹ thuật; chỉ upload và điền prompt, chưa gửi job. Mặc định lệnh không có cờ này chạy qua render, không cần duyệt admin:

```powershell
python run_browser.py --idea IDEA_001
```

Không chạy ví dụ render với IDEA_001 đã có kết quả. Khôi phục bằng URL kết quả thay vì tạo lại:

```powershell
python run_browser.py --idea IDEA_001 --conversation https://gemini.google.com/app/14db0bc9fa718837
```

Có thể chạy `--packet C:\path\packet.json` thay export live khi ChatGPT đã chuyển gói input có kiểm chứng lên máy. Packet chứa nguồn, URL ảnh L/M, file local và SHA256, nguyên văn prompt, AI/model/version/mode. Không chứa credential. Cùng input dùng cùng idempotency key.

## Đầu ra và xử lý lỗi

- Video: mặc định `%USERPROFILE%\Videos\TheLittleDays`, giữ tên gốc vì chưa được giao chuỗi mã video chuẩn.
- Bản browser download gốc vẫn ở Downloads.
- State: `.runtime/browser/<key>/browser-state.json`. Không commit hoặc xóa state để thử lại.
- Trạng thái `submission_uncertain`: đã ghi ý định gửi nhưng chưa xác nhận job ID; kiểm tra Chrome, cung cấp URL qua `--conversation`. Code không nhấn gửi lần hai.
- Lỗi capacity hoặc timeout: giữ job. Chỉ resume/poll hoặc đối chiếu kết quả; không tự click regenerate.
- Một conversation có nhiều video: dừng để chọn chính xác kết quả.
- Không tìm được model/mode/selector: dừng thật. Chọn đúng UI hoặc cập nhật selector sau khi quan sát; không tự fallback.
- `downloaded` chỉ có nghĩa MP4 đã tải và ghi hash, chưa có kiểm định sáng tạo. Phụ đề, diễn xuất, đúng thoại/ảnh và khả năng dùng final vẫn cần review thật.
- Kết quả adopted kiểm prompt và metadata, nhưng chưa chứng minh hình upload gốc đúng Frame 0; provenance được ghi rõ trong state.

## Chạy trên GitHub

Action `Little Days - plan input` tiếp tục chỉ đọc sheet. Render dùng máy local, không chạy trên Ubuntu GitHub-hosted vì không có Chrome profile/extension của bạn.

Chưa cài self-hosted runner hoặc lịch mới. Chỉ thêm sau khi chứng minh một lượt submit mới → job → video → QA → cập nhật kết quả đầy đủ. Việc cập nhật code trên GitHub chưa tự nâng cấp bản local; cần pull/copy phiên bản mới.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
```

Tài liệu chính thức: https://github.com/microsoft/playwright-mcp ; https://developers.google.com/workspace/sheets/api/guides/values
