# Idea pilot v1.3 — GPT draft và Gemini rewrite

Sheet: https://docs.google.com/spreadsheets/d/1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM/edit
Schema hiện hành: tld-sheet-v1.3. C=Idea GPT, D=Idea Gemini, AF=Ý tưởng / Hook. Không chèn cột trước L: L5 giữ nguyên vị trí.
Các cột khác A/B, E/F, G–AE giữ nghĩa; production là A–AF, nhật ký giữ A–X.

## Phạm vi chủ dự án giao
- IDEA_TEST: tham chiếu video nguồn thật và bốn nhân vật L5 gồm bố, mẹ, con gái hai tuổi, Dachshund.
- GPT viết bản idea chuyển thể mới vào C. Ưu tiên ý tưởng ít hoặc không lời thoại khi câu chuyện vẫn rõ và hấp dẫn.
- Gemini thật đọc nguồn, L5, bản GPT; đánh giá, phân tích và tự viết lại đầy đủ vào D.
- Giữ nguyên C sau review. Không gắn bản GPT tự sửa dưới tên Idea Gemini.
- D/E/F/AF chỉ ghi từ nội dung Gemini chốt; lý do, verdict, version và evidence ở manifest.
- Chưa làm storyboard, Frame 0, prompt hoặc render.

## Hợp đồng code
config.pilot.json và config/sheet_v1_3.contract.json là mặc định hiện hành.
headers.gpt_idea trỏ C; headers.idea trỏ D; headers.hook trỏ AF.
Runner đưa gpt_idea vào input và revision digest để thay C làm review cũ hết hiệu lực. Idea worker ghi D thay vì ghi đè C.
Admission pilot không cho đi quá idea. Deployment vẫn CHUA_KICH_HOAT, render false, workers rỗng; đây chưa là kết nối Gemini Web đã hoạt động.
Gemini review phải có provider, verdict, evidence và response_id hoặc conversation_url; không giả lập review. Reject/thiếu bằng chứng không đi tiếp.
Các adapter API cũ giữ lịch sử, chưa tự nối vào pilot Web.

## Kiểm tra nguồn và reference
Chỉ file video có audio và ảnh thật là bằng chứng. Frame samples không xác minh audio hoặc mọi chuyển động.
Nếu chưa nghe/transcribe được nguồn, chỉ lưu GPT draft có note provisional, không tuyên bố source verified hoặc Gemini ready.
Mia giữ packet/evidence; thiếu browser được hỗ trợ thì D để trống, report blocked. Không dùng terminal để né chặn UI và không âm thầm chuyển qua API.

## Quy tắc ưu tiên
Tài liệu này thay thế phần bản đồ C/D/AF và đoạn C là bản Gemini chốt trong docs/SHEET_V1_2_PILOT_WORKFLOW.md và lịch sử cũ.
Các quy tắc L5, giữ thoại thiết yếu, checkpoint, ngân sách, signed approval, không sửa main/merge PR #1 và chưa bật lịch vẫn giữ.
