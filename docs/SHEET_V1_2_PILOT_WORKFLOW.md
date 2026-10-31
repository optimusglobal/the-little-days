# Sheet v1.2 — quy trình pilot hiện hành

Ngày đồng bộ: 29/10/2026, Asia/Bangkok.

Sheet: https://docs.google.com/spreadsheets/d/1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM/edit
Schema: `tld-sheet-v1.2`. Đây là đặc tả và cấu hình mới, không phải chứng nhận E2E.

## Phạm vi hiện tại

Hoàn thiện Sheet và đồng bộ GitHub trước; tiếp theo chủ dự án giao từng bước cho một idea test. Sau mỗi bước phải lưu output thật, evidence và checkpoint rồi dừng. Chưa nhập IDEA_001/002, chưa bật scheduler, chưa gọi AI/browser hoặc render bằng cập nhật này.

`config.pilot.json` là mặc định mới của runner và Action plan. `config.example.json`, `config.mvp.example.json`, `examples/input.json` giữ làm fixture/luồng lịch sử, không phải nguồn sản xuất hiện hành. Không dùng legacy config để vượt trạng thái pilot chưa kích hoạt.

## Cấu trúc Sheet

- 00_HUONG_DAN: một bộ quy tắc hiện hành.
- 01_SAN_XUAT: A–AE, header hàng 4, input từ hàng 5. A/B input chủ dự án, H/K/U checkbox admin không chặn AI, L5 reference duy nhất cho mọi hàng.
- 02_CAU_HINH: cấu hình A–C; danh mục trạng thái E5:G24 gồm nhãn/mã/định nghĩa.
- 03_NHAT_KY_CHAY: A–X, log mỗi stage/attempt, capacity 10.000 hàng; production capacity 1.000 hàng.

Contract có đủ 31 headers, 59 settings và danh mục 20 trạng thái. Runtime đọc cấu hình và danh mục thật khi plan live; cấu hình hoặc schema lệch thì dừng. Plan chỉ xác minh reference URL/file ID; hash byte thật phải kiểm lại ở media stage.

## Gate và điểm dừng

Owner stop > deployment > render_enabled > Q/default_stop > prerequisites > authorization bundle > ngân sách.
Q=Làm đến video không tự cấp quyền submit. Pilot cần chỉ dẫn mới sau khi review gói script/ảnh/prompt, gắn hash phiên bản/provider/settings/segment. Thay gói làm quyền cũ không còn áp dụng. Không đổi ý nghĩa H/K/U.

Giữ `deployment_state=CHUA_KICH_HOAT`, `render_enabled=false`, workers rỗng. Runner từ chối run trước mọi worker hoặc sheet write. Chưa bật các giá trị này. Sau khi activation được triển khai/nghiệm thu, run pilot yêu cầu --idea và --stop-after cụ thể, chỉ làm một incomplete stage rồi dừng. Không tự nối các worker API cũ cho pilot Web.

Đường browser render/export cũ chưa được nghiệm thu theo v1.2 nên chặn với config pilot. Giữ signed-approval/production guards hiện tại; không nới bảo vệ hoặc xóa ledger.

## Gemini và media

Gemini Web trên Mia là ứng viên test; API tùy chọn, cả hai cần kiểm chứng thực tế. Mia gửi gói nhiệm vụ versioned, nhận/lưu phản hồi thật, kiểm tra ID/version. Không phụ thuộc Gemini tự đọc link Sheet. Không chuyển route/model tự động, tạo production keys hoặc bật billing.

Technical QC (ffprobe/ffmpeg), visual và audio/lip-sync/editorial có evidence riêng. Contact sheet chỉ lấy mẫu; silence detection không chứng minh thoại đúng. AD chỉ là QC video tổng thể. QC/API lỗi giữ file và resume review, không render lại.

## Ngân sách và khôi phục

Pilot đề xuất 1 submission/segment và 2/ngày; intent chưa rõ giữ chỗ ngân sách; prompt revision không reset cap. Enforcement ngân sách ngày và quyền bundle v1.2 chưa được triển khai/kiểm chứng nên render vẫn chặn hoàn toàn. Không coi số trong config là enforcement đã chạy.

Manifest riêng tư là nguồn chuẩn: idea/input/asset hash, stage, run/job, evidence, lỗi, next action. Một executor lock; atomic state/history/backup cần nghiệm thu. Idempotency từ byte và nội dung, không chỉ URL. Hết capacity phải mở rộng/archival, không ghi đè lịch sử.

## Migration

Chưa chạy migration. Không giả định lệnh runner.py import-legacy tồn tại. Đọc header cũ, đối soát từng asset/hash/review/dependency, tạo manifest migration. Giữ asset cũ và bản lỗi trong history; không tự gán IDEA_001 ready hoặc dùng Frame 0 cũ thay bản rebuild IDEA_002. Không chỉ copy A/B rồi chạy lại.

## Chạy kiểm tra không AI/browser

```bash
python -m unittest discover -s tests -v
python runner.py plan --config config.pilot.json --snapshot examples/pilot.input.json
```

Snapshot pilot trống idea thật nhưng có L5 và settings. Fixture test có thể thêm mã giả trong bộ nhớ, không ghi Sheet. Action live plan đọc Sheet mới; service account phải có quyền Reader hiện có hoặc được chủ dự án cấp đúng phạm vi. Chưa tự thay quyền chia sẻ.

## Trình tự tiếp theo

1. Đối soát hồ sơ đầu vào idea test khi chủ dự án yêu cầu.
2. Chứng minh Mia gửi/nhận/lưu một nhiệm vụ Gemini qua tích hợp được hỗ trợ.
3. Thực hiện script, Frame 0, prompt từng bước với output và evidence.
4. Chỉ xem xét commissioning render sau khi gói chuẩn bị và quyền rõ ràng.
5. Chưa mở lịch tự chạy, chưa tự đăng bài.

Tài liệu này thay thế hướng dẫn cột/nguồn/điểm dừng mâu thuẫn trong snapshot lịch sử. GitHub giữ toàn bộ code; không sửa main, không merge PR #1.
