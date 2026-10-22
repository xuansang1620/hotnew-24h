import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync_news import import_csv, normalize, parse_date, safe_url

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

if __name__ == '__main__':
    unittest.main()
