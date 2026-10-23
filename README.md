# Bản tin 24h

Website tin tức dùng Google Sheets công khai và GitHub Pages. Chạy lịch 07:25, 11:35, 17:35, 22:35 giờ Việt Nam.

Giao diện gọn với thông tin chính, bối cảnh/nguyên nhân, tác động/cơ hội/rủi ro, nguồn và ngày cập nhật. Có bộ lọc phần tin, chuyên mục, thời gian và tìm kiếm toàn bộ nội dung. Xem [phân tích dữ liệu và thiết kế hiển thị](docs/data-and-display.md).

“Đọc bài gốc” mở khung đọc ngay trong trang, hỗ trợ đóng/thu phóng và đọc bản tin tổng hợp. Trang báo chỉ hiển thị trong khung nếu nguồn cho phép nhúng (không chặn bằng X-Frame-Options/CSP, không yêu cầu truy cập ngoài khung). Nếu nguồn chặn, chọn “Bản tin tổng hợp” hoặc “Mở trang nguồn”. Trình duyệt không cho xác định đáng tin cậy việc nhúng bị chặn chỉ từ sự kiện iframe load; giao diện luôn có lựa chọn dự phòng, không báo thành công chỉ vì load đã phát ra.

## Triển khai

1. Tạo repository GitHub, push toàn bộ thư mục này vào nhánh `main`.
2. Settings → Pages → Source → GitHub Actions.
3. Actions → Đồng bộ bản tin → Run workflow.
4. Nếu đường dẫn export mặc định bị chặn, Publish to web dạng CSV và đặt Repository Variable `SHEET_CSV_URL` bằng URL CSV ấy.

Cần Python 3.11 trở lên. Cài phụ thuộc: `python -m pip install -r requirements.txt` (bổ sung dữ liệu múi giờ trên Windows).

Chạy thử: `python -m unittest discover -s tests -v`, sau đó `python scripts/sync_news.py` và `python -m http.server 8000 -d public`.

Script hỗ trợ tiêu đề cột song ngữ của Sheet hiện tại. Nếu CSV chỉ xuất chữ “Xem nguồn”, script đọc thêm bản XLSX công khai để lấy URL trong công thức `HYPERLINK` hoặc hyperlink của ô; không thực thi công thức. Chỉ khôi phục khi tiêu đề khớp và xác định được duy nhất một URL. Nếu dùng nguồn CSV khác, cột link phải chứa URL HTTP/HTTPS thật.

**Lưu ý:** Sheet phải cho phép đọc công khai cả CSV và XLSX nếu sử dụng liên kết ẩn. Không công khai thông tin nội bộ trên Sheet. Nội dung tin được giữ theo nguồn, chưa được kiểm chứng biên tập.
