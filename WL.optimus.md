# Hướng dẫn hiện hành — 29/10/2026

Nguồn chuẩn mới: [Sheet v1.2 và pilot từng bước](docs/SHEET_V1_2_PILOT_WORKFLOW.md). Mặc định dùng `config.pilot.json`, Sheet `1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM`. Chưa kích hoạt worker/render/lịch hoặc migration. Các mục dưới là lịch sử; mô tả cột, ảnh theo hàng, default config và readiness mâu thuẫn được thay bằng tài liệu v1.2. Cơ chế signed approval/security hiện có không bị nới hoặc thay thế.

---

# WL.optimus — The Little Days

> **Yêu cầu kiến trúc đã khóa:** Đọc và tuân thủ [ARCHITECTURE_LOCK.md](ARCHITECTURE_LOCK.md) trước khi thực thi. GitHub quản lý code và điều khiển lượt chạy; ChatGPT điều phối chính; Gemini hỗ trợ thực hiện và giữ quyền duyệt idea cuối. Máy cá nhân chỉ là nơi thực thi khi cần. Đây là yêu cầu kiến trúc đã chốt, không phải xác nhận đã triển khai đầy đủ. Các phần workflow còn nháp không tự được khóa theo.

Phiên bản: 0.1 · Snapshot ngày 26/10/2026 (Asia/Bangkok).
Trạng thái: BẢN NHÁP ĐANG HOÀN THIỆN, CHƯA KHÓA.

Đây là tài liệu handoff độc lập để khôi phục workflow trong cuộc trò chuyện hoặc môi trường khác. Đóng gói thành file không đồng nghĩa khóa quy trình, triển khai tích hợp hoặc xác nhận đã có video đầu ra.

## 1. Cách gọi lại

Đưa file này vào cuộc trò chuyện mới rồi yêu cầu:

> Đọc WL.optimus.md và tiếp tục workflow The Little Days với IDEA_XXX. Đọc dữ liệu hiện tại trong sheet, khôi phục phiên bản và tài sản đã có, rồi làm tiếp từ bước chưa hoàn tất. Chạy đến video thật, trừ khi tôi yêu cầu một điểm dừng khác.

Nếu môi trường có skill `the-little-days`, dùng skill đó cùng tài liệu này. Khi có xung đột, chỉ dẫn mới nhất của chủ dự án được ưu tiên. Đọc dữ liệu sống trước khi thao tác; không suy diễn trạng thái hiện tại từ snapshot này.

## 2. Mục tiêu và phạm vi

- Xây kênh và tăng lượt xem, sự gắn bó của khán giả Mỹ trước. POD được để lại cho giai đoạn sau khi chủ dự án yêu cầu; không dùng khả năng bán hàng làm điều kiện chặn idea hiện tại.
- Nội dung: hoạt hình 3D gia đình, những khoảnh khắc đời thường, tình cảm vợ chồng, hành trình yêu nhau và làm cha mẹ, sự ấm áp và hài hước. Không bắt buộc mọi tập phải có cú twist hoặc sản phẩm.
- Tên thương hiệu tương lai: **The Little Days**. Chưa xác minh username; không tự đổi tên hoặc username các kênh hiện có.
- ChatGPT là tác giả và bộ điều phối. Gemini thật tham gia phân tích, phản biện và kiểm định tại các bước cần thiết.
- Đầu vào chính: cột A và B trong Google Sheets. Đầu ra mục tiêu: video thực sự đã tạo, có bằng chứng kết quả và phiên bản tài sản đi kèm.
- Trao đổi với chủ dự án bằng tiếng Việt. Thoại, prompt, phụ đề và nội dung hướng tới người xem dùng US English.
- Workflow này tách biệt với DLH gốc. Không nhập lại các cổng duyệt hoặc hạn chế của DLH cũ.

## 3. Nguồn dữ liệu

Sheet: https://docs.google.com/spreadsheets/d/1MfErcyvRQSWS7kABIyq3_ljzI1keZ4HRl1Ngh3n-Cag/edit

ID: `1MfErcyvRQSWS7kABIyq3_ljzI1keZ4HRl1Ngh3n-Cag`.

Các tab đã quan sát: `00_HUONG_DAN`, `01_SAN_XUAT`, `02_US_POD`, `03_DANG_DO_LUONG`.
Tab sản xuất: `01_SAN_XUAT`, gid 0. Lần đọc gần nhất có tiêu đề ở hàng 4 và dữ liệu bắt đầu hàng 5. Tên file còn chứa “US POD”; điều đó không thay đổi mục tiêu hiện tại.

Trước mỗi lần chạy:

1. Đọc metadata, tiêu đề cột và toàn bộ hàng mục tiêu.
2. Ánh xạ đầu ra theo ý nghĩa tiêu đề hiện tại; chủ dự án có thể đổi layout.
3. Ngoại lệ bắt buộc: **cột L là nguồn ảnh nhận diện nhân vật duy nhất**. Nếu tiêu đề hoặc dữ liệu L mâu thuẫn với vai trò này, dừng phần tạo ảnh để làm rõ.
4. Không sửa layout, thêm cột, tạo bộ lọc, sửa A/B hoặc checkbox admin trong một lượt sản xuất.

### Bản đồ cột đã quan sát — cần xác minh lại khi chạy

| Cột | Vai trò |
| --- | --- |
| A | Mã idea nội bộ — chủ dự án nhập |
| B | Link video gốc — chủ dự án nhập |
| C | Idea mới |
| D | Ý tưởng / Hook |
| E | Insight |
| F | Proposed Angle — US |
| G | Mã idea từ tool — không tự bịa |
| H | Admin duyệt idea — chủ dự án tự quản lý |
| I | Hook đã chọn |
| J | Kịch bản / Storyboard |
| K | Admin duyệt kịch bản — chủ dự án tự quản lý |
| L | Ảnh tham chiếu nhân vật duy nhất |
| M | Frame 0 |
| N | Một prompt video chung |
| O | AI tạo video |
| P | Phiên bản |
| Q | Chế độ / điểm dừng |
| R | Trạng thái sản xuất |
| S | Trạng thái / phản hồi từ tool — không giả lập phản hồi |
| T | Mã video — khác mã idea |
| U | Admin duyệt video final — chủ dự án tự quản lý |
| V, W | Title, Hashtag |
| X–AA | Instagram, Facebook, YouTube, TikTok |

Các cột chứa raw/final video từng bị thay đổi hoặc xóa. Nếu không có chỗ lưu phù hợp, giao file/link ở chat; không ghi đè Title hoặc tự thiết kế lại sheet.

## 4. Nhân vật và nhận diện

- Bố mẹ trẻ khoảng 25–35 tuổi.
- Con gái khoảng hai tuổi: gương mặt dễ thương, tỷ lệ cơ thể và lời nói đúng tuổi toddler.
- Một chú chó Dachshund.
- Phong cách: hoạt hình 3D nguyên bản, giữ cùng danh tính và tỷ lệ giữa các tập.
- Chưa khóa tên riêng hoặc giọng nói; tạm dùng Mom, Dad, Daughter, Dog.
- **Ảnh thật được truy xuất từ L quyết định nhận diện.** Mô tả chữ, ảnh ở chat cũ, ảnh đóng gói trong skill, nhân vật video gốc hoặc Frame 0 của tập trước không được thay thế ảnh này.
- Mỗi lần tạo hoặc sửa Frame 0 đều phải xem ảnh L và truyền chính ảnh đó vào công cụ tạo ảnh. Nếu L không truy cập được, trống hoặc chứa tham chiếu mâu thuẫn, ghi rõ blocker; không tự chọn ảnh thay.

## 5. Sáu bước sản xuất tự động

### Bước 1 — Đọc input và phân tích video gốc

Đọc A/B, lấy đúng video của hàng. Phải xem được nội dung video và nghe hoặc phân tích âm thanh trước khi khẳng định câu chuyện, lời thoại.

Ghi nhận: thời lượng/tỷ lệ khung hình thực tế nếu đo được; bối cảnh; nhân vật; mở đầu; từng nhịp và thời gian; lời thoại cùng mức chắc chắn; biểu cảm, cử chỉ; máy quay; âm thanh; kết thúc và khả năng nối vòng.

Tách quan sát thực tế khỏi giả thuyết về lý do hấp dẫn. Nếu chỉ lấy mẫu frame hoặc không nghe được audio, ghi rõ giới hạn. Không phân tích nội dung chỉ từ URL, tên file hay thumbnail. Chỉ dùng comment, like, share khi đã được cung cấp hoặc thực sự truy xuất; không bịa chỉ số hoặc tỷ trọng khán giả Mỹ.

Đầu ra: bản phân tích nguồn có dẫn đến file/link và các giới hạn cụ thể.

### Bước 2 — Viết Idea mới và cập nhật các cột nội dung

Viết **Idea mới** trước, rồi mới suy ra ba trường còn lại. Idea có thể giữ cấu trúc/tình huống gốc hoặc scale thành biến thể phù hợp gia đình. Không ép đổi twist nếu làm yếu nội dung.

| Trường | Yêu cầu |
| --- | --- |
| Idea mới | Kể rõ câu chuyện được chuyển thể, gồm mở đầu, diễn biến và kết thúc |
| Ý tưởng / Hook | Tình huống và lý do người xem muốn theo dõi |
| Insight | Cảm xúc hoặc mâu thuẫn đời thường cụ thể, động cơ đồng cảm/chia sẻ |
| Proposed Angle — US | Bối cảnh Mỹ hợp lý, vai diễn trong gia đình, điểm giữ và thay so với nguồn |

Đánh giá độ phù hợp Mỹ qua sinh hoạt, lời nói, mối quan hệ và sự dễ hiểu trong văn hóa Mỹ. Nghiên cứu các khẳng định văn hóa chưa chắc chắn hoặc có tính thời sự. Không coi cờ Mỹ, khuôn mẫu hoặc thoại tiếng Anh là bằng chứng sẽ được phân phối tới người dùng Mỹ; không đảm bảo viral.

### Bước 3 — Chọn hook và viết kịch bản theo thời gian

Chuẩn bị 3–5 hook khác nhau với lý do ngắn; AI tự chọn trong phạm vi được giao. Chỉ trình option nếu chủ dự án yêu cầu.

Storyboard phải có: **thời gian | khung hình | hành động và diễn xuất | người nói và thoại chính xác | âm thanh/text**.

Yêu cầu:

- Mở đầu cho thấy ngay đang ở đâu, ai gặp tình huống gì.
- Dùng US English tự nhiên, câu ngắn, toddler nói đúng tuổi.
- Mô tả biểu cảm, ánh mắt, tư thế, cử động nhỏ và thời gian phản ứng; tránh chỉ ghi lời thoại.
- Chọn thời lượng ngắn nhất vẫn đủ diễn và nghe rõ. Khoảng 10 giây là mặc định tham khảo; 8/10/15 giây phải theo kịch bản và khả năng công cụ.
- Payoff được chuẩn bị bằng setup; không lộ quá sớm.
- Ghi phiên bản, dàn nhân vật, bối cảnh, thời lượng, mục tiêu 9:16 và nhịp cảm xúc.

Gemini phản biện các rủi ro văn hóa, lời thoại, logic, diễn xuất và tính khả thi; ChatGPT sửa các lỗi cụ thể.

### Bước 4 — Tạo Frame 0 và lặp self-QC

Frame 0 là **ảnh bắt đầu video trước hành động chính**, không phải poster, ảnh minh họa nội dung hoặc khung hình punchline.

Quy trình: lấy và xem ảnh L → tạo ảnh với ảnh L làm đầu vào nhận diện → xem ảnh kết quả → đối chiếu với ảnh L, nguồn và opening của kịch bản → sửa lỗi → xem lại.

Checklist: đúng mặt/tuổi/tỷ lệ; trang phục; số nhân vật; giải phẫu Dachshund; tay và đạo cụ; bố cục dọc; trạng thái hành động ban đầu; chỗ trống cho phụ đề; không xuất hiện payoff trước thời điểm.

Tối đa hai vòng sửa có mục tiêu cho mỗi lượt tự động. Nếu vẫn còn lỗi đáng kể, nêu đúng lỗi và trạng thái chưa đạt; không gọi bản đó là final. Hiển thị ảnh thật trong chat, lưu link/file và gắn với phiên bản kịch bản.

### Bước 5 — Tạo một prompt video chung

Tạo **một prompt canonical bằng US English**, dùng cùng kịch bản và cùng Frame 0 cho Grok hoặc Gemini. Lưu một lần ở trường prompt; không tự tạo hai bản có thoại hoặc diễn biến khác nhau.

Prompt gồm: opening; nhân vật và người nói; các nhịp theo thời gian; thoại nguyên văn; giọng/nhịp nói; nét mặt/cử chỉ; máy quay; môi trường/ánh sáng; âm thanh; ending/loop; ràng buộc liên tục và tránh thoại thừa/đổi nhân vật/lộ payoff sớm.

Cài duration, resolution và chế độ theo UI thực tế của từng dịch vụ. Mục tiêu dọc 9:16; 720p/10s là cấu hình từng test, không phải cam kết mọi tool hỗ trợ. Nếu có bất tương thích thật sự, ghi rõ thay vì âm thầm fork prompt.

Yêu cầu phụ đề từng câu được giữ trong hồ sơ. Ưu tiên dựng sub khớp audio thực tế; không mặc định chữ do model tạo sẽ đúng. Nếu chưa có bước hậu kỳ được thực hiện thì giao raw và ghi rõ sub chưa hoàn tất; không gọi SRT là video đã gắn sub.

### Bước 6 — Tạo video và giao kết quả thực tế

Đọc AI được chọn trong sheet hoặc yêu cầu mới nhất. Nếu chưa chọn, làm rõ trước khi dùng lượt/credit. Chỉ chạy cả Grok và Gemini khi được yêu cầu.

1. Mở đúng dịch vụ bằng tích hợp được hỗ trợ hoặc trình duyệt đã được cho phép.
2. Đăng nhập đúng tài khoản bằng cơ chế bảo mật được hỗ trợ; không xin mật khẩu trong chat hoặc ghi bí mật vào file.
3. Chọn đúng model/mode, chế độ video và cài đặt được hỗ trợ.
4. Upload chính Frame 0 của phiên bản đang dùng.
5. Dán prompt canonical tương ứng và gửi tạo video.
6. Theo dõi job có thật; tránh submit lặp khi job đang chạy hoặc đã hoàn thành.
7. Xác minh có kết quả video; kiểm tra thực tế các lỗi lớn về cảnh, nhân vật, thoại, diễn xuất và nhịp. Ghi các phần chưa kiểm được.
8. Giao video/file/link thật, tên dịch vụ, phiên bản ảnh/prompt và bằng chứng job/kết quả. Không coi trạng thái đã gửi là đã tạo xong.

Khi có lỗi dịch vụ, giữ nguyên tài sản đã đạt, ghi thông báo lỗi và bước kế tiếp. Không suy rộng một lần lỗi thành toàn dịch vụ quá tải. Không âm thầm đổi tool/model/kịch bản.

Hậu kỳ mở rộng như export có phụ đề, dựng nhạc, nhiều bản final được thực hiện khi có phạm vi và công cụ phù hợp. Ghi rõ raw/final, không gọi sản phẩm chưa hoàn tất là final.

## 6. Cơ chế kiểm định với Gemini

- Dùng Gemini thực sự; không đóng vai Gemini hoặc đổi tên một agent ChatGPT thành Gemini.
- Gửi gói tối thiểu: brief dự án, quan sát nguồn cùng giới hạn, phiên bản cần kiểm và ảnh/video liên quan. Không gửi dữ liệu riêng tư không liên quan.
- Yêu cầu verdict `ready / revise / insufficient-evidence`, phát hiện gắn với cảnh/câu cụ thể, mức độ và cách sửa.
- Các điểm kiểm: hiểu nguồn, phù hợp US, logic kịch bản, thoại, tuổi toddler, Frame 0, prompt và video thực tế khi có thể.
- Tối đa hai vòng sửa tự động mỗi giai đoạn; báo bất đồng còn tồn tại cùng nhận định của ChatGPT.
- Nếu Gemini không truy cập được, ghi `pending/unavailable`; có thể tiếp tục soạn độc lập nhưng không tuyên bố đã kiểm định kép. Để tuyên bố bước đã được Gemini duyệt cần kết quả thật hoặc chủ dự án miễn bước này rõ ràng.
- Phản biện nằm trong hồ sơ thực thi, không thêm cột Gemini vào sheet.

## 7. Tự chủ, điểm dừng và thao tác ngoài phạm vi

**Không chờ admin duyệt trong workflow sản xuất AI.** Chủ dự án tự điền các cột admin; AI để nguyên. Giá trị trống/FALSE/chưa tích không được chặn viết kịch bản, tạo ảnh hoặc tạo video. Không tự thêm cổng duyệt idea/ảnh/prompt.

Tôn trọng điểm dừng được yêu cầu rõ ràng. Cụm “dừng trước render” hoặc “dừng ở bước tạo video” được hiểu là chuẩn bị xong nhưng chưa gửi job tạo video.

Các blocker thật: thiếu video nguồn, ảnh L không dùng được, thiếu quyền truy cập, yêu cầu đăng nhập/CAPTCHA cần người dùng, công cụ không hỗ trợ hoặc lỗi dịch vụ. Báo đúng blocker, không giả lập hoàn tất.

FreeTraffic đang hoãn thao tác. Quy trình duyệt trong tool là quy trình riêng; các bảng 2/3 và tích hợp đầy đủ chưa được kiểm chứng. Không tự nộp idea vào tool.

Đăng lên nền tảng là bước cuối **sau video và kiểm định**, chỉ thực hiện khi được cho phép riêng. “Tạo video” không bao gồm quyền đăng công khai.

## 8. Quét hằng ngày và chống xử lý trùng

Chủ dự án điền A = mã idea, B = video nguồn. Khi chạy, đọc dữ liệu hiện tại, xử lý hàng hợp lệ cũ trước, bỏ qua hàng hoàn tất không đổi.

So sánh mã idea, link/phiên bản nguồn, phiên bản tài sản và job hiện có. Khôi phục bước chưa xong; không tạo lại từ đầu hoặc submit lại job chỉ vì đổi cuộc trò chuyện. Input thay đổi phải có phiên bản mới, giữ bản cũ.

Lịch đã ghi nhận: “Quét input Little Days”, khoảng 09:00 hằng ngày theo Asia/Bangkok; task ID `6adf246a23048191801078b53f16e2d6`.

**Phạm vi lịch đã cấu hình chỉ tới phân tích nguồn, C/D/E/F và kịch bản.** Chưa xác nhận chuỗi tạo ảnh → đăng nhập → render → lưu video chạy không giám sát. Kiểm tra trạng thái lịch hiện tại trước khi sửa; không tạo task trùng. Chỉ mở rộng tự động hóa khi kết nối, lưu đầu ra và một lượt chạy đầy đủ đã được kiểm chứng.

## 9. Hồ sơ thực thi và tên file

Mỗi idea cần lưu: mã nội bộ; nguồn và phiên bản; quan sát/giới hạn; idea mới; script/version; ảnh L đã dùng; Frame 0; prompt; AI/model/cài đặt; phản biện Gemini; lỗi và sửa; job/result; trạng thái từng bước; bước kế tiếp.

- Mã idea nội bộ, mã idea/script do tool cấp và mã video là ba loại khác nhau.
- Không tự bịa mã do tool cấp hoặc chuỗi mã video chuẩn của chủ dự án.
- Tên video: `YYYYMMDD-VIDEO_CODE`, ngày theo Asia/Bangkok; thêm suffix raw/final/version khi cần.
- Ví dụ quy tắc lịch sử: `20261017-DLH-TEST-01`; không dùng tiền tố DLH cho dự án mới nếu chưa được chọn.
- Lưu tài sản và hồ sơ bền vững. Không dựa vào đường dẫn scratch cũ như một nguồn chắc chắn tồn tại.
- Không lưu password, cookie, token hoặc bí mật đăng nhập trong tài liệu/skill/GitHub.

## 10. Điểm khôi phục IDEA_001 tại thời điểm đóng gói

Đây là checkpoint lịch sử, cần đọc lại hàng hiện tại trước khi tiếp tục:

- Video nguồn đã xem: khoảng 15,045 giây, 720×1280, 24 fps, có audio.
- Đã phân tích bằng Gemini thật và sửa kịch bản sang bản 8 giây.
- Thoại bản v2: con “Mommy first!” → “Daddy last!”; bố “I cooked it!”; con “Good job, Daddy!”; cuối có phản ứng của bố mẹ.
- Frame 0 đã tạo từ ảnh L, bản v1: https://drive.google.com/file/d/1xK83PFSCQMOGcotNWceRYkg4DdPqJrJh/view
- Script v2 / Frame 0 v1 / prompt v1 đã lưu trong hàng idea. Khôi phục prompt nguyên văn từ sheet; đoạn tóm tắt này không thay thế prompt.
- Chưa có video đầu ra được xác minh. Lần gửi Gemini trước báo full capacity. Lần chọn “4 Argon” sau đó dùng regenerate trên phản hồi cũ cũng trả lỗi; chưa phải bằng chứng về một job Argon mới độc lập.
- Nếu tiếp tục theo yêu cầu Argon: tạo chat mới → chọn đúng “4 Argon” trước → chọn Video → upload Frame 0 → đặt 9:16/cài đặt được hỗ trợ → gửi prompt đã lưu. Không chỉ regenerate lỗi cũ.
- Chat đã dùng: https://gemini.google.com/app/14db0bc9fa718837 ; có thể cần truy cập lại bằng đúng tài khoản được cho phép.

## 11. GitHub và Remote Desktop Commander — chưa triển khai

- Chủ dự án muốn GitHub để lưu/phiên bản hóa skill, prompt và mã workflow, đồng thời muốn Remote Desktop Commander (“Use your computer from chat”) để thao tác trên máy.
- Chưa xác minh nhà phát triển, quyền, cách cài và khả năng của Commander. Chưa xác nhận kết nối hoạt động hoặc có quyền truy cập máy từ chat hiện tại.
- Không đồng nhất Commander với mục Remote Connections của ChatGPT/Codex.
- Chưa có cơ sở kết luận Commander giảm token, credit render hoặc CPU/RAM. Chỉ đánh giá bằng thử nghiệm sau khi xác minh chức năng.
- Việc có GitHub hoặc Commander không tự triển khai chuỗi video tự động. Cần kiểm chứng một idea xuyên suốt, lấy được video và lưu được đầu ra trước khi tuyên bố hoạt động.

## 12. Checklist khi mở lại

1. Đọc file và chỉ dẫn mới nhất; giữ trạng thái draft.
2. Nạp skill The Little Days nếu có; không chạy DLH gốc.
3. Đọc sheet hiện tại và đúng hàng được yêu cầu.
4. Khôi phục nguồn, ảnh L, phiên bản, job và kết quả sẵn có.
5. Chọn bước chưa hoàn tất sớm nhất, tránh làm lại việc đã đạt.
6. Tiến hành trong phạm vi tới video thật, không chờ checkbox admin.
7. Giao tài sản có thật, ghi blocker và bước tiếp theo nếu chưa xong; không tuyên bố các tích hợp chưa được kiểm chứng.


## 13. Cập nhật triển khai v0.2 — 27/10/2026

- GitHub đã kết nối repo riêng tư `optimusglobal/the-little-days`; WL này được lưu phiên bản bằng commit. Chat thay đổi chưa tự đồng bộ file/skill/code.
- Action đọc thử Sheets đã chạy thành công với `eligible_rows: 1`; không có lịch render mới.
- Commander đã kết nối máy Mia. Playwright MCP/extension đã đọc được tab Gemini đang đăng nhập và thao tác nút tải video.
- Kết quả IDEA_001 trong conversation `14db0bc9fa718837` có video thật: DOM báo 720×1280, 10.005 giây; đã tải MP4 về Downloads. Chưa QA nội dung/thoại/phụ đề; không coi là final đạt.
- Bổ sung code `browser_video.py`, `export_browser_packet.py`, `run_browser.py`, `start-browser.cmd` và hướng dẫn `BROWSER_SETUP.md`: xử lý hàng đã có Frame 0/prompt, hash ảnh L/M, một prompt, giữ job khi lỗi, tải raw và QA pending.
- Chưa chứng minh một job mới đi trọn upload → submit → render → download bằng bộ code. Worker các bước phân tích/biên kịch/tạo ảnh/review trong runner và adapter Grok vẫn chưa kết nối tự động. Tiếp tục theo hồ sơ thực thi, không gửi lại job IDEA_001 đã có kết quả.
- Playwright phải khởi động trong thư mục dự án để upload chỉ trong phạm vi đó. Không mở quyền file toàn máy hoặc cổng Internet. Giữ xác nhận kết nối tab của extension.


## 14. Chỉ dẫn ưu tiên — Gemini quyết định idea cuối cùng (27/10/2026)

Phần này thay thế mọi chỉ dẫn cũ mâu thuẫn về quyền quyết định idea và chat kiểm duyệt. Chủ dự án đã xác nhận cho phép lưu cập nhật này vào GitHub.

- ChatGPT viết bản nháp Idea mới sau khi phân tích nguồn. Chưa chuyển sang sản xuất tiếp theo cho tới khi Gemini thật kiểm duyệt và chốt.
- Chỉ sử dụng đúng conversation do chủ dự án chỉ định: https://gemini.google.com/app/28109bf28700e364 . Kiểm tra URL thực tế trước mỗi lần gửi; không tự mở chat mới hoặc dùng conversation khác thay thế.
- Gửi nguồn, quan sát và giới hạn xác minh audio, bản Idea mới cùng nội dung liên quan để Gemini quyết định: DÙNG / SỬA / KHÔNG DÙNG. Thiếu bằng chứng thì giữ pending.
- Nếu SỬA, chính Gemini viết lại đầy đủ Idea mới và các trường nội dung bị ảnh hưởng. Ghi nguyên văn bản Gemini chốt vào đúng hàng/cột hiện tại trên Sheets. ChatGPT có thể thao tác ghi thay khi Gemini không có quyền ghi trực tiếp, nhưng không tự biên tập lại hoặc tuyên bố Gemini đã trực tiếp sửa Sheets.
- Nếu KHÔNG DÙNG, lưu kết luận và lý do, không triển khai idea đó. Bản thay thế cũng phải được Gemini chốt.
- Quyết định biên tập của Gemini là quyết định cuối cùng trong phạm vi yêu cầu chủ dự án; ChatGPT không ghi đè bằng đánh giá riêng. Hết vòng sửa mà chưa chốt thì giữ pending, không tự coi là được duyệt.
- Lưu phản hồi thật, URL conversation, phiên bản và nội dung cuối trong hồ sơ thực thi. Không thêm cột hoặc sửa checkbox admin.
- Áp dụng cho IDEA_002 đang dang dở và các idea tiếp theo; giữ nguyên các bước đã hoàn tất không bị ảnh hưởng.
- Ảnh tham chiếu duy nhất cho toàn bộ nhân vật là L5, kể cả các hàng idea khác; L6 trống không phải blocker.
- Giữ đầy đủ thoại và thời gian diễn; mục tiêu video mới hay hơn hoặc ít nhất ngang video nguồn. Không cắt thoại để ép thời lượng. Nếu Gemini không đủ thời lượng, chia hai video khi có thể giữ đầy đủ thoại và liên tục; hỏi chủ dự án trước khi đổi sang Grok.
- Khi cần chủ dự án phản hồi, cung cấp lựa chọn bấm có sẵn thay vì yêu cầu gõ.


## 15. Chuyển kiểm duyệt idea sang Gemini API — 27/10/2026

Chủ dự án đã chọn tự động hóa lâu dài bằng Gemini API và xác nhận cho phép lưu cập nhật API vào repo này. Phần này thay thế yêu cầu bắt buộc dùng box Gemini ở mục 14 cho bước kiểm duyệt idea; box cũ chỉ là lịch sử, không được tuyên bố phản hồi API xuất hiện ở đó.

- Gemini vẫn quyết định biên tập cuối cùng. Gửi video nguồn thực tế bao gồm audio, bản nháp và brief dự án; nhận verdict use/revise/reject/insufficient_evidence cùng transcript, giới hạn và bản viết lại.
- Chỉ triển khai tiếp khi Gemini duyệt bản gốc hoặc chốt rõ bản do Gemini sửa. Nội dung cuối ghi nguyên văn vào đúng trường Sheets sau khi kiểm tra hàng và header. Không ghi đè A/B, ảnh L5 hoặc checkbox admin.
- Ảnh tham chiếu duy nhất vẫn là L5. Giữ đầy đủ thoại và thời gian diễn; không cắt thoại để ép thời lượng. Nếu cần đổi dịch vụ tạo video sang Grok, hỏi chủ dự án trước.
- Bộ gọi độc lập: gemini_idea_review.py; hướng dẫn: GEMINI_API_SETUP.md. Code đã đặt trên Mia và lưu GitHub; năm kiểm tra logic duyệt đã đạt. Chưa có lượt gọi Gemini API thành công được xác minh.
- Trạng thái cấu hình: Python trên Mia chưa tìm thấy API key khả dụng. Cần cấu hình GEMINI_API_KEY cục bộ, xác minh model hỗ trợ video/JSON và quota trước khi gọi review thật. Không suy ra key hợp lệ từ kiểm tra biến môi trường đơn thuần.
- Bản này chưa tự nối vào runner hoặc lịch hằng ngày, chưa tự ghi Sheets và chưa thay thế công cụ tạo video. Không coi việc đặt code là hệ thống tự động hoàn tất. IDEA_002 giữ pending ở bước xác minh audio và Gemini kiểm duyệt.
- Không lưu API key trong GitHub, Sheets, chat hoặc packet. Lưu phản hồi gốc, model, response ID khi có, hash đầu vào và bản chốt ở hồ sơ local riêng tư. Không tự retry khi yêu cầu trước chưa được đối soát.
