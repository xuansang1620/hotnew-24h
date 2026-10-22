import sys
import csv
import io
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync_news import import_csv, normalize, parse_date, safe_url, recover_google_links, xlsx_source_links

HEADERS = ['Ngày cập nhật (Date)', 'Phần (Section)', 'Mục / Lĩnh vực (Category)',
           'Tiêu đề (Headline)', 'Thông tin chính & Số liệu (Main Information & Figures)',
           'Bối cảnh / Nguyên nhân (Context & Background)',
           'Tác động / Cơ hội & Rủi ro (Impact, Opportunities & Risks)', 'Link bài gốc (Source URL)']

def csv_sample(link):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    writer.writerow(['22/10/2026', 'Phần A', 'Kinh tế', 'Tin A', 'Thông tin chính', 'Bối cảnh', 'Tác động', link])
    return output.getvalue()

def xlsx_sample(formulas):
    rows = ['<row r="1"><c r="A1" t="inlineStr"><is><t>Tiêu đề (Headline)</t></is></c>'
            '<c r="B1" t="inlineStr"><is><t>Link bài gốc (Source URL)</t></is></c></row>']
    for number, formula in enumerate(formulas, start=2):
        rows.append(f'<row r="{number}"><c r="A{number}" t="inlineStr"><is><t>Tin A</t></is></c>'
                    f'<c r="B{number}" t="str"><f>{escape(formula)}</f><v>Xem nguồn</v></c></row>')
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as book:
        book.writestr('xl/worksheets/sheet1.xml',
                      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                      '<sheetData>' + ''.join(rows) + '</sheetData></worksheet>')
    return data.getvalue()

class TestSync(unittest.TestCase):
    def test_unicode(self):
        self.assertEqual(normalize('Tiêu đề'), 'tieu de')

    def test_url(self):
        self.assertEqual(safe_url('javascript:alert(1)'), '')

    def test_date(self):
        self.assertEqual(parse_date('22/10/2026 07:00'), '2026-10-22T00:00:00+00:00')

    def test_import_and_dedupe(self):
        csv_data = 'Tiêu đề,Link,Nguồn,Ngày đăng\nTin A,https://example.com/a?utm_source=x,Báo A,22/10/2026\nTin A,https://example.com/a,Báo A,22/10/2026\n'
        items, info = import_csv(csv_data, [])
        self.assertEqual(len(items), 1)
        self.assertEqual(info['sourceRows'], 2)

    def test_missing_schema(self):
        with self.assertRaises(ValueError):
            import_csv('Name,Other\na,b\n', [])

    def test_empty_is_rejected(self):
        with self.assertRaises(ValueError):
            import_csv('Tiêu đề,Link\n', [])

    def test_live_bilingual_schema(self):
        items, _ = import_csv(csv_sample('https://example.com/a'), [])
        article = items[0]
        self.assertEqual(article['title'], 'Tin A')
        self.assertEqual(article['summary'], 'Thông tin chính')
        self.assertEqual(article['category'], 'Kinh tế')
        self.assertEqual(article['collectedAt'], '2026-10-21T17:00:00+00:00')
        self.assertEqual(article['section'], 'Phần A')
        self.assertEqual(article['context'], 'Bối cảnh')
        self.assertEqual(article['analysis'], 'Tác động')

    @patch('sync_news.download')
    def test_recover_hyperlink_from_xlsx(self, download):
        download.return_value = xlsx_sample(['HYPERLINK("https://example.com/a?x=1&y=2", "Xem nguồn")'])
        recovered = recover_google_links(csv_sample('Xem nguồn'),
                                        'https://docs.google.com/spreadsheets/d/test-id/export?format=csv')
        items, _ = import_csv(recovered, [])
        self.assertEqual(items[0]['sourceUrl'], 'https://example.com/a?x=1&y=2')
        download.assert_called_once()

    def test_ambiguous_or_unsafe_hyperlinks_are_not_guessed(self):
        self.assertEqual(xlsx_source_links(xlsx_sample([
            'HYPERLINK("https://example.com/a", "Xem nguồn")',
            'HYPERLINK("https://example.com/b", "Xem nguồn")'])), {})
        self.assertEqual(xlsx_source_links(xlsx_sample(['HYPERLINK("javascript:alert(1)", "Xem nguồn")'])), {})

    @patch('sync_news.download')
    def test_plain_urls_do_not_require_xlsx(self, download):
        raw = csv_sample('https://example.com/a')
        self.assertEqual(recover_google_links(raw, 'https://docs.google.com/spreadsheets/d/test/export'), raw)
        download.assert_not_called()

if __name__ == '__main__':
    unittest.main()
