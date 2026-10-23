const $ = (selector) => document.querySelector(selector);
let articles = [], category = 'Tất cả', limit = 12;
const expanded = new Set();
const vn = new Intl.DateTimeFormat('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', year: 'numeric'});
const clock = new Intl.DateTimeFormat('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit'});
const clean = (value) => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase();
const text = (value) => typeof value === 'string' ? value.trim() : '';
function node(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value) element.textContent = value;
  return element;
}
function allowedUrl(value) {
  try {const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url : null;}
  catch {return null;}
}
function articleTime(article) {
  for (const value of [article.publishedAt, article.collectedAt]) {
    if (!value) continue;
    const date = new Date(value);
    if (!Number.isNaN(+date)) return date;
  }
  return null;
}
function sourceName(article) {
  return text(article.source) || allowedUrl(article.sourceUrl)?.hostname.replace(/^www\./, '') || 'Chưa rõ nguồn';
}
function sectionName(article) {
  const value = text(article.section), normalized = clean(value);
  if (/^(?:phan\s+)?a\s*[-–—:]/.test(normalized)) return 'Tin trọng điểm';
  if (/^(?:phan\s+)?b\s*[-–—:]/.test(normalized)) return 'Theo lĩnh vực';
  if (/^(?:phan\s+)?c\s*[-–—:]/.test(normalized)) return 'Xu hướng đáng theo dõi';
  if (/^(?:phan\s+)?d\s*[-–—:]/.test(normalized)) return 'Công nghệ đáng thử';
  return value || 'Chưa phân phần';
}
function inPeriod(article, period, now) {
  if (period === 'all') return true;
  const date = articleTime(article);
  if (!date) return false;
  return period === '24h' ? +now - +date >= 0 && +now - +date <= 86400000 : vn.format(now) === vn.format(date);
}
function baseFiltered() {
  const query = clean($('#search').value), period = $('#period').value, section = $('#section').value, now = new Date();
  return articles.filter(article => inPeriod(article, period, now)
    && (section === 'all' || sectionName(article) === section)
    && (!query || clean([article.title, article.summary, article.context, article.analysis, article.category,
      article.section, sourceName(article), article.sourceUrl].join(' ')).includes(query)));
}
function infoBlock(label, value, className) {
  const block = node('section', className);
  block.append(node('h4', '', label), node('p', '', value || 'Chưa có thông tin trong bảng tin.'));
  return block;
}
let readerOpener = null;
function setReaderMode(mode) {
  const original = mode === 'original';
  $('#reader-original-panel').hidden = !original;
  $('#reader-summary-panel').hidden = original;
  $('#reader-original').setAttribute('aria-pressed', String(original));
  $('#reader-summary').setAttribute('aria-pressed', String(!original));
}
function openReader(article, opener) {
  const url = allowedUrl(article.sourceUrl);
  if (!url) return;
  const reader = $('#article-reader');
  readerOpener = opener;
  $('#reader-title').textContent = text(article.title);
  $('#reader-source').textContent = url.hostname.replace(/^www\./, '');
  $('#reader-external').href = url.href;
  $('#reader-frame').title = `Bài gốc: ${text(article.title)}`;
  const summary = $('#reader-summary-panel');
  summary.replaceChildren(node('p', 'reader-attribution', 'Nội dung tổng hợp từ bảng tin. Xem bài gốc để đối chiếu thông tin và số liệu.'),
    infoBlock('Thông tin chính & số liệu', text(article.summary), 'main-info'),
    infoBlock('Bối cảnh / Nguyên nhân', text(article.context), 'context-info'),
    infoBlock('Tác động / Cơ hội & Rủi ro', text(article.analysis), 'impact-info'));
  // HTTPS pages cannot embed insecure HTTP articles. Keep the local brief usable.
  const insecure = location.protocol === 'https:' && url.protocol === 'http:';
  $('#reader-note').textContent = insecure
    ? 'Nguồn dùng kết nối HTTP nên không thể xem trong khung này. Bạn có thể đọc bản tin tổng hợp hoặc mở trang nguồn.'
    : 'Nếu nguồn không cho xem bài trong khung, chọn “Bản tin tổng hợp” để đọc ngay tại đây hoặc “Mở trang nguồn”.';
  $('#reader-original').disabled = insecure;
  setReaderMode(insecure ? 'summary' : 'original');
  // Never grant same-origin scripts both sandbox privileges on our own origin.
  $('#reader-frame').setAttribute('sandbox', url.origin === location.origin
    ? 'allow-scripts allow-forms' : 'allow-scripts allow-same-origin allow-forms');
  if (!insecure) $('#reader-frame').src = url.href;
  reader.showModal();
  document.body.classList.add('reader-open');
}
$('#reader-original').addEventListener('click', () => setReaderMode('original'));
$('#reader-summary').addEventListener('click', () => setReaderMode('summary'));
$('#reader-close').addEventListener('click', () => $('#article-reader').close());
$('#reader-maximize').addEventListener('click', () => {
  const wide = $('#article-reader').classList.toggle('reader-wide');
  $('#reader-maximize').setAttribute('aria-pressed', String(wide));
  $('#reader-maximize').textContent = wide ? 'Thu nhỏ' : 'Toàn màn hình';
});
$('#article-reader').addEventListener('click', event => {
  if (event.target !== $('#article-reader')) return;
  const bounds = event.target.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) event.target.close();
});
$('#article-reader').addEventListener('close', () => {
  $('#reader-frame').removeAttribute('src');
  $('#reader-summary-panel').replaceChildren();
  $('#article-reader').classList.remove('reader-wide');
  $('#reader-maximize').setAttribute('aria-pressed', 'false');
  $('#reader-maximize').textContent = 'Toàn màn hình';
  document.body.classList.remove('reader-open');
  if (readerOpener?.isConnected) readerOpener.focus({preventScroll: true});
  readerOpener = null;
});
function renderCard(article) {
  const card = node('article', 'news-card');
  const meta = node('div', 'meta');
  meta.append(node('span', 'tag', article.category || 'Khác'));
  if (sectionName(article) === 'Tin trọng điểm') meta.append(node('span', 'priority', 'TIN TRỌNG ĐIỂM'));
  const heading = node('div', 'card-heading');
  const imageUrl = allowedUrl(article.imageUrl);
  if (imageUrl) {
    const image = node('img', 'thumbnail');
    image.src = imageUrl.href; image.alt = ''; image.loading = 'lazy'; image.referrerPolicy = 'no-referrer';
    image.addEventListener('error', () => image.remove(), {once: true}); heading.append(image);
  }
  heading.append(node('h3', '', article.title));
  const provenance = node('div', 'provenance');
  const date = articleTime(article);
  const stamp = node('time', '', date ? `${article.publishedAt ? 'Đăng' : 'Cập nhật'} ${vn.format(date)} · ${clock.format(date)}` : 'Chưa rõ ngày cập nhật');
  if (date) stamp.dateTime = date.toISOString();
  provenance.append(node('span', 'source-name', sourceName(article)), stamp);
  const preview = node('div', 'preview');
  preview.append(infoBlock('Thông tin chính & số liệu', text(article.summary), 'main-info'));
  const insights = node('div', 'insights');
  insights.append(infoBlock('Bối cảnh / Nguyên nhân', text(article.context), 'context-info'),
    infoBlock('Tác động / Cơ hội & Rủi ro', text(article.analysis), 'impact-info'));
  preview.append(insights);
  const details = node('details', 'article-details');
  const summary = node('summary');
  summary.append(node('span', 'open-label', 'Đọc đầy đủ'), node('span', 'close-label', 'Thu gọn nội dung'));
  const full = node('div', 'full-content');
  full.append(infoBlock('Thông tin chính & số liệu', text(article.summary), 'main-info'),
    infoBlock('Bối cảnh / Nguyên nhân', text(article.context), 'context-info'),
    infoBlock('Tác động / Cơ hội & Rủi ro', text(article.analysis), 'impact-info'));
  if (article.region) full.append(infoBlock('Khu vực', article.region, 'region-info'));
  full.append(node('p', 'section-note', `Phần bản tin: ${text(article.section) || 'Chưa phân phần'}`));
  details.append(summary, full);
  details.open = $('#expand-all').checked || expanded.has(article.id);
  details.addEventListener('toggle', () => {
    if (!details.isConnected) return;
    if (details.open) expanded.add(article.id); else expanded.delete(article.id);
  });
  const footer = node('div', 'card-footer');
  footer.append(node('span', 'section-label', sectionName(article)));
  const url = allowedUrl(article.sourceUrl);
  if (url) {
    const link = node('a', 'source-link', 'Đọc bài gốc');
    link.href = url.href; link.rel = 'nofollow'; link.setAttribute('aria-haspopup', 'dialog');
    link.addEventListener('click', event => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); openReader(article, link);
    });
    footer.append(link);
  }
  card.append(meta, heading, provenance, preview, details, footer);
  return card;
}
function renderCategories(items) {
  const counts = new Map();
  for (const article of items) counts.set(article.category || 'Khác', (counts.get(article.category || 'Khác') || 0) + 1);
  $('#categories').replaceChildren();
  const names = ['Tất cả', ...[...counts.keys()].sort((a, b) => a.localeCompare(b, 'vi'))];
  if (category !== 'Tất cả' && !counts.has(category)) names.push(category);
  for (const name of names) {
    const button = node('button', name === category ? 'active' : '', name);
    button.type = 'button'; button.setAttribute('aria-pressed', String(name === category));
    button.append(node('span', 'chip-count', String(name === 'Tất cả' ? items.length : counts.get(name) || 0)));
    button.addEventListener('click', () => {category = name; limit = 12; render();});
    $('#categories').append(button);
  }
}
function render() {
  const base = baseFiltered();
  const items = base.filter(article => category === 'Tất cả' || (article.category || 'Khác') === category);
  renderCategories(base);
  $('#list-title').textContent = category === 'Tất cả' ? 'Tin mới nhất' : category;
  $('#count').textContent = `${items.length} tin phù hợp · đang hiển thị ${Math.min(limit, items.length)}`;
  $('#news').replaceChildren(...items.slice(0, limit).map(renderCard));
  $('#more').hidden = items.length <= limit;
  $('#more').textContent = `Xem thêm ${Math.min(12, Math.max(0, items.length - limit))} tin`;
  $('#status').textContent = items.length ? '' : articles.length
    ? 'Không có tin phù hợp. Thử chọn “Tất cả thời gian” hoặc xóa bộ lọc.'
    : 'Chưa có dữ liệu. Vui lòng kiểm tra đồng bộ Google Sheets.';
}
function resetFilters() {
  $('#search').value = ''; $('#period').value = 'today'; $('#section').value = 'all'; category = 'Tất cả'; limit = 12; render();
}
function applyTheme(dark) {
  document.body.classList.toggle('dark', dark);
  $('#theme').setAttribute('aria-pressed', String(dark));
  $('#theme').setAttribute('aria-label', dark ? 'Bật chế độ sáng' : 'Bật chế độ tối');
}
$('#today').textContent = vn.format(new Date());
$('#search').addEventListener('input', () => {limit = 12; render();});
for (const selector of ['#period', '#section']) $(selector).addEventListener('change', () => {limit = 12; render();});
$('#reset').addEventListener('click', resetFilters);
$('#more').addEventListener('click', () => {limit += 12; render();});
$('#expand-all').addEventListener('change', () => {
  expanded.clear();
  if ($('#expand-all').checked) articles.forEach(article => expanded.add(article.id));
  render();
});
$('#theme').addEventListener('click', () => {
  applyTheme(!document.body.classList.contains('dark'));
  try {localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');} catch {}
});
try {applyTheme(localStorage.getItem('theme') === 'dark');} catch {}
async function loadJson(path) {
  const response = await fetch(path, {cache: 'no-store'});
  if (!response.ok) throw new Error(`Không tải được ${path}: ${response.status}`);
  return response.json();
}
Promise.all([loadJson('data/news.json'), loadJson('data/metadata.json').catch(() => null)]).then(([news, meta]) => {
  articles = (Array.isArray(news) ? news : []).filter(article => article && typeof article === 'object' && text(article.title));
  articles.sort((a, b) => (articleTime(b)?.getTime() || 0) - (articleTime(a)?.getTime() || 0));
  $('#total').textContent = articles.length.toLocaleString('vi-VN');
  $('#today-total').textContent = articles.filter(article => inPeriod(article, 'today', new Date())).length.toLocaleString('vi-VN');
  $('#analysis-total').textContent = articles.filter(article => text(article.context) && text(article.analysis)).length.toLocaleString('vi-VN');
  const lastSync = meta?.lastSync ? new Date(meta.lastSync) : null;
  $('#updated').textContent = lastSync && !Number.isNaN(+lastSync)
    ? `Dữ liệu cập nhật: ${clock.format(lastSync)} · ${vn.format(lastSync)}` : 'Chưa có thời điểm cập nhật dữ liệu';
  for (const name of [...new Set(articles.map(sectionName))].sort((a, b) => a.localeCompare(b, 'vi'))) {
    const option = node('option', '', name); option.value = name; $('#section').append(option);
  }
  render();
}).catch(error => {
  $('#status').textContent = 'Không thể tải bản tin. Vui lòng tải lại trang sau.';
  $('#updated').textContent = 'Dữ liệu không khả dụng'; console.error(error);
});
