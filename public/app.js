const $ = (s) => document.querySelector(s);
let articles = [], category = 'Tất cả', limit = 18;
const vn = new Intl.DateTimeFormat('vi-VN', {timeZone:'Asia/Ho_Chi_Minh',day:'2-digit',month:'2-digit',year:'numeric'});
const time = new Intl.DateTimeFormat('vi-VN', {timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit'});
const clean = (s) => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
function isAllowedUrl(value){try {const u = new URL(value);return ['https:','http:'].includes(u.protocol)}catch{return false}}
function articleTime(a){const d = new Date(a.publishedAt || a.collectedAt || 0);return Number.isNaN(+d)?null:d}
function filtered(){const search=clean($('#search').value), period=$('#period').value, now=new Date();return articles.filter(a=>{
  if(category!=='Tất cả' && a.category!==category)return false;
  if(search && !clean(`${a.title} ${a.summary} ${a.source} ${a.category}`).includes(search))return false;
  if(period==='all')return true;
  const d=articleTime(a);if(!d)return false;
  return period==='24h' ? (+now - +d>=0 && +now - +d<=86400000) : vn.format(now)===vn.format(d);
})}
function render(){const items=filtered();$('#count').textContent=`${items.length} tin`;$('#news').replaceChildren();$('#more').hidden=items.length<=limit;
  if(!items.length){$('#status').textContent=articles.length?'Không có tin phù hợp với bộ lọc.':'Chưa có dữ liệu. Vui lòng kiểm tra đồng bộ Google Sheets.';return}
  $('#status').textContent='';
  for(const a of items.slice(0,limit)){
    const card=document.createElement('article');card.className='news-card';
    const visual=document.createElement('div');visual.className='visual';visual.textContent='BẢN TIN 24h';
    if(isAllowedUrl(a.imageUrl)){const img=document.createElement('img');img.src=a.imageUrl;img.loading='lazy';img.alt='';img.onerror=()=>img.remove();visual.replaceChildren(img)}
    const body=document.createElement('div');body.className='content';
    const meta=document.createElement('div');meta.className='meta';
    const tag=document.createElement('span');tag.className='tag';tag.textContent=a.category||'Tin tức';
    const date=document.createElement('span');date.textContent=articleTime(a)?time.format(articleTime(a)):'Chưa rõ ngày';meta.append(tag,date);
    const title=document.createElement('h3');title.textContent=a.title;
    const summary=document.createElement('p');summary.textContent=a.summary||'';
    const link=document.createElement('a');link.className='source-link';link.textContent=`Đọc nguồn gốc ↗ ${a.source||''}`;
    if(isAllowedUrl(a.sourceUrl)){link.href=a.sourceUrl;link.target='_blank';link.rel='noopener noreferrer nofollow'}else{link.removeAttribute('href')}
    body.append(meta,title,summary,link);card.append(visual,body);$('#news').append(card);
  }
}
function categories(){const all=['Tất cả',...new Set(articles.map(a=>a.category||'Khác'))];$('#categories').replaceChildren();for(const item of all){const b=document.createElement('button');b.textContent=item;b.className=item===category?'active':'';b.addEventListener('click',()=>{category=item;limit=18;categories();render()});$('#categories').append(b)}}
$('#today').textContent=vn.format(new Date());
$('#search').addEventListener('input',()=>{limit=18;render()});$('#period').addEventListener('change',()=>{limit=18;render()});$('#more').addEventListener('click',()=>{limit+=18;render()});
$('#theme').addEventListener('click',()=>{document.body.classList.toggle('dark');try{localStorage.setItem('theme',document.body.classList.contains('dark')?'dark':'light')}catch{}});
try{if(localStorage.getItem('theme')==='dark')document.body.classList.add('dark')}catch{}
Promise.all([fetch('data/news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}),fetch('data/metadata.json',{cache:'no-store'}).then(r=>r.json())]).then(([news,meta])=>{
  articles=Array.isArray(news)?news:[];articles.sort((a,b)=>(articleTime(b)?.getTime()||0)-(articleTime(a)?.getTime()||0));
  $('#total').textContent=articles.length.toLocaleString('vi-VN');$('#updated').textContent=meta.lastSync?`Đồng bộ: ${time.format(new Date(meta.lastSync))}`:'Chưa đồng bộ';categories();render();
}).catch(err=>{$('#status').textContent='Không thể tải bản tin. Vui lòng thử lại sau.';$('#updated').textContent='Đồng bộ không khả dụng';console.error(err)});
