# The Little Days — Workflow V2.1

Ngày chốt kiến trúc: 29/10/2026 (Asia/Bangkok). Chủ dự án đã đồng ý triển khai bộ xử lý chạy trên Google. Trạng thái triển khai: code pilot, chưa xác nhận kết nối end-to-end.

## Nguồn chuẩn và phạm vi
V2.1 kế thừa thiết kế THE_LITTLE_DAYS_WORKFLOW_V2.md ngày 29/10/2026 và thay đường Gemini side panel ưu tiên bằng Google Apps Script + Gemini API. Đây là workflow độc lập trong workflow_v2/, không import runner cũ. Khi có xung đột, quyết định V2.1 áp dụng cho workflow mới; không tự thay đổi quy trình production cũ.

Phạm vi triển khai đầu tiên: một IDEA_TEST, từ bản GPT và source_analysis có bằng chứng đến critique + rewrite của Gemini, sau đó GPT so sánh. Render tắt; IDEA_002 giữ nguyên trạng thái dừng. Chưa triển khai Scene/Motion/Compiler hoặc QC media trong đợt pilot này.

## Vai trò đã chốt
- GPT: điều phối chính, viết idea GPT và chấm hai bản cùng rubric. GPT chọn GPT/GEMINI/NONE theo thiết kế V2; không tự cho bản Gemini thắng. Quy tắc lựa chọn này thay quy tắc lịch sử Gemini luôn quyết định cuối.
- Gemini thật: critique độc lập có beat, lý do, ảnh hưởng người xem và cách sửa; viết idea Gemini riêng. Nếu không thấy lỗi vật chất phải giải thích, không bịa lỗi. Không tự phê duyệt bản mình.
- Apps Script: thực thi trên Google; đọc Sheet và Drive bằng quyền chủ tài khoản đã cấp, gọi Gemini API, lưu phản hồi và báo cáo vào Drive, ghi bản Gemini vào vùng được cấu hình. Không phụ thuộc Mia cho pilot text.
- GitHub: nguồn chuẩn toàn bộ code, schema, kiểm thử, phiên bản triển khai; Actions kiểm tra code, không giữ runtime cá nhân hay bắt buộc điều phối từng lượt Google.
- Sheets: input và bảng trạng thái. Drive: bằng chứng nguồn, candidate, phản hồi và report riêng tư. Không tự chia sẻ công khai.
- Mia: xử lý media/UI chỉ khi giai đoạn đó cần và adapter được kiểm chứng. Không phải cầu nối bắt buộc cho Gemini text review.
- Flow/Grok: một provider render được chọn, chỉ sau QC và khi mở scope riêng.

Gemini không tự có quyền Sheets/Drive vì cùng Google. Apps Script thực hiện đọc/ghi; Gemini nhận packet giới hạn. Pilot này TEXT_ONLY và media_verified=false. Việc đọc URL không chứng minh đã xem video/L5.

## Chuỗi biên tập
Idea gốc → phân tích nguồn có bằng chứng → GPT viết idea mới → Gemini đánh giá bản GPT → Gemini viết lại độc lập → GPT chấm hai bản và chọn bản tốt hơn.

Giữ nguyên hai candidate và hash. Không ghi bản Gemini đè bản GPT. Không ghép lén thành bản thắng. QC-1: tổng >=80/100, không tiêu chí dưới 3/5, không hard fail. Trọng số: setup20, nhân quả20, payoff20, hợp gia đình15, khả thi15, US naturalness10. Một bản đạt chọn bản đó; hai bản đạt chọn điểm cao hơn, hòa thì ít rủi ro/ít phức tạp hơn; cả hai fail → NONE/NEEDS_IDEA_REVISION, không script/frame/render. Một vòng sửa có mục tiêu; tranh chấp → NEEDS_REVIEW.

## Luồng trên Google
1. GPT cung cấp idea riêng và source_analysis đã có evidence. Trong pilot source_analysis là text; không gán QC-0 media PASS.
2. Apps Script kiểm tra schema pilot, duy nhất IDEA_TEST ở hàng 2, input đầy đủ, cấu hình và khóa thực thi.
3. Hash packet bao gồm version/model/source_analysis/idea GPT. Kiểm tra state trước khi gọi.
4. Gọi Gemini một lần để critique + rewrite trong JSON có cấu trúc.
5. Lưu response gốc Drive trước validation; kiểm tra idea ID/hash/scope/critique/rewrite.
6. Đọc lại input trước ghi. Nếu input đổi giữ output ở Drive, không ghi nhầm revision.
7. Chỉ ghi D:G của pilot: idea Gemini, report link, trạng thái, hash. A:C bất biến.
8. Dừng WAITING_GPT_SELECTION; GPT đọc cả hai bản và report để chấm. Gate lựa chọn/đồng bộ kết quả sẽ được thêm sau kiểm chứng kết nối; pilot không tự đi sang sản xuất.

## State và tiết kiệm quota
Script Properties giữ state theo hash; Drive giữ raw response/report. ScriptLock ngăn các lượt trong cùng dự án chạy chồng nhau. Chỉ một Apps Script là writer; không bảo đảm giao dịch phân tán giữa nhiều dự án.

COMPLETE chạy lại dùng report, không gọi model. Input thay đổi khi đã có output → NEEDS_REVISION_RECONCILIATION; lưu bản cũ trước khi mở revision. SUBMITTING sau gián đoạn → dừng đối soát, không tự gọi lại. HTTP429 → WAITING_QUOTA, không tự đổi model/tài khoản/bật billing. HTTP503/5xx → WAITING_SERVICE. Timeout không rõ → AMBIGUOUS. Mọi retry cần đối soát và cho phép tiếp tục riêng; không có vòng retry mặc định. Phản hồi sai schema được giữ để sửa, không tự gọi model mới.

Work nhận summary ngắn; không in prompt dài, key, base64 hoặc media. Cache theo nội dung/model/prompt version; không tải lại media đã có. AI không làm hash, copy, schema hay ghép template. Không hứa số token tiết kiệm khi chưa đo.

## Những ràng buộc V2 giữ nguyên
L5 là nguồn nhận diện duy nhất cho FATHER/MOTHER/DAUGHTER/DOG. Hồ sơ visual, personality, behavior, voice, wardrobe theo episode tách observed/proposed; giọng chưa kiểm chứng không gọi là canon. Giữ thoại, speaker ownership, diễn xuất và thời lượng; không cắt thoại để ép clip. Các giai đoạn sau giữ Scene Plan → Motion Plan → structured data → deterministic compiler → Frame0/QC-2 → render → QC-3 → deliver. Chưa kiểm chứng capability thì không render. Không tự đăng công khai.

## Acceptance trước bật automation
- Cấp OAuth cho đúng tài khoản, cấu hình model/key trong Google; không đưa key vào GitHub/chat.
- Preflight đọc đúng pilot Sheet và thư mục Drive.
- Một lượt Gemini thật: có response evidence, critique, rewrite; C không đổi; D có kết quả; report Drive mở được.
- Chạy lại cùng input không phát sinh request; thay input không ghi đè revision; lỗi/quota dừng có state.
- GPT lưu phiếu chấm hai bản và winner/NONE. Hai bản fail bị chặn.
- Chỉ sau các kiểm chứng trên mới thiết kế trigger và mở rộng schema. Không bật lịch hoặc tuyên bố unattended trước đó.
