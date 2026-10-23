"""Serve public/ on port 8000, then uv run --with playwright python tests/reader_smoke.py."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

SOURCE = 'https://reader-source.test/story'
ARTICLE = {'id': 'reader-test', 'title': 'Bài báo kiểm tra khung đọc', 'sourceUrl': SOURCE,
           'category': 'Công nghệ', 'section': 'B - Theo lĩnh vực',
           'summary': 'Số liệu đầy đủ: 123,45 tỷ đồng. ' * 12,
           'context': 'Bối cảnh từ bảng tin.', 'analysis': 'Cơ hội và rủi ro từ bảng tin.'}
OUT = Path(__file__).resolve().parents[1] / '.venv/ui-qa'
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/data/news.json', lambda route: route.fulfill(json=[ARTICLE]))
    page.route('**/data/metadata.json', lambda route: route.fulfill(json={'lastSync': None}))
    page.route(SOURCE, lambda route: route.fulfill(content_type='text/html; charset=utf-8', body='<!doctype html><html lang="vi"><meta charset="utf-8"><title>Nguồn thử nghiệm</title><body><h1>Bài báo trong khung</h1><p>Nội dung nguồn cho phép nhúng.</p><input aria-label="Ô trong bài báo"><script>try {top.location="https://escaped.test"} catch {}</script></body></html>'))
    page.goto('http://127.0.0.1:8000', wait_until='networkidle')
    page.select_option('#period', 'all')
    page.fill('#search', 'kiểm tra')
    opener = page.locator('.source-link')
    original_url = page.url
    opener.click()
    expect(page.locator('#article-reader')).to_be_visible()
    expect(page.frame_locator('#reader-frame').get_by_role('heading', name='Bài báo trong khung')).to_be_visible()
    assert len(context.pages) == 1 and page.url == original_url
    assert page.locator('#reader-external').get_attribute('href') == SOURCE
    assert page.locator('#reader-frame').get_attribute('sandbox') == 'allow-scripts allow-same-origin allow-forms'
    page.screenshot(path=str(OUT / 'reader-desktop.png'))
    page.locator('#reader-summary').click()
    expect(page.locator('#reader-summary-panel')).to_be_visible()
    assert ARTICLE['summary'].strip() in page.locator('#reader-summary-panel').inner_text()
    assert ARTICLE['context'] in page.locator('#reader-summary-panel').inner_text()
    assert ARTICLE['analysis'] in page.locator('#reader-summary-panel').inner_text()
    page.locator('#reader-maximize').click()
    assert page.locator('#article-reader').evaluate('e => Math.abs(e.getBoundingClientRect().width - innerWidth) < 2')
    page.locator('#reader-close').click()
    expect(page.locator('#article-reader')).not_to_be_visible()
    expect(opener).to_be_focused()
    expect(page.locator('#reader-frame')).not_to_have_attribute('src', SOURCE)
    assert page.input_value('#search') == 'kiểm tra' and page.input_value('#period') == 'all'
    assert not page.locator('body').evaluate("e => e.classList.contains('reader-open')")
    # Escape is handled in the app toolbar; keys inside a remote frame belong to that page.
    opener.click()
    page.frame_locator('#reader-frame').get_by_label('Ô trong bài báo').click()
    page.locator('#reader-close').focus()
    page.keyboard.press('Escape')
    expect(page.locator('#article-reader')).not_to_be_visible()
    # A publisher denial must leave a usable, in-page brief and explicit fallback link.
    page.unroute(SOURCE)
    page.route(SOURCE, lambda route: route.fulfill(headers={'Content-Type': 'text/html', 'X-Frame-Options': 'DENY'}, body='<h1>Cannot embed</h1>'))
    opener.click()
    page.locator('#reader-summary').click()
    expect(page.locator('#reader-summary-panel')).to_be_visible()
    assert '123,45 tỷ đồng' in page.locator('#reader-summary-panel').inner_text()
    assert len(context.pages) == 1 and page.url == original_url
    for width in (390, 320):
        page.set_viewport_size({'width': width, 'height': 844})
        assert page.locator('#article-reader').evaluate('e => e.scrollWidth <= e.clientWidth')
        assert page.locator('#reader-summary-panel .main-info p').evaluate('e => e.clientHeight >= e.scrollHeight')
        assert page.locator('#reader-close').bounding_box()['height'] >= 44
        page.screenshot(path=str(OUT / f'reader-mobile-{width}.png'))
    page.locator('#reader-close').click()
    expect(page.locator('#article-reader')).not_to_be_visible()
    # On a secure deployment, HTTP sources cannot be embedded; do not attempt mixed content.
    app = 'https://reader-app.test'
    root = Path(__file__).resolve().parents[1] / 'public'
    page.route(app + '/', lambda route: route.fulfill(content_type='text/html; charset=utf-8', body=(root / 'index.html').read_bytes()))
    page.route(app + '/app.js*', lambda route: route.fulfill(content_type='application/javascript; charset=utf-8', body=(root / 'app.js').read_bytes()))
    page.route(app + '/styles.css*', lambda route: route.fulfill(content_type='text/css; charset=utf-8', body=(root / 'styles.css').read_bytes()))
    page.unroute('**/data/news.json')
    page.route('**/data/news.json', lambda route: route.fulfill(json=[{**ARTICLE, 'sourceUrl': 'http://reader-source.test/story'}]))
    page.goto(app, wait_until='networkidle')
    page.select_option('#period', 'all')
    page.locator('.source-link').click()
    expect(page.locator('#reader-summary-panel')).to_be_visible()
    expect(page.locator('#reader-original')).to_be_disabled()
    assert not page.locator('#reader-frame').get_attribute('src')
    page.locator('#reader-close').click()
    # Same-origin pages must not get both allow-scripts and allow-same-origin.
    page.unroute('**/data/news.json')
    page.route('**/data/news.json', lambda route: route.fulfill(json=[{**ARTICLE, 'sourceUrl': app + '/same-story'}]))
    page.route(app + '/same-story', lambda route: route.fulfill(content_type='text/html', body='<h1>Same-origin source</h1>'))
    page.reload(wait_until='networkidle')
    page.select_option('#period', 'all')
    page.locator('.source-link').click()
    assert 'allow-same-origin' not in page.locator('#reader-frame').get_attribute('sandbox')
    page.locator('#reader-close').click()
    assert not errors, errors
    browser.close()
print('PASS: inline article, no new tab/navigation, full in-page brief, fullscreen, focus/filters restored, iframe unloaded, Escape, blocked publisher fallback, 390/320px mobile, HTTP fallback and same-origin sandbox.')
