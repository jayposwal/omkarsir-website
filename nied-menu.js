(function(){
  function esc(s){
    var d = document.createElement('div');
    d.textContent = (s===null||s===undefined) ? '' : String(s);
    return d.innerHTML;
  }

  function injectStyles(){
    if(document.getElementById('nied-menu-style')) return;
    var css = '#nied-navbar{font-family:"Noto Sans Devanagari",Arial,sans-serif;position:sticky;top:0;z-index:9999;}'
      + '.nied-ticker{background:#111a3d;color:#fff;display:flex;align-items:center;overflow:hidden;padding:0;font-size:.78rem;height:34px;}'
      + '.nied-ticker-live{flex-shrink:0;display:flex;align-items:center;gap:6px;background:#FF6B00;color:#fff;font-weight:800;padding:0 14px;height:100%;letter-spacing:.4px;font-size:.72rem;}'
      + '.nied-ticker-dot{width:7px;height:7px;border-radius:50%;background:#fff;animation:niedPulse 1.2s infinite;}'
      + '@keyframes niedPulse{0%,100%{opacity:1;}50%{opacity:.3;}}'
      + '.nied-ticker-track-wrap{flex:1;overflow:hidden;white-space:nowrap;position:relative;height:100%;display:flex;align-items:center;}'
      + '.nied-ticker-track{display:inline-flex;align-items:center;white-space:nowrap;animation:niedTicker 70s linear infinite;padding-left:100%;}'
      + '.nied-ticker-track span{margin-right:46px;color:#dfe3f5;}'
      + '.nied-ticker-track span::before{content:"\2022";color:#FF6B00;margin-right:10px;font-weight:800;}'
      + '@keyframes niedTicker{0%{transform:translateX(0);}100%{transform:translateX(-100%);}}'
      + '.nied-logo-icon{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#FF6B00,#ffb27a);display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;box-shadow:0 3px 8px rgba(255,107,0,.35);}'
      + '.nied-logo-wrap{display:flex;align-items:center;gap:10px;text-decoration:none;}'
      + '.nied-nav-inner{background:#1B2A6B;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:10px 20px;flex-wrap:wrap;box-shadow:0 2px 10px rgba(0,0,0,.18);position:relative;}'
      + '.nied-logo{color:#fff;font-weight:700;font-size:1.05rem;text-decoration:none;}'
      + '.nied-logo-text{display:flex;flex-direction:column;line-height:1.25;}'
      + '.nied-logo-sub{font-weight:600;font-size:.68rem;color:#cdd4ee;}'
      + '.nied-burger{display:none;background:none;border:none;color:#fff;font-size:1.6rem;cursor:pointer;line-height:1;padding:4px 8px;}'
      + '.nied-menu{list-style:none;display:flex;gap:4px;margin:0;padding:0;align-items:center;}'
      + '.nied-menu li{position:relative;}'
      + '.nied-top-link{display:block;color:#fff;text-decoration:none;padding:11px 14px;border-radius:8px;font-weight:600;font-size:.92rem;cursor:pointer;}'
      + '.nied-top-link:hover{background:#FF6B00;}'
      + '.nied-caret{font-size:.7em;}'
      + '.nied-dropdown{display:none;position:absolute;top:100%;left:0;background:#fff;min-width:220px;list-style:none;margin:6px 0 0;padding:6px;border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);z-index:100;}'
      + '.nied-has-dropdown.open > .nied-dropdown{display:block;}'
      + '.nied-dropdown li a{display:block;padding:8px 11px;color:#1B2A6B;text-decoration:none;border-radius:7px;font-size:.82rem;font-weight:500;}'
      + '.nied-dropdown li a:hover{background:#FFF1E6;color:#FF6B00;}'
      + '.nied-dropdown li.nied-has-submenu{position:relative;}'
      + '.nied-sub-link{display:flex !important;align-items:center;justify-content:space-between;gap:6px;cursor:pointer;}'
      + '.nied-subcaret{font-size:.75em;color:#999;}'
      + '.nied-submenu{display:none;position:absolute;top:-6px;left:100%;margin-left:4px;background:#fff;min-width:220px;list-style:none;padding:6px;border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);z-index:110;}'
      + '.nied-has-submenu.open > .nied-submenu, .nied-has-submenu:hover > .nied-submenu{display:block;}'
      + '.nied-submenu li a{display:block;padding:8px 11px;color:#1B2A6B;text-decoration:none;border-radius:7px;font-size:.8rem;font-weight:500;white-space:nowrap;}'
      + '.nied-submenu li a:hover{background:#FFF1E6;color:#FF6B00;}'
      + '.nied-search-wrap{position:relative;margin-left:10px;}'
      + '.nied-search-btn{background:none;border:none;color:#fff;font-size:1.15rem;cursor:pointer;padding:6px 10px;line-height:1;}'
      + '.nied-search-btn:hover{color:#FFD0A0;}'
      + '.nied-search-panel{display:none;position:absolute;top:100%;right:0;margin-top:8px;background:#fff;border-radius:12px;box-shadow:0 12px 32px rgba(0,0,0,.25);width:320px;max-width:88vw;padding:12px;z-index:200;}'
      + '.nied-search-panel.open{display:block;}'
      + '.nied-search-input{width:100%;box-sizing:border-box;padding:10px 12px;border:2px solid #E8EAF0;border-radius:8px;font-size:14px;font-family:inherit;outline:none;}'
      + '.nied-search-input:focus{border-color:#FF6B00;}'
      + '.nied-search-results{max-height:340px;overflow-y:auto;margin-top:8px;}'
      + '.nied-search-item{display:block;padding:9px 10px;border-radius:8px;text-decoration:none;color:#1A1A2E;}'
      + '.nied-search-item:hover{background:#FFF3E8;}'
      + '.nied-search-item .nsr-title{font-size:13px;font-weight:700;color:#1B2A6B;display:block;}'
      + '.nied-search-item .nsr-desc{font-size:11.5px;color:#888;display:block;margin-top:2px;line-height:1.4;}'
      + '.nied-search-empty{font-size:12.5px;color:#999;padding:10px;text-align:center;}'
      + '@media (max-width:880px){'
      + '.nied-ticker{font-size:.68rem;height:30px;}'
      + '.nied-ticker-live{padding:0 8px;font-size:.62rem;}'
      + '.nied-ticker-track span{margin-right:30px;}'
      + '.nied-logo-icon{width:28px;height:28px;font-size:14px;}'
      + '.nied-logo{font-size:.92rem;}'
      + '.nied-burger{display:block;}'
      + '.nied-menu{display:none;flex-direction:column;width:100%;align-items:stretch;background:#1B2A6B;position:absolute;left:0;top:100%;padding:8px 14px 14px;box-shadow:0 10px 24px rgba(0,0,0,.25);max-height:80vh;overflow-y:auto;}'
      + '.nied-menu.open{display:flex;}'
      + '.nied-menu > li{width:100%;}'
      + '.nied-top-link{padding:12px 10px;border-bottom:1px solid rgba(255,255,255,.12);}'
      + '.nied-dropdown{position:static;box-shadow:none;background:#24398f;margin:0 0 0 12px;width:calc(100% - 12px);border-radius:8px;}'
      + '.nied-dropdown li a{color:#fff;}'
      + '.nied-dropdown li a:hover{background:#FF6B00;color:#fff;}'
      + '.nied-submenu{position:static;box-shadow:none;background:#2c4099;margin:2px 0 0 10px;width:calc(100% - 10px);border-radius:8px;display:none;}'
      + '.nied-has-submenu.open > .nied-submenu{display:block;}'
      + '.nied-has-submenu:hover > .nied-submenu{display:none;}'
      + '.nied-has-submenu.open:hover > .nied-submenu{display:block;}'
      + '.nied-submenu li a{color:#fff;}'
      + '.nied-submenu li a:hover{background:#FF6B00;color:#fff;}'
      + '.nied-subcaret{color:#cdd4ee;}'
      + '.nied-search-panel{right:auto;left:0;width:280px;}'
      + '}';
    var style = document.createElement('style');
    style.id = 'nied-menu-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function render(mount, menu){
    injectStyles();
    var logo = menu.logo || {text:'New India Education', url:'/'};
    var ticker = menu.ticker || [];
    var tickerItems = ticker.map(function(t){ return '<span>' + esc(t) + '</span>'; }).join('');
    var tickerHtml = '';
    if(ticker.length){
      tickerHtml = '<div class="nied-ticker">'
        + '<div class="nied-ticker-live"><span class="nied-ticker-dot"></span>LIVE</div>'
        + '<div class="nied-ticker-track-wrap"><div class="nied-ticker-track">' + tickerItems + tickerItems + '</div></div>'
        + '</div>';
    }
    var logoTextInner = esc(logo.text) + (logo.subtitle ? '<span class="nied-logo-sub">' + esc(logo.subtitle) + '</span>' : '');
    var logoInner = '<span class="nied-logo-icon">🎓</span><span class="nied-logo-text">' + logoTextInner + '</span>';
    var html = tickerHtml
      + '<div class="nied-nav-inner"><a class="nied-logo nied-logo-wrap" href="' + esc(logo.url) + '">' + logoInner + '</a>'
      + '<button class="nied-burger" id="niedBurger" aria-label="Menu">&#9776;</button>'
      + '<ul class="nied-menu" id="niedMenuList">';
    function renderChildren(children){
      var out = '';
      (children || []).forEach(function(ch){
        if(ch.type === 'submenu'){
          out += '<li class="nied-has-submenu"><a class="nied-sub-link">' + esc(ch.label) + ' <span class="nied-subcaret">&#9656;</span></a><ul class="nied-submenu">';
          out += renderChildren(ch.children);
          out += '</ul></li>';
        } else {
          out += '<li><a href="' + esc(ch.url) + '">' + esc(ch.label) + '</a></li>';
        }
      });
      return out;
    }
    (menu.items || []).forEach(function(item){
      if(item.type === 'dropdown'){
        html += '<li class="nied-has-dropdown"><a class="nied-top-link">' + esc(item.label) + ' <span class="nied-caret">&#9662;</span></a><ul class="nied-dropdown">';
        html += renderChildren(item.children);
        html += '</ul></li>';
      } else {
        html += '<li><a class="nied-top-link" href="' + esc(item.url) + '">' + esc(item.label) + '</a></li>';
      }
    });
    html += '</ul>'
      + '<div class="nied-search-wrap">'
      + '<button class="nied-search-btn" id="niedSearchBtn" aria-label="Search">&#128269;</button>'
      + '<div class="nied-search-panel" id="niedSearchPanel">'
      + '<input type="text" class="nied-search-input" id="niedSearchInput" placeholder="Subject/Chapter खोजें..." autocomplete="off">'
      + '<div class="nied-search-results" id="niedSearchResults"></div>'
      + '</div></div>'
      + '</div>';
    mount.innerHTML = html;

    var burger = mount.querySelector('#niedBurger');
    var list = mount.querySelector('#niedMenuList');
    if(burger){
      burger.addEventListener('click', function(){ list.classList.toggle('open'); });
    }
    mount.querySelectorAll('.nied-has-dropdown > a.nied-top-link').forEach(function(a){
      a.addEventListener('click', function(e){
        e.preventDefault();
        e.stopPropagation();
        var parent = a.parentElement;
        var wasOpen = parent.classList.contains('open');
        mount.querySelectorAll('.nied-has-dropdown.open').forEach(function(li){
          li.classList.remove('open');
          li.querySelectorAll('.nied-has-submenu.open').forEach(function(s){ s.classList.remove('open'); });
        });
        if(!wasOpen) parent.classList.add('open');
      });
    });
    mount.querySelectorAll('.nied-has-submenu > a.nied-sub-link').forEach(function(a){
      a.addEventListener('click', function(e){
        e.preventDefault();
        e.stopPropagation();
        var parent = a.parentElement;
        var wasOpen = parent.classList.contains('open');
        var siblingGroup = parent.parentElement;
        siblingGroup.querySelectorAll(':scope > .nied-has-submenu.open').forEach(function(li){ li.classList.remove('open'); });
        if(!wasOpen) parent.classList.add('open');
      });
    });
    document.addEventListener('click', function(e){
      if(!mount.contains(e.target)){
        mount.querySelectorAll('.nied-has-dropdown.open').forEach(function(li){ li.classList.remove('open'); });
        mount.querySelectorAll('.nied-has-submenu.open').forEach(function(li){ li.classList.remove('open'); });
      }
    });

    setupSearch(mount);
  }

  var searchIndexCache = null;
  function loadSearchIndex(cb){
    if(searchIndexCache){ cb(searchIndexCache); return; }
    fetch('/search-index.json', {cache:'force-cache'})
      .then(function(r){ return r.json(); })
      .then(function(data){ searchIndexCache = data; cb(data); })
      .catch(function(err){ console.error('NIEd search index load error:', err); cb([]); });
  }

  function setupSearch(mount){
    var btn = mount.querySelector('#niedSearchBtn');
    var panel = mount.querySelector('#niedSearchPanel');
    var input = mount.querySelector('#niedSearchInput');
    var results = mount.querySelector('#niedSearchResults');
    if(!btn || !panel || !input || !results) return;

    btn.addEventListener('click', function(e){
      e.stopPropagation();
      panel.classList.toggle('open');
      if(panel.classList.contains('open')){
        input.focus();
        loadSearchIndex(function(){});
      }
    });

    document.addEventListener('click', function(e){
      if(!panel.contains(e.target) && e.target !== btn){
        panel.classList.remove('open');
      }
    });

    function renderResults(items){
      if(!items.length){
        results.innerHTML = '<div class="nied-search-empty">कोई परिणाम नहीं मिला</div>';
        return;
      }
      results.innerHTML = items.slice(0, 15).map(function(it){
        return '<a class="nied-search-item" href="' + esc(it.url) + '">'
          + '<span class="nsr-title">' + esc(it.title) + '</span>'
          + (it.desc ? '<span class="nsr-desc">' + esc(it.desc) + '</span>' : '')
          + '</a>';
      }).join('');
    }

    var debounceTimer = null;
    input.addEventListener('input', function(){
      var q = input.value.trim().toLowerCase();
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function(){
        if(!q){ results.innerHTML = ''; return; }
        loadSearchIndex(function(data){
          var matches = data.filter(function(it){
            return it.title.toLowerCase().indexOf(q) !== -1 || (it.desc && it.desc.toLowerCase().indexOf(q) !== -1);
          });
          renderResults(matches);
        });
      }, 150);
    });
  }

  function init(){
    var mount = document.getElementById('nied-navbar');
    if(!mount) return;
    fetch('/menu.json', {cache:'no-store'})
      .then(function(r){ return r.json(); })
      .then(function(menu){ render(mount, menu); })
      .catch(function(err){ console.error('NIEd menu load error:', err); });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* ============================================================
   Content Protection — NIEd
   Deters casual copy-paste of paid/free notes. This raises the
   bar for casual copying; it is not a substitute for legal
   copyright (see /privacy.html) which is the real protection.
   ============================================================ */
(function(){
  function toast(msg){
    var existing = document.getElementById('nied-toast');
    if(existing) existing.remove();
    var t = document.createElement('div');
    t.id = 'nied-toast';
    t.textContent = msg;
    t.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);'
      + 'background:#1B2A6B;color:#fff;padding:11px 20px;border-radius:50px;'
      + 'font-family:Arial,sans-serif;font-size:13px;font-weight:600;z-index:99999;'
      + 'box-shadow:0 8px 24px rgba(0,0,0,.25);max-width:88vw;text-align:center;'
      + 'opacity:0;transition:opacity .25s ease;';
    document.body.appendChild(t);
    requestAnimationFrame(function(){ t.style.opacity = '1'; });
    setTimeout(function(){
      t.style.opacity = '0';
      setTimeout(function(){ t.remove(); }, 300);
    }, 1800);
  }

  // Block right-click context menu (Save As / Inspect shortcuts)
  document.addEventListener('contextmenu', function(e){
    e.preventDefault();
    toast('🔒 यह Content Omkar Sir / New India Education की संपत्ति है — कृपया Copy न करें');
  });

  // Block copy — allow inside actual form fields (search boxes etc.)
  document.addEventListener('copy', function(e){
    var tag = (e.target && e.target.tagName) || '';
    if(tag === 'INPUT' || tag === 'TEXTAREA') return;
    e.preventDefault();
    toast('🔒 Copy Disabled — यह Content पिछले 8 सालों की मेहनत से बना है, कृपया केवल App/Website पर ही पढ़ें');
  });

  // Block common devtools / view-source / save-page shortcuts
  document.addEventListener('keydown', function(e){
    var k = e.key ? e.key.toLowerCase() : '';
    var blockCombo = (e.ctrlKey || e.metaKey) && ['u','s','c'].indexOf(k) !== -1;
    var blockDevtools = e.key === 'F12' || ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i','j','c'].indexOf(k) !== -1);
    if(blockCombo || blockDevtools){
      e.preventDefault();
      toast('🔒 यह Action इस Website पर उपलब्ध नहीं है');
    }
  });

  // Make images harder to drag-save
  document.addEventListener('dragstart', function(e){
    if(e.target && e.target.tagName === 'IMG') e.preventDefault();
  });

  // Light text-selection deterrent — skip form fields & anything marked selectable
  var css = '.nied-protect-off, input, textarea, select { -webkit-user-select: text !important; user-select: text !important; }';
  var style = document.createElement('style');
  style.textContent = 'body:not(.nied-protect-off){-webkit-user-select:none;-ms-user-select:none;user-select:none;}' + css;
  document.head.appendChild(style);
})();
