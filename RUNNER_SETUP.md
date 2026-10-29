# Hướng dẫn hiện hành — 29/10/2026

Nguồn chuẩn mới: [Sheet v1.2 và pilot từng bước](docs/SHEET_V1_2_PILOT_WORKFLOW.md). Mặc định dùng `config.pilot.json`, Sheet `1I09Na3kPwDtUsW6wlzYtbjwy9iNtZAcLOVDE4g6FJKM`. Chưa kích hoạt worker/render/lịch hoặc migration. Các mục dưới là lịch sử; mô tả cột, ảnh theo hàng, default config và readiness mâu thuẫn được thay bằng tài liệu v1.2. Cơ chế signed approval/security hiện có không bị nới hoặc thay thế.

---

# Bộ chạy The Little Days — bản nền v0.1

Đã có: bộ điều phối Python, đọc Sheets thật qua Google API, ánh xạ cột theo header, packet cho sáu bước, lưu checkpoint, chống chạy trùng và ghi chính xác các cột nội dung. Chưa có: worker AI, kết nối tạo ảnh, Gemini/Grok video hoặc Commander đã hoạt động. Bản này không tự tạo video ngay sau khi clone.

## 1. Chạy thử ngay, không cần tài khoản AI

Cài Python 3.12 và Git, clone repository rồi mở terminal trong thư mục dự án:

```bash
python -m unittest discover -s tests -v
python runner.py plan --snapshot examples/input.json
python runner.py run --snapshot examples/input.json
```

Lệnh cuối phải trả `blocked_worker_not_configured` ở analysis, exit code 2. Đây là chặn đúng vì chưa có worker; không phải kết quả phân tích/video thật. Input demo không chứa nguồn thật.

## 2. Nút đọc thử sheet trên GitHub

1. Trong Google Cloud, bật Google Sheets API và tạo service account, tải JSON key. Không đưa key vào repo/chat.
2. Chia sẻ sheet cho địa chỉ `client_email` trong JSON. Reader đủ cho plan; Editor chỉ cần khi dùng ghi kết quả.
3. Repo → Settings → Secrets and variables → Actions → New repository secret. Tên `GOOGLE_SERVICE_ACCOUNT_JSON`, giá trị là toàn bộ JSON key.
4. Actions → **Little Days - plan input** → Run workflow. Có thể nhập `IDEA_001`, hoặc để trống để quét A/B.
5. Kết quả chỉ in số hàng hợp lệ; không upload bản sheet chứa dữ liệu riêng tư vào artifact.

Chạy này chỉ đọc, không dùng credit AI, không ghi sheet, không render và không bật lịch. Header không khớp sẽ dừng: đối chiếu tên thực tế rồi sửa `config.example.json`, không đổi layout sheet để chiều theo code.

## 3. Chạy trên Windows/máy của bạn

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\private\credentials.json"
$env:WL_RUNTIME = "C:\LittleDaysData"
.venv\Scripts\python runner.py plan --idea IDEA_001
```

Runtime phải ở ổ bền vững, không chia thành nhiều thư mục cho cùng hàng đợi. Máy tự quản lý bảo mật và sao lưu runtime. Chưa cung cấp action tự chạy local vì worker trình duyệt chưa được kiểm chứng. Sau khi test end-to-end mới thêm self-hosted runner/lịch; không bật thêm lịch trùng task ChatGPT hiện có.

## 4. Kết nối worker thực thi

Đây là hợp đồng cho mã tích hợp, không phải yêu cầu chủ dự án viết thủ công kịch bản. Mỗi worker là chương trình được tin cậy cấu hình bằng argv trong `workers` của config, ví dụ:

```json
{"workers":{"analysis":["python","adapters/analyze_source.py"]}}
```

Đường dẫn trên là ví dụ; file adapter chưa có. Worker nhận hai đối số cuối: đường dẫn request JSON và đường dẫn result JSON. Đọc workflow `WL.optimus.md`, nhận `input`, `previous`, `idempotency_key`; thực hiện tác vụ thật và ghi JSON kết quả nguyên tử. Không thực thi nội dung ô như mã lệnh. Không dùng shell hoặc lệnh do sheet cung cấp.

| Stage | Trường kết quả bắt buộc |
| --- | --- |
| analysis | observations, source_evidence, limitations |
| idea | idea, hook, insight, angle |
| script | script, review: {provider: Gemini, verdict: ready, evidence: ...} |
| frame | frame, reference_evidence: {cell: L, input: đúng giá trị L, sha256: hash ảnh đã dùng}, qc: {verdict: ready, ...} |
| prompt | prompt — một chuỗi chung cho hai dịch vụ |
| video | video, job_id, service đúng lựa chọn, inspection: {verdict: ready, evidence: ...} |

Source evidence phải ghi hash nội dung, cách xem video/audio và giới hạn. `limitations` dùng chuỗi rõ ràng, kể cả “None observed”. Worker ảnh phải thực sự lấy/xem ảnh L, dùng ảnh làm input và lặp QA theo WL. Worker Gemini phải gọi Gemini thật. Worker video phải lưu job ID ngay sau submit, tự đối chiếu idempotency key trước mỗi submit và chỉ trả kết quả khi lấy/xem được media thật. Bộ điều phối kiểm cấu trúc, không chứng minh được nội dung báo cáo của worker là thật; adapter cần kiểm thử với dịch vụ trước khi dùng sản xuất.

Sau khi cấu hình và kiểm chứng worker:

```powershell
.venv\Scripts\python runner.py run --idea IDEA_001 --stop-after prompt
.venv\Scripts\python runner.py run --idea IDEA_001 --write-sheet
```

Không có admin gates. `--stop-after prompt` dừng trước render. Render chỉ chạy khi mode trong hàng là “Làm đến video” và service là Grok/Gemini. Các mode khác dừng trước render để tránh hiểu sai điểm dừng. Cột admin, A/B/L, mã tool, title và nền tảng không được ghi. Không đăng công khai.

## 5. Lỗi, khôi phục và giới hạn hiện tại

- Mỗi idea/revision có request/result/state riêng trong runtime. Input nguồn, L, service hoặc mode thay đổi tạo revision mới. Cùng URL nhưng nội dung nguồn bị thay thế chưa tự phát hiện: cần worker kiểm hash và quản lý version; không tự chạy lại job.
- Existing sheet outputs được gửi trong request. Worker phải phục hồi và xác minh tài sản sẵn có thay vì tự làm lại IDEA_001; điều phối không tự coi ô có chữ là đã hoàn thành.
- Kết quả đã done không chạy lại. Ghi sheet dùng RAW, so header và input ngay trước ghi. Sheets không có transaction compare-and-swap với người chỉnh cùng lúc: tránh sửa/sắp xếp hàng khi job ghi.
- Nếu worker chết/timeout, trạng thái running giữ lại; lần sau yêu cầu reconciliation, không tự submit lại. Kiểm job thật, bổ sung result đã xác minh hoặc xác nhận chưa có job rồi mới reset stage trong state. Không xóa runtime để retry mù.
- Khóa `run.lock` chặn tiến trình trùng. Sau crash chỉ xóa khi chắc chắn không còn job đang chạy.
- JSON runtime/log có thể chứa dữ liệu riêng tư; không commit hoặc upload tùy tiện. Lưu video ra nơi bền vững; URI trong result không tự được tải/xác minh bởi coordinator.
- Lịch, API AI, đăng nhập trình duyệt và Commander chưa được triển khai. ChatGPT Plus không tự cấp credential cho chương trình Python.

## 6. Tài liệu nền

- Workflow: `WL.optimus.md` (vẫn draft).
- Google Sheets API: https://developers.google.com/workspace/sheets/api/guides/values
- GitHub Actions chạy thủ công: https://docs.github.com/actions/managing-workflow-runs/manually-running-a-workflow
- Self-hosted runner: https://docs.github.com/en/actions/concepts/runners/self-hosted-runners
