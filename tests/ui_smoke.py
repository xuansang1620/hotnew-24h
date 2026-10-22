"""Browser checks: serve public/ on port 8000, then uv run --with playwright --with tzdata python tests/ui_smoke.py."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'public/data/news.json').read_text('utf-8'))
OUT = ROOT / '.venv/ui-qa'
OUT.mkdir(parents=True, exist_ok=True)
latest = max(datetime.fromisoformat(a['publishedAt'] or a['collectedAt']) for a in DATA if a.get('publishedAt') or a.get('collectedAt'))

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 1050}, timezone_id='Asia/Ho_Chi_Minh')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.clock.install(time=latest + timedelta(minutes=1))
    page.goto('http://127.0.0.1:8000', wait_until='networkidle')
    page.wait_for_selector('.news-card')
    assert page.locator('.news-card').count() == 12
    assert page.locator('.news-card .preview .context-info').first.is_visible()
    assert page.locator('.news-card .preview .impact-info').first.is_visible()
    assert page.locator('.news-card .source-name').first.inner_text() != 'Chưa rõ nguồn'
    assert '1970' not in page.locator('#news').inner_text()
    page.screenshot(path=str(OUT / 'desktop.png'), full_page=False)
    page.locator('.article-details summary').first.click()
    assert page.locator('.news-card .full-content').first.is_visible()
    assert not page.locator('.news-card .preview').first.is_visible()
    assert page.locator('.article-details .close-label').first.is_visible()
    page.screenshot(path=str(OUT / 'expanded.png'), full_page=False)
    page.locator('#expand-all').check()
    assert page.locator('details[open]').count() == 12
    page.locator('#expand-all').uncheck()
    assert page.locator('details[open]').count() == 0
    page.locator('#period').select_option('all')
    page.locator('#more').click()
    assert page.locator('.news-card').count() == min(24, len(DATA))
    sample = next(a for a in DATA if a.get('context') and a.get('analysis'))
    page.locator('#search').fill(sample['context'])
    assert sample['title'] in page.locator('#news').inner_text()
    page.locator('#search').fill(sample['analysis'])
    assert sample['title'] in page.locator('#news').inner_text()
    page.locator('#search').fill('zzzz-no-matching-article-zzzz')
    assert page.locator('.news-card').count() == 0 and page.locator('#status').is_visible()
    page.locator('#reset').click()
    page.locator('#section').select_option(label='Tin trọng điểm')
    assert page.locator('.news-card').count() > 0
    assert all(label == 'Tin trọng điểm' for label in page.locator('.section-label').all_text_contents())
    page.locator('#reset').click()
    page.locator('#categories button').nth(1).click()
    selected = page.locator('#list-title').inner_text()
    assert all(label == selected for label in page.locator('.news-card .tag').all_text_contents())
    page.locator('#reset').click()
    for width in (768, 390, 320):
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}px'
        page.screenshot(path=str(OUT / f'mobile-{width}.png'), full_page=False)
    page.set_viewport_size({'width': 1440, 'height': 1050})
    page.locator('#theme').click()
    assert page.locator('body').evaluate("element => element.classList.contains('dark')")
    page.reload(wait_until='networkidle')
    assert page.locator('body').evaluate("element => element.classList.contains('dark')")
    assert page.locator('body').evaluate('element => getComputedStyle(element).color') == 'rgb(234, 240, 248)'
    assert page.locator('body').evaluate('element => getComputedStyle(element).backgroundColor') == 'rgb(12, 21, 33)'
    page.screenshot(path=str(OUT / 'dark.png'), full_page=False)
    assert not errors, errors
    # Missing metadata must not block articles; absent dates must remain unknown.
    page.route('**/data/metadata.json', lambda route: route.fulfill(status=500, body='unavailable'))
    fixture = [{'id': 'no-date', 'title': 'Tin thiếu ngày', 'summary': '<script>bad()</script>',
                'sourceUrl': 'javascript:alert(1)', 'context': '', 'analysis': ''}]
    page.route('**/data/news.json', lambda route: route.fulfill(json=fixture))
    page.reload(wait_until='networkidle')
    page.locator('#period').select_option('all')
    assert page.locator('.news-card').count() == 1
    assert 'Chưa rõ ngày cập nhật' in page.locator('.news-card').inner_text()
    assert page.locator('.source-link').count() == 0
    assert page.locator('.news-card script').count() == 0
    assert not errors, errors
    browser.close()
print('PASS: desktop, 768/390/320px, full text, search context/impact, filters, pagination, dark theme, missing metadata/dates, unsafe URLs and text escaping.')
