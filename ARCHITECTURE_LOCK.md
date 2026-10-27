# Kiến trúc thực thi The Little Days — ĐÃ KHÓA

Ngày chốt: 27/10/2026 (Asia/Bangkok).
Chủ dự án đã yêu cầu khóa kiến trúc dưới đây vào workflow. Đây là khóa yêu cầu kiến trúc, không phải xác nhận hệ thống đã triển khai xong và không khóa các phần sáng tạo còn ở trạng thái nháp. Chỉ thay đổi kiến trúc khi có chỉ dẫn mới rõ ràng từ chủ dự án.

## Quy tắc bắt buộc

1. **GitHub quản lý toàn bộ code.** Repository này là nguồn chuẩn của code thực thi, workflow, cấu hình mẫu không chứa bí mật, prompt template, adapter và kiểm tra. Mọi code dự án tạo/sửa phải được commit vào GitHub trước khi dùng trong sản xuất. Bản trên máy thực thi là checkout/bản triển khai từ commit đã biết, không duy trì script độc lập chưa đồng bộ như một đường sản xuất khác. Thử nghiệm tạm được phép nhưng phải được ghi là thử nghiệm; tích hợp và commit trước khi đưa vào quy trình chính.

2. **ChatGPT điều phối chính.** Đọc input và trạng thái thực tế, khôi phục bước chưa hoàn tất, giao nhiệm vụ cho Gemini và công cụ phù hợp, theo dõi lượt chạy, kiểm tra bằng chứng, cập nhật Sheets và tài sản, báo blocker. Không coi lời hứa trong chat là một tích hợp đã được triển khai.

3. **Gemini hỗ trợ thực hiện.** Phân tích nguồn, hỗ trợ viết/sửa idea, kịch bản, prompt và kiểm duyệt theo nhiệm vụ do ChatGPT điều phối. Giữ quyết định trước của chủ dự án: Gemini thật có quyền quyết định biên tập cuối đối với idea và bản sửa; ChatGPT không giả lập hoặc tự ghi đè kết luận đó. Gemini viết prompt không phải bảo đảm video sẽ hết lỗi; phải kiểm tra kết quả thực tế.

4. **GitHub điều khiển các lượt chạy code.** Các tác vụ phù hợp như gọi API, xử lý dữ liệu và đồng bộ Sheets được triển khai qua GitHub Actions. Những bước cần trình duyệt đã đăng nhập có thể chạy trên máy của chủ dự án bằng self-hosted runner do GitHub Actions điều khiển. Code nằm trên GitHub không có nghĩa mọi thao tác phải chạy trên máy chủ GitHub-hosted.

5. **Máy cá nhân là nơi thực thi.** Máy thực thi chỉ chạy phiên bản code đã triển khai từ GitHub và cung cấp trình duyệt hoặc xử lý media khi cần. Không dùng việc máy online làm bằng chứng rằng Flow đã kết nối. Cài đặt self-hosted runner, cơ chế đăng nhập và adapter trình duyệt phải được thực hiện, kiểm tra riêng trước khi tuyên bố hoạt động.

6. **Sheets và Flow có vai trò riêng.** Google Sheets nhận input và hiển thị nội dung/trạng thái/liên kết đầu ra; Google Flow tạo video theo tài sản và prompt đã chốt. Đọc tiêu đề sống, bảo toàn cột admin và nguồn, không tự thay layout. D/E/F tuân theo TOOL_INTAKE_WORKFLOW.md.

7. **Khôi phục không phụ thuộc box chat.** Lưu bền vững idea ID, phiên bản input/tài sản, commit code, stage, run/job ID, review thật, kết quả, lỗi và next action. Đổi chat phải đọc trạng thái và tiếp tục, không phân tích/render lại phần đã xong hoặc gửi trùng job. Không lưu trạng thái runtime nhạy cảm vào Git công khai; dùng kho trạng thái riêng tư phù hợp và giữ liên kết đối soát.

8. **Phiên đăng nhập trình duyệt không tự chuyển giữa chat.** Khôi phục dữ liệu và khôi phục quyền điều khiển trình duyệt là hai việc khác nhau. Xác minh session hiện tại trước khi thao tác; đăng nhập bằng cơ chế bảo mật khi cần. Không mặc định chat mới là sai chế độ Work, không hứa chuyển được live browser bằng văn bản handoff.

9. **Bí mật nằm ngoài code.** Dùng GitHub Secrets hoặc secret store cục bộ phù hợp với nơi thực thi; không commit API key, cookie, password, token hoặc URL tải tạm. Không lấy secret từ log hay đưa vào chat.

10. **Không tự mở rộng quyền hoặc chi tiêu.** Kiến trúc này không tự cho phép bật billing, mua tín dụng, cấp quyền mới, đăng công khai hay bỏ qua bước xác nhận đăng nhập/điều khoản của dịch vụ.

## Trạng thái triển khai tại lúc khóa

Đã có repository, code review Gemini API và một số code browser; Gemini API review đã có lượt chạy thành công. Flow đã tạo video thật trong một phiên browser của chat, nhưng video IDEA_002 chưa đạt kiểm tra ở checkpoint đã biết.

Chưa xác minh một chuỗi đầy đủ do GitHub Actions điều khiển từ intake đến review, render, kiểm tra và lưu kết quả. Chưa xác minh self-hosted runner hoặc cơ chế khôi phục phiên Flow giữa các chat đã được cài và chạy đạt. Các script từng chạy độc lập trên máy cần được đối soát, tích hợp và commit trước khi trở thành workflow chính.

Các câu trạng thái cũ như “chưa có API key” trong snapshot lịch sử không thay thế trạng thái sống. Mọi lượt chạy phải đọc hồ sơ hiện tại trước khi quyết định bước kế tiếp.

## Tài liệu liên quan

- WL.optimus.md: workflow tổng thể và checkpoint lịch sử.
- TOOL_INTAKE_WORKFLOW.md: ba trường intake và xử lý lỗi kiểm duyệt.
- GEMINI_API_SETUP.md: cấu hình bộ kiểm duyệt API.

Không tự render hoặc tiếp tục IDEA_002 chỉ vì tài liệu kiến trúc được khóa. Tiếp tục theo phạm vi và điểm dừng mới nhất của chủ dự án.
