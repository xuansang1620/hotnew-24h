# Phân tích dữ liệu và thiết kế hiển thị Bản tin 24h

Đối chiếu trực tiếp Google Sheet ngày 22/10/2026 (giờ Việt Nam). Sheet có thể thay đổi trong khi đồng bộ: lần khảo sát đầu có 22 dòng, lần nhập kiểm tra tiếp theo có 41 dòng hợp lệ. Sau khi gộp với lịch sử, dữ liệu kiểm tra gồm 64 tin, đủ ngày cập nhật, bối cảnh và tác động; 17 tin có URL ảnh. Đây là số liệu tại thời điểm kiểm tra, không phải chỉ tiêu cố định.

Nguồn: https://docs.google.com/spreadsheets/d/1BKvEFsK-SjtW0CPBylrXOWSNIo7vDEWhEFemPsOs--Y/edit

## Các cột và cách hiển thị

| Cột trong Sheet | Trường JSON | Hiển thị |
|---|---|---|
| Ngày cập nhật (Date) | collectedAt | Ngày/giờ cập nhật theo múi giờ Việt Nam, không gọi là ngày xuất bản |
| Phần (Section) | section | Bộ lọc phần tin và nhãn cuối thẻ; tên gốc được giữ trong nội dung mở rộng |
| Mục / Lĩnh vực (Category) | category | Nhãn chuyên mục, bộ lọc có số tin |
| Tiêu đề (Headline) | title | Tiêu đề hiển thị đầy đủ |
| Thông tin chính & Số liệu (Main Information & Figures) | summary | Hiển thị đầy đủ trên điện thoại/tablet (rộng tối đa 900 px), cỡ chữ 14 px trên điện thoại; desktop xem nhanh 3 dòng và mở rộng để đọc toàn bộ |
| Bối cảnh / Nguyên nhân (Context & Background) | context | Khối nền xanh; có bản xem nhanh và nội dung đầy đủ |
| Tác động / Cơ hội & Rủi ro (Impact, Opportunities & Risks) | analysis | Khối nền vàng; giữ nguyên nội dung gộp của nguồn |
| Link bài gốc (Source URL) | sourceUrl | Mở khung đọc trong trang; tên miền hiển thị nếu chưa có tên nguồn riêng |
| Thumbnail URL | imageUrl | Ảnh nhỏ khi có URL hợp lệ; không tạo ô ảnh trống |

Khảo sát 22 dòng đầu: tiêu đề dài trung vị 95 ký tự, thông tin chính 334 ký tự, bối cảnh 152 ký tự, tác động 179 ký tự. Vì nội dung dạng bản tin phân tích và ít ảnh, chọn hai cột thẻ trên desktop, một cột trên điện thoại, thay cho thẻ có vùng ảnh lớn. Không cắt tiêu đề hoặc thay số liệu gốc. Bản xem nhanh được rút bằng CSS; văn bản đầy đủ vẫn có trong nút “Đọc đầy đủ”.

## Những thay đổi có ích cho việc đọc

- Thu nhỏ masthead và đầu trang, hiển thị số tin hôm nay, tổng số tin lưu trữ và số tin có cả bối cảnh lẫn tác động. Các số đếm tổng quan tính trên toàn bộ dữ liệu; số tin phù hợp tính theo bộ lọc.
- Tìm kiếm không dấu trong tiêu đề, nội dung chính, bối cảnh, tác động, chuyên mục, phần tin và nguồn.
- Lọc theo ngày, chuyên mục và phần bản tin; mỗi lần tải 12 tin, có nút xem thêm.
- Gộp cách viết “PHẦN A – …” và “A - …” thành nhãn phần dễ đọc, không sửa giá trị gốc trong JSON. Nhãn “Tin trọng điểm” lấy từ phần A, không phải điểm quan trọng do hệ thống tự chấm.
- Mở từng thẻ hoặc mở toàn bộ nội dung; màu sáng/tối được lưu trên trình duyệt.
- Khi thiếu metadata vẫn hiển thị tin; khi thiếu ngày ghi chưa rõ ngày, không tự suy ra năm 1970.

## Sửa dữ liệu đầu vào

Script nhận thêm `Thumbnail URL` và ngày dạng `2026-10-22 14:01 GMT+7`. Ngày cập nhật được chuyển sang UTC khi lưu JSON, rồi chuyển về giờ Việt Nam khi hiển thị. URL hình và bài gốc chỉ dùng HTTP/HTTPS; nội dung Sheet được đưa vào DOM dưới dạng văn bản.

## Giới hạn nội dung cần hiểu

- Sheet chứa nhận định, số liệu, dự báo và bài tổng hợp. Hệ thống giữ nguyên nguồn, chưa kiểm chứng tính chính xác của tin, mốc sự kiện hoặc nhận định. Không tự gắn mức rủi ro, khuyến nghị đầu tư hay nhãn “đã xác minh”.
- Cột tác động đang gộp cơ hội và rủi ro trong một đoạn. Giao diện giữ nguyên đoạn này, không tự tách hoặc phân loại ý nghĩa. Nếu muốn bộ lọc riêng, nên bổ sung các cột cơ hội/rủi ro có cấu trúc tại nguồn.
- Ngày cập nhật khác ngày xuất bản bài báo. Nguồn chưa có cột ngày xuất bản riêng thì chỉ hiển thị “Cập nhật”.
- Dữ liệu tích lũy theo URL. Một URL xuất hiện nhiều dòng sẽ giữ nội dung của dòng nhập sau; dữ liệu đã bỏ khỏi Sheet vẫn có trong kho lịch sử. Nhãn phần/chuyên mục đang phản ánh một bản ghi đã gộp, không phải mọi lần URL xuất hiện trong Sheet.
- Ảnh tải từ nguồn bên ngoài có thể bị chặn hoặc hỏng; khi lỗi ảnh, thẻ vẫn hiển thị nội dung.

## Đọc bài gốc trong trang

Nút “Đọc bài gốc” mở dialog chứa iframe, không điều hướng trang chính khi nhấn thông thường. Có nút đóng, thu phóng trên desktop và khung toàn màn hình trên điện thoại. Đóng khung dừng tải iframe và giữ bộ lọc, vị trí danh sách, trả focus về liên kết đã mở. Phím Esc dùng được khi focus ở phần điều khiển của ứng dụng; phím bên trong iframe khác miền do trang nguồn xử lý.

Khung có hai chế độ: “Bài gốc” (nội dung trực tiếp từ website nguồn) và “Bản tin tổng hợp” (thông tin chính, bối cảnh, tác động từ JSON đã lưu). “Mở trang nguồn” là lựa chọn riêng, chủ động mở tab mới. Không tự mở trang ngoài nếu nhúng bị chặn. Nguồn HTTP trên website HTTPS mặc định chuyển sang bản tin tổng hợp để tránh mixed content.

Iframe bị giới hạn bằng sandbox để không tự điều hướng trang chính, mở popup hay truy cập tài nguyên nhạy cảm của ứng dụng. Nguồn cùng origin không được cấp đồng thời allow-scripts và allow-same-origin. Không lấy lại toàn văn, không dùng proxy bỏ chặn X-Frame-Options/CSP. Không thể xác nhận nguồn đã hiển thị chỉ dựa trên sự kiện iframe load: trình duyệt có thể phát sự kiện này cả khi nội dung bị chặn.

Giới hạn: website báo có thể chặn nhúng bằng X-Frame-Options hoặc CSP frame-ancestors; có thể yêu cầu đăng nhập, cookie hoặc thanh toán. Các trường hợp này vẫn cần đọc bản tin tổng hợp hoặc mở nguồn trực tiếp. Tài liệu: [MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe), [MDN X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options).

Kiểm tra riêng khung đọc: `uv run --with playwright python tests/reader_smoke.py` sau khi phục vụ public/ ở cổng 8000. Dùng nguồn thử nghiệm cho phép nhúng và nguồn trả X-Frame-Options DENY để kiểm tra hai trường hợp; không coi thử nghiệm fixture là xác nhận mọi báo đều nhúng được.

## Kiểm tra

`python -m unittest discover -s tests -v` kiểm tra importer, schema song ngữ, hyperlink, ngày GMT/UTC và thumbnail. Kiểm tra trình duyệt: chạy `python -m http.server 8000 --bind 127.0.0.1 -d public`, sau đó `uv run --with playwright --with tzdata python tests/ui_smoke.py`. Script dùng Edge headless trên Windows, kiểm tra desktop/mobile, mở nội dung, tìm bối cảnh/tác động, lọc, phân trang, dark mode, dữ liệu thiếu và URL không an toàn. Ảnh QA nằm trong `.venv/ui-qa/`, không đưa lên GitHub.
