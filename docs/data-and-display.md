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
| Thông tin chính & Số liệu (Main Information & Figures) | summary | Xem nhanh 3 dòng; mở rộng để đọc toàn bộ |
| Bối cảnh / Nguyên nhân (Context & Background) | context | Khối nền xanh; có bản xem nhanh và nội dung đầy đủ |
| Tác động / Cơ hội & Rủi ro (Impact, Opportunities & Risks) | analysis | Khối nền vàng; giữ nguyên nội dung gộp của nguồn |
| Link bài gốc (Source URL) | sourceUrl | Nút đọc bài gốc; tên miền hiển thị nếu chưa có tên nguồn riêng |
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

## Kiểm tra

`python -m unittest discover -s tests -v` kiểm tra importer, schema song ngữ, hyperlink, ngày GMT/UTC và thumbnail. Kiểm tra trình duyệt: chạy `python -m http.server 8000 --bind 127.0.0.1 -d public`, sau đó `uv run --with playwright --with tzdata python tests/ui_smoke.py`. Script dùng Edge headless trên Windows, kiểm tra desktop/mobile, mở nội dung, tìm bối cảnh/tác động, lọc, phân trang, dark mode, dữ liệu thiếu và URL không an toàn. Ảnh QA nằm trong `.venv/ui-qa/`, không đưa lên GitHub.
