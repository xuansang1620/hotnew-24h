"""Public Google Sheet CSV -> validated, deduplicated JSON; Python 3.11+."""
import csv
import hashlib
import io
import json
import os
import posixpath
import re
import sys
import tempfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'public/data'
DEFAULT_URL = 'https://docs.google.com/spreadsheets/d/1BKvEFsK-SjtW0CPBylrXOWSNIo7vDEWhEFemPsOs--Y/export?format=csv&gid=0'
ALIASES = {
    'title': ['title', 'tieu de', 'tieu de tin', 'headline', 'ten bai viet', 'Tiêu đề (Headline)'],
    'summary': ['summary', 'tom tat', 'noi dung', 'description', 'mo ta', 'Thông tin chính & Số liệu (Main Information & Figures)'],
    'sourceUrl': ['url', 'link', 'link goc', 'link bai viet', 'source url', 'duong dan', 'Link bài gốc (Source URL)'],
    'source': ['source', 'nguon', 'nguon tin', 'bao', 'ten bao'],
    'category': ['category', 'chuyen muc', 'linh vuc', 'chu de', 'nhom tin', 'Mục / Lĩnh vực (Category)'],
    'section': ['section', 'Phần (Section)'],
    'context': ['context', 'Bối cảnh / Nguyên nhân (Context & Background)'],
    'region': ['region', 'khu vuc', 'pham vi'],
    'publishedAt': ['published at', 'ngay dang', 'ngay xuat ban', 'thoi gian dang'],
    'collectedAt': ['collected at', 'ngay thu thap', 'thoi gian thu thap', 'ngay cap nhat', 'Ngày cập nhật (Date)'],
    'imageUrl': ['image url', 'hinh anh', 'thumbnail', 'anh'],
    'analysis': ['analysis', 'phan tich', 'nhan dinh', 'tac dong', 'Tác động / Cơ hội & Rủi ro (Impact, Opportunities & Risks)'],
}

def normalize(s):
    s = unicodedata.normalize('NFKD', str(s or '').replace('đ', 'd').replace('Đ', 'D'))
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in s if not unicodedata.combining(c)).lower()).strip()

def safe_url(s):
    s = (s or '').strip()
    p = urlparse(s)
    return s if p.scheme in ('http', 'https') and p.netloc and not p.username and not p.password else ''

def canonical(s):
    p = urlparse(s)
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(('utm_', 'fbclid', 'gclid'))]
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), '', urlencode(query), ''))

def parse_date(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError:
        d = None
        for fmt in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                d = datetime.strptime(s, fmt)
                break
            except ValueError:
                pass
    if d is None:
        return None
    return d.replace(tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')).astimezone(timezone.utc).isoformat() if not d.tzinfo else d.astimezone(timezone.utc).isoformat()

def mapping(headers):
    lookup = {normalize(h): h for h in headers if h}
    return {key: next((lookup[normalize(a)] for a in aliases if normalize(a) in lookup), None) for key, aliases in ALIASES.items()}

def download(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'BanTin24h/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(12_000_001)
    if len(data) > 12_000_000:
        raise ValueError('Dữ liệu nguồn vượt giới hạn 12 MB')
    return data

def xlsx_source_links(data):
    """Read literal HYPERLINK URLs without evaluating spreadsheet formulas."""
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    candidates = {}
    with zipfile.ZipFile(io.BytesIO(data)) as book:
        if sum(item.file_size for item in book.infolist()) > 60_000_000:
            raise ValueError('XLSX giải nén vượt giới hạn 60 MB')
        shared = []
        if 'xl/sharedStrings.xml' in book.namelist():
            shared = [''.join(item.itertext()) for item in ET.fromstring(book.read('xl/sharedStrings.xml'))]
        for name in book.namelist():
            if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name):
                continue
            root = ET.fromstring(book.read(name))
            links = {}
            relpath = posixpath.join(posixpath.dirname(name), '_rels', posixpath.basename(name) + '.rels')
            if relpath in book.namelist():
                rels = {r.get('Id'): r.get('Target', '') for r in ET.fromstring(book.read(relpath))
                        if r.get('Type', '').endswith('/hyperlink') and r.get('TargetMode') == 'External'}
                for link in root.findall('.//s:hyperlink', ns):
                    rid = link.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    links[link.get('ref')] = rels.get(rid, '')
            headers = None
            for row in root.findall('.//s:sheetData/s:row', ns):
                values, urls = {}, {}
                for cell in row.findall('s:c', ns):
                    ref = cell.get('r', '')
                    col = re.sub(r'\d', '', ref)
                    value = cell.findtext('s:v', default='', namespaces=ns)
                    if cell.get('t') == 's':
                        value = shared[int(value)]
                    elif cell.get('t') == 'inlineStr':
                        value = ''.join(cell.find('s:is', ns).itertext())
                    values[col] = value.strip()
                    formula = cell.findtext('s:f', default='', namespaces=ns)
                    match = re.match(r'^\s*=?HYPERLINK\s*\(\s*"((?:[^"]|"")*)"\s*[,;]', formula, re.I)
                    urls[col] = safe_url(match.group(1).replace('""', '"') if match else links.get(ref, ''))
                if headers is None:
                    header_map = mapping(values.values())
                    if header_map['title'] and header_map['sourceUrl']:
                        headers = {key: next(col for col, value in values.items() if value == header_map[key])
                                   for key in ('title', 'sourceUrl')}
                    continue
                title = values.get(headers['title'], '')
                url = urls.get(headers['sourceUrl']) or safe_url(values.get(headers['sourceUrl'], ''))
                if title and url:
                    candidates.setdefault(title, set()).add(url)
    # An ambiguous title must never be assigned a guessed source URL.
    return {title: next(iter(urls)) for title, urls in candidates.items() if len(urls) == 1}

def recover_google_links(csv_text, url):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
    cols = mapping(reader.fieldnames or [])
    rows = list(reader)
    parsed = urlparse(url)
    sheet = re.match(r'^/spreadsheets/d/([A-Za-z0-9_-]+)/', parsed.path)
    if (parsed.hostname != 'docs.google.com' or not sheet or not cols['title'] or not cols['sourceUrl']
            or not any(not safe_url(row.get(cols['sourceUrl'])) for row in rows)):
        return csv_text
    links = xlsx_source_links(download(f'https://docs.google.com/spreadsheets/d/{sheet.group(1)}/export?format=xlsx'))
    for row in rows:
        if not safe_url(row.get(cols['sourceUrl'])):
            row[cols['sourceUrl']] = links.get((row.get(cols['title']) or '').strip(), row.get(cols['sourceUrl']))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()

def transform(row, cols):
    def get(key):
        return str(row.get(cols[key]) or '').strip() if cols.get(key) else ''
    title, link = get('title'), safe_url(get('sourceUrl'))
    if not title or not link:
        return None
    return {'id': hashlib.sha256(canonical(link).encode()).hexdigest()[:20], 'title': title,
            'summary': get('summary'), 'sourceUrl': link, 'source': get('source'),
            'category': get('category') or 'Khác', 'region': get('region'),
            'section': get('section'), 'context': get('context'),
            'publishedAt': parse_date(get('publishedAt')), 'collectedAt': parse_date(get('collectedAt')),
            'imageUrl': safe_url(get('imageUrl')), 'analysis': get('analysis')}

def import_csv(csv_text, existing):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
    cols = mapping(reader.fieldnames or [])
    if not cols['title'] or not cols['sourceUrl']:
        raise ValueError(f'Chưa tìm thấy cột tiêu đề/URL: {reader.fieldnames}; ánh xạ: {cols}')
    merged = {x['id']: x for x in existing if isinstance(x, dict) and x.get('id')}
    before = len(merged)
    raw_count = valid = 0
    for row in reader:
        raw_count += 1
        article = transform(row, cols)
        if article:
            valid += 1
            merged[article['id']] = article
    if valid == 0:
        raise ValueError('Sheet không có tin hợp lệ: cần tiêu đề và URL http/https thật, không chỉ chữ "Xem nguồn"; giữ dữ liệu cũ')
    ordered = sorted(merged.values(), key=lambda a: (a.get('publishedAt') or a.get('collectedAt') or '', a['id']), reverse=True)
    max_records = max(1, int(os.getenv('MAX_RECORDS', '5000')))
    return ordered[:max_records], {'sourceRows': raw_count, 'validRows': valid,
                                    'newRows': len(merged) - before, 'totalRows': len(ordered), 'columns': cols}

def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as tmp:
        json.dump(obj, tmp, ensure_ascii=False, indent=2)
        tmp.write('\n')
        temp_name = tmp.name
    os.replace(temp_name, path)

def main():
    url = os.getenv('SHEET_CSV_URL') or DEFAULT_URL
    if not safe_url(url):
        raise ValueError('SHEET_CSV_URL không hợp lệ')
    raw = download(url).decode('utf-8-sig')
    if raw.lstrip().lower().startswith(('<html', '<!doctype')):
        raise ValueError('Nhận HTML thay CSV. Kiểm tra quyền Publish to web')
    raw = recover_google_links(raw, url)
    path = DATA / 'news.json'
    old = json.loads(path.read_text('utf-8')) if path.exists() else []
    news, info = import_csv(raw, old)
    if news == old:
        print('Không có thay đổi', json.dumps(info, ensure_ascii=False))
        return
    atomic_json(path, news)
    atomic_json(DATA / 'metadata.json', {'lastSync': datetime.now(timezone.utc).isoformat(), 'status': 'ok', **info})
    print(json.dumps(info, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Lỗi đồng bộ, dữ liệu cũ được giữ: {exc}', file=sys.stderr)
        sys.exit(1)
