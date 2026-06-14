(function(){
  function esc(s){
    var d = document.createElement('div');
    d.textContent = (s===null||s===undefined) ? '' : String(s);
    return d.innerHTML;
  }

  function fmtDate(iso){
    try{
      var d = new Date(iso);
      var months = ['जन','फ़र','मार्च','अप्रैल','मई','जून','जुल','अग','सित','अक्तू','नव','दिस'];
      return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
    }catch(e){ return ''; }
  }

  function injectStyles(){
    if(document.getElementById('nied-lp-style')) return;
    var css = '.nied-lp-section{padding:50px 6%;}'
      + '.nied-lp-title{text-align:center;font-size:26px;font-weight:800;font-family:"Baloo 2","Noto Sans Devanagari",sans-serif;margin-bottom:6px;color:#1A1A2E;}'
      + '.nied-lp-title span{color:#FF6B00;}'
      + '.nied-lp-sub{text-align:center;color:#999;font-size:14px;margin-bottom:28px;}'
      + '.nied-lp-grid{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;}'
      + '.nied-lp-card{background:#fff;border:2px solid #E8EAF0;border-radius:14px;padding:16px 18px;display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;transition:all .2s;}'
      + '.nied-lp-card:hover{border-color:#FF6B00;transform:translateY(-3px);box-shadow:0 8px 24px rgba(255,107,0,.12);}'
      + '.nied-lp-icon{font-size:26px;flex-shrink:0;width:46px;height:46px;border-radius:12px;background:#FFF3E8;display:flex;align-items:center;justify-content:center;}'
      + '.nied-lp-info{flex:1;min-width:0;}'
      + '.nied-lp-cardtitle{font-weight:700;color:#1A1A2E;font-size:14px;line-height:1.4;font-family:"Baloo 2","Noto Sans Devanagari",sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
      + '.nied-lp-date{font-size:12px;color:#999;margin-top:3px;}'
      + '.nied-lp-arrow{color:#FF6B00;font-size:18px;flex-shrink:0;}';
    var style = document.createElement('style');
    style.id = 'nied-lp-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function render(mount, posts){
    if(!posts || !posts.length){ return; }
    injectStyles();
    var html = '<section class="nied-lp-section"><h2 class="nied-lp-title">📝 नवीनतम <span>Notes</span></h2>'
      + '<p class="nied-lp-sub">हाल ही में जोड़े गए नोट्स यहाँ देखें</p><div class="nied-lp-grid">';
    posts.slice(0, 6).forEach(function(p){
      html += '<a class="nied-lp-card" href="' + esc(p.url) + '">'
        + '<span class="nied-lp-icon">' + esc(p.icon || '📄') + '</span>'
        + '<div class="nied-lp-info"><div class="nied-lp-cardtitle">' + esc(p.title) + '</div>'
        + '<div class="nied-lp-date">' + esc(fmtDate(p.date)) + '</div></div>'
        + '<span class="nied-lp-arrow">→</span></a>';
    });
    html += '</div></section>';
    mount.innerHTML = html;
  }

  function init(){
    var mount = document.getElementById('nied-latest-posts');
    if(!mount) return;
    fetch('/posts.json', {cache:'no-store'})
      .then(function(r){ return r.json(); })
      .then(function(data){ render(mount, data.posts || []); })
      .catch(function(err){ console.error('NIEd latest posts error:', err); });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
