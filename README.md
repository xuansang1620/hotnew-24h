# Bản tin 24h

Website tin tức dùng Google Sheets công khai và GitHub Pages. Chạy lịch 07:25, 11:35, 17:35, 22:35 giờ Việt Nam.

## Triển khai

1. Tạo repository GitHub, push toàn bộ thư mục này vào nhánh `main`.
2. Settings → Pages → Source → GitHub Actions.
3. Actions → Đồng bộ bản tin → Run workflow.
4. Nếu đường dẫn export mặc định bị chặn, Publish to web dạng CSV và đặt Repository Variable `SHEET_CSV_URL` bằng URL CSV ấy.

Cần Python 3.11 trở lên. Cài phụ thuộc: `python -m pip install -r requirements.txt` (bổ sung dữ liệu múi giờ trên Windows).

Chạy thử: `python -m unittest discover -s tests -v`, sau đó `python scripts/sync_news.py` và `python -m http.server 8000 -d public`.

**Lưu ý:** Chưa thể xác minh schema Sheet từ môi trường này. Cần đối chiếu tiêu đề thật với `ALIASES` trong script. Không công khai thông tin nội bộ trên Sheet.
