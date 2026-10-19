(function(){
  function esc(s){
    var d = document.createElement('div');
    d.textContent = (s===null||s===undefined) ? '' : String(s);
    return d.innerHTML;
  }

  // Site-wide favicon injection — runs on every page that loads nied-menu.js,
  // so we don't have to hand-edit the <head> of ~430+ pages individually.
  (function injectFavicon(){
    if(document.querySelector('link[rel="icon"]')) return; // don't duplicate if a page already sets its own
    var links = [
      {rel:'icon', type:'image/x-icon', href:'/favicon.ico'},
      {rel:'icon', type:'image/png', sizes:'192x192', href:'/favicon-192.png'},
      {rel:'icon', type:'image/png', sizes:'512x512', href:'/favicon-512.png'},
      {rel:'apple-touch-icon', href:'/apple-touch-icon.png'}
    ];
    links.forEach(function(l){
      var el = document.createElement('link');
      Object.keys(l).forEach(function(k){ el.setAttribute(k, l[k]); });
      document.head.appendChild(el);
    });
  })();

  // Site-wide GA4: pages generated without the gtag snippet (e.g. quizzes/*)
  // get it injected here, so every page that loads nied-menu.js is tracked.
  (function ensureGA4(){
    var GA_ID = 'G-WCK16L4WZX';
    if(typeof window.gtag === 'function' || document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){ window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID);
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
  })();

  // Site-wide GA4 conversion events — one delegated listener for every
  // App / WhatsApp / Telegram / Course / PDF / Social click on any page.
  // Mark these as Key Events in GA4 Admin → Events.
  (function trackConversionClicks(){
    function eventFor(href){
      if(/play\.google\.com|apps\.apple\.com/.test(href)) return 'app_install_click';
      if(/wa\.me|whatsapp\.com/.test(href)) return 'whatsapp_click';
      if(/t\.me\//.test(href)) return 'telegram_click';
      if(/omkarsir\.in/.test(href)) return 'course_click';
      if(/\.pdf(\?|#|$)|drive\.google\.com|archive\.org/.test(href)) return 'pdf_download';
      if(/youtube\.com|youtu\.be|instagram\.com/.test(href)) return 'social_click';
      return null;
    }
    document.addEventListener('click', function(e){
      var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
      if(!a || typeof window.gtag !== 'function') return;
      var name = eventFor(a.href);
      if(!name) return;
      var placement = a.className && typeof a.className === 'string' ? a.className.split(' ')[0] : '';
      if(!placement && a.closest('#nied-popup-overlay')) placement = 'popup';
      window.gtag('event', name, {
        link_url: a.href,
        link_text: (a.textContent || '').trim().slice(0, 80),
        placement: placement || 'inline',
        page_path: location.pathname
      });
    }, true);
  })();

  // Service worker (/sw.js) keeps fonts, images, CSS and JS in the browser
  // cache across visits — GitHub Pages itself only allows a 10-minute cache.
  (function registerServiceWorker(){
    if(!('serviceWorker' in navigator) || !window.isSecureContext) return;
    window.addEventListener('load', function(){
      navigator.serviceWorker.register('/sw.js').catch(function(err){ console.warn('NIEd SW:', err); });
    });
  })();

  // Site-wide timed conversion popup injection (15s delay)
  (function injectPopupScript(){
    if(document.getElementById('nied-popup-script')) return;
    var s = document.createElement('script');
    s.id = 'nied-popup-script';
    s.src = '/nied-popup.js';
    s.defer = true;
    document.head.appendChild(s);
  })();

  // Splits a top-nav label like "\ud83d\udcc4 \u0938\u092d\u0940 Courses" into two stacked lines
  // ("\ud83d\udcc4 \u0938\u092d\u0940" / "Courses") to save horizontal space, matching the
  // logo's title/subtitle stacking style. Single-word labels stay on one line.
  function formatTopLabel(label, caretHtml){
    caretHtml = caretHtml || '';
    return '<span class="nied-tl-line1">' + esc(label) + caretHtml + '</span>';
  }
  function injectStyles(){
    if(document.getElementById('nied-menu-style')) return;
    var css =
      "" +
      "#nied-navbar{font-family:\"Noto Sans Devanagari\",\"Hind\",Arial,sans-serif;position:sticky;top:0;z-index:9999}" +
      ".nied-logo-icon{width:38px;height:38px;border-radius:12px;background:linear-gradient(135deg,#f97316,#ffbd80);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;box-shadow:0 4px 10px rgba(249,115,22,.18)}" +
      ".nied-logo-wrap{display:flex;align-items:center;gap:10px;text-decoration:none;flex-shrink:0;order:1}" +
      ".nied-nav-inner{background:rgba(255,255,255,.98);color:#1b2a6b;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px clamp(14px,2.2vw,30px);flex-wrap:nowrap;box-shadow:0 5px 18px rgba(31,48,86,.07);border-bottom:1px solid #edf0f5;position:relative;min-height:72px}" +
      ".nied-logo{color:#1b2a6b;font-weight:800;font-size:1.05rem;text-decoration:none;letter-spacing:-.15px}" +
      ".nied-logo-text{display:flex;flex-direction:column;line-height:1.25}" +
      ".nied-logo-sub{font-weight:600;font-size:.68rem;color:#5f6880;margin-top:3px;letter-spacing:.1px}" +
      ".nied-burger{display:none;order:4;background:#fff;border:1px solid #dfe5f0;border-radius:10px;color:#1b2a6b;font-size:1.45rem;cursor:pointer;line-height:1;padding:7px 11px}" +
      ".nied-menu{list-style:none;display:flex;gap:3px;margin:0;padding:0;align-items:center;justify-content:flex-end;flex:1;order:2}" +
      ".nied-menu li{position:relative}" +
      ".nied-top-link{display:flex;align-items:center;justify-content:center;gap:5px;color:#26365f;text-decoration:none;padding:10px 9px;border-radius:10px;font-weight:700;font-size:.86rem;cursor:pointer;text-align:center;line-height:1.25;white-space:nowrap;transition:background .18s,color .18s}" +
      ".nied-top-link:hover,.nied-has-dropdown.open>.nied-top-link{background:#fff0e5;color:#c6530b}" +
      ".nied-tl-line1{display:inline-flex;align-items:center;gap:5px}" +
      ".nied-tl-line2{font-size:.86em;font-weight:600;opacity:.9}" +
      ".nied-caret{font-size:.7em;color:#969eb1;margin-left:2px}" +
      ".nied-dropdown{display:none;position:absolute;top:100%;left:0;background:#fff;min-width:245px;max-width:min(340px,90vw);list-style:none;margin:7px 0 0;padding:7px;border:1px solid #e8ecf4;border-radius:14px;box-shadow:0 16px 36px rgba(31,48,86,.14);z-index:100}" +
      ".nied-has-dropdown.open>.nied-dropdown{display:block}" +
      ".nied-dropdown li a{display:block;padding:10px 12px;color:#26365f;text-decoration:none;border-radius:9px;font-size:.84rem;font-weight:600;line-height:1.45}" +
      ".nied-dropdown li a:hover{background:#fff2e8;color:#c6530b}" +
      ".nied-dropdown li.nied-has-submenu{position:relative}" +
      ".nied-sub-link{display:flex!important;align-items:center;justify-content:space-between;gap:8px;cursor:pointer}" +
      ".nied-subcaret{font-size:.75em;color:#8b94aa}" +
      ".nied-submenu{display:none;position:absolute;top:-7px;left:100%;margin-left:5px;background:#fff;min-width:230px;max-width:min(340px,88vw);list-style:none;padding:7px;border:1px solid #e8ecf4;border-radius:14px;box-shadow:0 16px 36px rgba(31,48,86,.14);z-index:110}" +
      ".nied-has-submenu.open>.nied-submenu,.nied-has-submenu:hover>.nied-submenu{display:block}" +
      ".nied-submenu li a{display:block;padding:9px 11px;color:#26365f;text-decoration:none;border-radius:8px;font-size:.81rem;font-weight:600;white-space:normal;line-height:1.4}" +
      ".nied-submenu li a:hover{background:#fff2e8;color:#c6530b}" +
      ".nied-search-wrap{position:relative;margin-left:2px;flex-shrink:0;order:3}" +
      ".nied-search-btn{display:flex;align-items:center;justify-content:center;gap:8px;background:#f8f9fc;border:1px solid #e2e7f1;border-radius:999px;color:#26365f;font-size:.8rem;font-weight:700;cursor:pointer;padding:10px 13px;line-height:1.15;white-space:nowrap}" +
      ".nied-search-btn:hover,.nied-search-btn[aria-expanded=true]{border-color:#f5bd91;background:#fff5ed;color:#b94e0a}" +
      ".nied-search-icon{font-size:1.05rem;line-height:1}" +
      ".nied-search-panel{display:none;position:absolute;top:calc(100% + 10px);right:0;background:#fff;border:1px solid #e6eaf2;border-radius:14px;box-shadow:0 16px 36px rgba(31,48,86,.17);width:340px;max-width:88vw;padding:12px;z-index:200}" +
      ".nied-search-panel.open{display:block}" +
      ".nied-search-input{width:100%;box-sizing:border-box;padding:11px 12px;border:1.5px solid #dfe5f0;border-radius:10px;font-size:14px;font-family:inherit;color:#26365f;outline:none}" +
      ".nied-search-input:focus{border-color:#f97316;box-shadow:0 0 0 3px rgba(249,115,22,.12)}" +
      ".nied-search-results{max-height:340px;overflow-y:auto;margin-top:8px}" +
      ".nied-search-item{display:block;padding:10px;border-radius:9px;text-decoration:none;color:#1a1a2e}" +
      ".nied-search-item:hover{background:#fff3e8}" +
      ".nied-search-item .nsr-title{font-size:13px;font-weight:800;color:#1b2a6b;display:block}" +
      ".nied-search-item .nsr-desc{font-size:11.5px;color:#727b92;display:block;margin-top:3px;line-height:1.45}" +
      ".nied-search-empty{font-size:12.5px;color:#7c8497;padding:12px;text-align:center}" +
      "@media(max-width:1100px){" +
      " .nied-nav-inner{flex-wrap:wrap;gap:8px;padding:10px 16px}" +
      " .nied-burger{display:block}" +
      " .nied-menu{display:none;flex-direction:column;width:100%;flex:0 0 100%;align-items:stretch;justify-content:flex-start;background:#fff;position:absolute;left:0;right:0;top:100%;padding:9px 14px 16px;border:1px solid #edf0f5;border-top:0;border-radius:0 0 16px 16px;box-shadow:0 14px 28px rgba(31,48,86,.13);max-height:78vh;overflow-y:auto;order:5}" +
      " .nied-menu.open{display:flex}" +
      " .nied-menu>li{width:100%}" +
      " .nied-top-link{justify-content:flex-start;text-align:left;padding:12px 11px;font-size:.92rem;white-space:normal}" +
      " .nied-dropdown{position:static;max-width:none;box-shadow:none;background:#fbfcff;margin:0 0 0 10px;width:calc(100% - 10px);border:1px solid #edf0f5;border-radius:10px}" +
      " .nied-submenu{position:static;max-width:none;box-shadow:none;background:#fff6ef;margin:3px 0 3px 10px;width:calc(100% - 10px);border-radius:10px;border:1px solid #f6e0cf;display:none}" +
      " .nied-has-submenu.open>.nied-submenu{display:block}" +
      " .nied-has-submenu:hover>.nied-submenu{display:none}" +
      " .nied-has-submenu.open:hover>.nied-submenu{display:block}" +
      " .nied-dropdown li a,.nied-submenu li a{color:#26365f;white-space:normal}" +
      " .nied-dropdown li a:hover,.nied-submenu li a:hover{background:#ffead9;color:#b94e0a}" +
      " .nied-search-wrap{margin-left:auto}" +
      " .nied-search-label{display:none}" +
      " .nied-search-btn{width:42px;height:42px;padding:0;border-radius:12px}" +
      "}" +
      "@media(max-width:520px){" +
      " .nied-logo-icon{width:31px;height:31px;font-size:15px}" +
      " .nied-logo{font-size:.95rem}" +
      " .nied-logo-sub{font-size:.62rem}" +
      " .nied-nav-inner{padding:9px 10px;gap:7px;min-height:62px}" +
      " .nied-burger{font-size:1.3rem;padding:7px 10px}" +
      " .nied-search-panel{right:0;left:auto;width:min(340px,88vw)}" +
      "}" +
      "@media(prefers-reduced-motion:reduce){" +
      " .nied-top-link,.nied-search-btn{transition:none}" +
      "}" +
      "#nied-back-to-top{position:fixed;right:16px;bottom:24px;z-index:9990;width:42px;height:42px;border-radius:50%;background:#FFFFFF;border:2px solid #FF6B00;color:#FF6B00;box-shadow:0 4px 16px rgba(0,0,0,.15);display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:800;cursor:pointer;opacity:0;visibility:hidden;transform:translateY(10px);transition:all .25s ease;text-decoration:none}" +
      "#nied-back-to-top.show{opacity:1;visibility:visible;transform:translateY(0)}" +
      "#nied-back-to-top:hover{background:#FF6B00;color:#fff}" +
      "@media(max-width:768px){" +
      " p,li{line-height:1.82}" +
      " .ch-nav{display:flex!important;flex-direction:column!important;gap:10px!important;padding:0 16px!important;margin:24px auto!important}" +
      " .ch-nav-btn{width:100%!important;min-height:46px!important;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;font-size:14px!important;font-weight:700!important;border-radius:12px!important;background:#FFFFFF!important;border:2px solid #FF6B00!important;color:#1B2A6B!important;box-shadow:0 4px 14px rgba(27,42,107,.06)!important;padding:11px 14px!important}" +
      " .ch-nav-next{background:linear-gradient(135deg,#FF6B00,#F97316)!important;color:#FFFFFF!important;border-color:#FF6B00!important}" +
      "}";
    var style = document.createElement('style');
    style.id = 'nied-menu-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function render(mount, menu){
    injectStyles();
    var logo = menu.logo || {text:'New India Education', url:'/'};
    var logoTextInner = esc(logo.text) + (logo.subtitle ? '<span class="nied-logo-sub">' + esc(logo.subtitle) + '</span>' : '');
    var logoInner = '<span class="nied-logo-icon">🎓</span><span class="nied-logo-text">' + logoTextInner + '</span>';
    var html = '<div class="nied-nav-inner"><a class="nied-logo nied-logo-wrap" href="' + esc(logo.url) + '">' + logoInner + '</a>'
      + '<button class="nied-burger" id="niedBurger" aria-label="Menu">&#9776;</button>'
      + '<ul class="nied-menu" id="niedMenuList">';
    function renderChildren(children){
      var out = '';
      (children || []).forEach(function(ch){
        if(ch.type === 'submenu'){
          out += '<li class="nied-has-submenu"><a class="nied-sub-link" href="#" role="button" aria-expanded="false">' + esc(ch.label) + ' <span class="nied-subcaret">&#9656;</span></a><ul class="nied-submenu">';
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
        html += '<li class="nied-has-dropdown"><a class="nied-top-link" href="#" role="button" aria-expanded="false">' + formatTopLabel(item.label, ' <span class="nied-caret">&#9662;</span>') + '</a><ul class="nied-dropdown">';
        html += renderChildren(item.children);
        html += '</ul></li>';
      } else {
        html += '<li><a class="nied-top-link" href="' + esc(item.url) + '">' + formatTopLabel(item.label) + '</a></li>';
      }
    });
    html += '</ul>'
      + '<div class="nied-search-wrap">'
      + '<button type="button" class="nied-search-btn" id="niedSearchBtn" aria-label="Notes, Subject या Exam खोजें" aria-expanded="false"><span class="nied-search-icon" aria-hidden="true">&#128269;</span><span class="nied-search-label">Notes, Subject या Exam खोजें</span></button>'
      + '<div class="nied-search-panel" id="niedSearchPanel">'
      + '<input type="text" class="nied-search-input" id="niedSearchInput" aria-label="Notes, Subject या Exam खोजें" placeholder="Notes, Subject या Exam खोजें..." autocomplete="off">'
      + '<div class="nied-search-results" id="niedSearchResults" role="listbox"></div>'
      + '</div></div>'
      + '</div>';
    mount.innerHTML = html;

    var burger = mount.querySelector('#niedBurger');
    var list = mount.querySelector('#niedMenuList');
    if(burger){
      burger.setAttribute('aria-expanded','false');
      burger.addEventListener('click', function(){
        var isOpen = list.classList.toggle('open');
        burger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
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
        syncExpanded();
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
        syncExpanded();
      });
    });
    document.addEventListener('click', function(e){
      if(!mount.contains(e.target)){
        mount.querySelectorAll('.nied-has-dropdown.open').forEach(function(li){ li.classList.remove('open'); });
        mount.querySelectorAll('.nied-has-submenu.open').forEach(function(li){ li.classList.remove('open'); });
        syncExpanded();
      }
    });
    function syncExpanded(){
      mount.querySelectorAll('a[role="button"][aria-expanded]').forEach(function(a){
        a.setAttribute('aria-expanded', a.parentElement.classList.contains('open') ? 'true' : 'false');
      });
    }

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
      btn.setAttribute('aria-expanded', panel.classList.contains('open') ? 'true' : 'false');
      if(panel.classList.contains('open')){
        input.focus();
        loadSearchIndex(function(){});
      }
    });

    document.addEventListener('click', function(e){
      if(!panel.contains(e.target) && e.target !== btn){
        panel.classList.remove('open');
        btn.setAttribute('aria-expanded','false');
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

  function initMobileBarAndBackToTop(){
    // Back to top button
    if(!document.getElementById('nied-back-to-top')){
      var btt = document.createElement('a');
      btt.id = 'nied-back-to-top';
      btt.href = '#';
      btt.setAttribute('aria-label', 'ऊपर जाएँ');
      btt.innerHTML = '↑';
      document.body.appendChild(btt);

      btt.addEventListener('click', function(e){
        e.preventDefault();
        window.scrollTo({top: 0, behavior: 'smooth'});
      });

      window.addEventListener('scroll', function(){
        if(window.scrollY > 300){
          btt.classList.add('show');
        } else {
          btt.classList.remove('show');
        }
      }, {passive: true});
    }
  }

  function init(){
    var mount = document.getElementById('nied-navbar');
    if(!mount){
      mount = document.createElement('div');
      mount.id = 'nied-navbar';
      document.body.insertBefore(mount, document.body.firstChild);
    }
    fetch('/menu.json', {cache:'no-store'})
      .then(function(r){ return r.json(); })
      .then(function(menu){ 
        render(mount, menu);
        initMobileBarAndBackToTop();
      })
      .catch(function(err){ 
        console.error('NIEd menu load error:', err);
        injectStyles();
        initMobileBarAndBackToTop();
      });
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

/* ============================================================
   Site-wide Floating WhatsApp Button — NIEd
   Course/query enquiries redirect straight to WhatsApp chat.
   ============================================================ */
(function(){
  function init(){
    var css = '.wa-float{position:fixed;bottom:80px;right:20px;background:#25d366;color:#fff;'
      + 'border-radius:50px;padding:13px 20px;text-decoration:none;font-weight:700;font-size:14px;'
      + 'box-shadow:0 4px 18px rgba(37,211,102,.5);z-index:9998;display:flex;align-items:center;'
      + 'gap:8px;transition:transform .2s;font-family:Arial,sans-serif;}'
      + '.wa-float:hover{transform:scale(1.05);}'
      + '.wa-float svg{width:20px;height:20px;fill:#fff;flex-shrink:0;}'
      + '.app-float{position:fixed;bottom:24px;right:20px;background:#FF6B00;color:#fff;'
      + 'border-radius:50px;padding:13px 20px;text-decoration:none;font-weight:700;font-size:14px;'
      + 'box-shadow:0 4px 18px rgba(255,107,0,.5);z-index:9998;display:flex;align-items:center;'
      + 'gap:8px;transition:transform .2s;font-family:Arial,sans-serif;}'
      + '.app-float:hover{transform:scale(1.05);}'
      + '@media (max-width:480px){'
      + '.wa-float{padding:12px 16px;font-size:13px;bottom:68px;right:14px;}'
      + '.wa-float span{display:none;}.wa-float svg{width:24px;height:24px;}'
      + '.app-float{padding:12px 16px;font-size:13px;bottom:16px;right:14px;}'
      + '.app-float span{display:none;}'
      + '}';
    var style = document.createElement('style');
    style.id = 'nied-float-style';
    style.textContent = css;
    document.head.appendChild(style);

    if(!document.querySelector('.wa-float')){
      var msg = encodeURIComponent('नमस्ते Omkar Sir, मुझे किसी Course के बारे में जानकारी चाहिए।');
      var wa = document.createElement('a');
      wa.href = 'https://wa.me/917023166962?text=' + msg;
      wa.className = 'wa-float';
      wa.setAttribute('aria-label', 'WhatsApp पर संपर्क करें');
      wa.target = '_blank';
      wa.rel = 'noopener';
      wa.innerHTML = '<svg viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg><span>WhatsApp</span>';
      document.body.appendChild(wa);
    }

    if(!document.querySelector('.app-float')){
      var app = document.createElement('a');
      app.href = 'https://play.google.com/store/apps/details?id=co.april2019.techa';
      app.className = 'app-float';
      app.setAttribute('aria-label', 'NIEd App डाउनलोड करें (Google Play)');
      app.target = '_blank';
      app.rel = 'noopener';
      app.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="#fff"><path d="M3 20.5v-17c0-.59.34-1.1.83-1.34L13.69 12l-9.86 9.84c-.49-.24-.83-.75-.83-1.34m13.81-8.5l2.35-2.35 3.13 1.81c.88.51.88 1.76 0 2.27l-3.13 1.81L16.81 12M14.5 12L4.7 2.2 15.19 8.24 14.5 12z"/></svg><span>App Download</span>';
      document.body.appendChild(app);
    }
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* ============================================================
   Site-wide Comment Section — NIEd
   हर page के नीचे comments + 👍❤️🔥 reactions।
   Backend: Firebase Firestore (public read approved-only,
   public create as "pending", admin approves via /admin-comments.html)
   ============================================================ */
(function(){
  var FIREBASE_CONFIG = {
    apiKey: "AIzaSyBalM_wgEhegoReyANDLiSHRvwi7n4zIUk",
    authDomain: "omkarsir-comments.firebaseapp.com",
    projectId: "omkarsir-comments",
    storageBucket: "omkarsir-comments.firebasestorage.app",
    messagingSenderId: "514558519516",
    appId: "1:514558519516:web:04b3847f97002ef2b46c19"
  };
  var SDK_VERSION = "10.12.2";

  function loadScript(src){
    return new Promise(function(resolve, reject){
      var s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function esc(t){
    return String(t == null ? "" : t)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  function timeAgo(ts){
    if(!ts) return "";
    var d = ts.toDate ? ts.toDate() : new Date(ts);
    var diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
    if(diffSec < 60) return "अभी अभी";
    var diffMin = Math.floor(diffSec / 60);
    if(diffMin < 60) return diffMin + " मिनट पहले";
    var diffHr = Math.floor(diffMin / 60);
    if(diffHr < 24) return diffHr + " घंटे पहले";
    var diffDay = Math.floor(diffHr / 24);
    if(diffDay < 30) return diffDay + " दिन पहले";
    return d.toLocaleDateString('hi-IN');
  }

  function injectStyle(){
    if(document.getElementById('nied-cmt-style')) return;
    var css = ''
      + '.cmt-sec{max-width:820px;margin:0 auto;padding:34px 6% 50px;font-family:"Hind",sans-serif}'
      + '.cmt-sec-title{font-family:"Poppins",sans-serif;font-size:19px;font-weight:800;color:#1B2A6B;margin-bottom:4px;display:flex;align-items:center;gap:8px}'
      + '.cmt-sec-sub{font-size:13px;color:#888;margin-bottom:20px}'
      + '.cmt-form{background:#fff;border:2px solid #E8EAF0;border-radius:14px;padding:18px 20px;margin-bottom:26px}'
      + '.cmt-form input, .cmt-form textarea{width:100%;border:1.5px solid #E8EAF0;border-radius:10px;padding:10px 14px;font-family:"Hind",sans-serif;font-size:14px;margin-bottom:10px;background:#F8F9FA;color:#1A1A2E}'
      + '.cmt-form input:focus, .cmt-form textarea:focus{outline:none;border-color:#FF6B00;background:#fff}'
      + '.cmt-form textarea{min-height:80px;resize:vertical}'
      + '.cmt-form-row{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}'
      + '.cmt-submit-btn{background:#FF6B00;color:#fff;border:none;padding:10px 22px;border-radius:30px;font-weight:700;font-size:13.5px;cursor:pointer;font-family:"Hind",sans-serif;transition:background .2s}'
      + '.cmt-submit-btn:hover{background:#E05500}'
      + '.cmt-submit-btn:disabled{background:#ccc;cursor:not-allowed}'
      + '.cmt-note{font-size:12px;color:#999}'
      + '.cmt-msg{font-size:13px;font-weight:600;padding:10px 14px;border-radius:10px;margin-bottom:14px;display:none}'
      + '.cmt-msg.show{display:block}'
      + '.cmt-msg.ok{background:#E8F5E9;color:#2E7D32;border:1.5px solid #A5D6A7}'
      + '.cmt-msg.err{background:#FFF0F0;color:#B71C1C;border:1.5px solid #FFB3B3}'
      + '.cmt-list{display:flex;flex-direction:column;gap:14px}'
      + '.cmt-card{background:#fff;border:1.5px solid #E8EAF0;border-radius:12px;padding:14px 18px}'
      + '.cmt-card-head{display:flex;align-items:center;gap:8px;margin-bottom:6px}'
      + '.cmt-avatar{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#1B2A6B,#2b3f9e);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}'
      + '.cmt-name{font-weight:700;font-size:13.5px;color:#1B2A6B}'
      + '.cmt-time{font-size:11.5px;color:#aaa;margin-left:auto;white-space:nowrap}'
      + '.cmt-text{font-size:14px;color:#333;line-height:1.6;margin:6px 0 10px;word-break:break-word}'
      + '.cmt-reactions{display:flex;gap:8px}'
      + '.cmt-react-btn{background:#F8F9FC;border:1.5px solid #E8EAF0;border-radius:20px;padding:4px 12px;font-size:12.5px;cursor:pointer;display:flex;align-items:center;gap:5px;transition:all .15s;font-family:"Hind",sans-serif;color:#555}'
      + '.cmt-react-btn:hover{border-color:#FF6B00}'
      + '.cmt-react-btn.reacted{background:#FFF3E8;border-color:#FFD0A0;color:#B45300;font-weight:700}'
      + '.cmt-react-btn:disabled{cursor:default;opacity:.85}'
      + '.cmt-empty{font-size:13.5px;color:#999;text-align:center;padding:20px 0}'
      + '.cmt-loading{font-size:13.5px;color:#999;text-align:center;padding:20px 0}'
      + '@media(max-width:640px){.cmt-form-row{flex-direction:column;align-items:stretch}.cmt-submit-btn{width:100%}}';
    var style = document.createElement('style');
    style.id = 'nied-cmt-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function pageId(){
    var p = location.pathname.split('/').pop();
    if(!p) p = 'index.html';
    return p;
  }

  function reactedKey(id, emoji){
    return 'nied_cmt_react_' + id + '_' + emoji;
  }

  function render(container, db, firestore, comments){
    var pid = pageId();
    var html = '';
    html += '<div class="cmt-sec-title">💬 Comments <span style="color:#999;font-weight:600;font-size:14px">(' + comments.length + ')</span></div>';
    html += '<div class="cmt-sec-sub">अपना सवाल या विचार यहाँ लिखें — तुरंत सबको दिखेगा</div>';

    html += '<div class="cmt-form">';
    html += '<div class="cmt-msg" id="cmtMsg"></div>';
    html += '<input type="text" id="cmtName" maxlength="40" placeholder="आपका नाम *" required>';
    html += '<textarea id="cmtText" maxlength="500" placeholder="अपना Comment लिखें... *" required></textarea>';
    html += '<div class="cmt-form-row"><span class="cmt-note">🏆 आपका Comment तुरंत live हो जाएगा</span><button class="cmt-submit-btn" id="cmtSubmitBtn">Comment भेजें →</button></div>';
    html += '</div>';

    html += '<div class="cmt-list" id="cmtList">';
    if(comments.length === 0){
      html += '<div class="cmt-empty">अभी तक कोई Comment नहीं — सबसे पहले आप लिखिए! 🎉</div>';
    } else {
      comments.forEach(function(c){
        var r = c.reactions || {like:0, heart:0, fire:0};
        var initial = (c.name || '?').trim().charAt(0).toUpperCase();
        html += '<div class="cmt-card" data-id="' + c.id + '">';
        html += '<div class="cmt-card-head"><div class="cmt-avatar">' + esc(initial) + '</div><div class="cmt-name">' + esc(c.name) + '</div><div class="cmt-time">' + timeAgo(c.createdAt) + '</div></div>';
        html += '<div class="cmt-text">' + esc(c.text) + '</div>';
        html += '<div class="cmt-reactions">';
        ['like','heart','fire'].forEach(function(emo){
          var symbol = emo === 'like' ? '👍' : (emo === 'heart' ? '❤️' : '🔥');
          var already = !!localStorage.getItem(reactedKey(c.id, emo));
          html += '<button class="cmt-react-btn' + (already ? ' reacted' : '') + '" data-emoji="' + emo + '" data-id="' + c.id + '"' + (already ? ' disabled' : '') + '>' + symbol + ' <span>' + (r[emo] || 0) + '</span></button>';
        });
        html += '</div></div>';
      });
    }
    html += '</div>';

    container.innerHTML = html;

    var msgEl = container.querySelector('#cmtMsg');
    var btn = container.querySelector('#cmtSubmitBtn');
    btn.addEventListener('click', function(){
      var nameEl = container.querySelector('#cmtName');
      var textEl = container.querySelector('#cmtText');
      var name = nameEl.value.trim();
      var text = textEl.value.trim();
      msgEl.className = 'cmt-msg';
      if(!name){ msgEl.textContent = '⚠️ कृपया अपना नाम लिखें।'; msgEl.className = 'cmt-msg err show'; return; }
      if(!text){ msgEl.textContent = '⚠️ कृपया अपना Comment लिखें।'; msgEl.className = 'cmt-msg err show'; return; }
      if(name.length > 40 || text.length > 500){ msgEl.textContent = '⚠️ Name/Comment बहुत लंबा है।'; msgEl.className = 'cmt-msg err show'; return; }
      btn.disabled = true;
      btn.textContent = 'भेजा जा रहा है...';
      firestore.addDoc(firestore.collection(db, 'comments'), {
        pageId: pid,
        name: name,
        text: text,
        status: 'approved',
        reactions: { like: 0, heart: 0, fire: 0 },
        createdAt: firestore.serverTimestamp()
      }).then(function(){
        nameEl.value = '';
        textEl.value = '';
        msgEl.textContent = '✅ धन्यवाद! आपका Comment Live हो गया है।';
        msgEl.className = 'cmt-msg ok show';
        btn.disabled = false;
        btn.textContent = 'Comment भेजें →';
      }).catch(function(err){
        msgEl.textContent = '❌ कुछ गलत हो गया, दोबारा प्रयास करें।';
        msgEl.className = 'cmt-msg err show';
        btn.disabled = false;
        btn.textContent = 'Comment भेजें →';
        console.error(err);
      });
    });

    container.querySelectorAll('.cmt-react-btn').forEach(function(rb){
      rb.addEventListener('click', function(){
        if(rb.disabled) return;
        var id = rb.getAttribute('data-id');
        var emo = rb.getAttribute('data-emoji');
        rb.disabled = true;
        rb.classList.add('reacted');
        var span = rb.querySelector('span');
        span.textContent = (parseInt(span.textContent, 10) || 0) + 1;
        localStorage.setItem(reactedKey(id, emo), '1');
        var field = 'reactions.' + emo;
        var update = {};
        update[field] = firestore.increment(1);
        firestore.updateDoc(firestore.doc(db, 'comments', id), update).catch(function(err){
          console.error(err);
        });
      });
    });
  }

  function init(){
    injectStyle();
    var footer = document.querySelector('footer');
    if(!footer) return;
    var section = document.createElement('section');
    section.className = 'cmt-sec';
    section.innerHTML = '<div class="cmt-loading">Comments लोड हो रहे हैं...</div>';
    footer.parentNode.insertBefore(section, footer);

    // Firebase SDK (~300 KB) is fetched only when the comments are near the
    // viewport, not on every page load.
    if('IntersectionObserver' in window){
      var io = new IntersectionObserver(function(entries){
        if(entries.some(function(en){ return en.isIntersecting; })){
          io.disconnect();
          loadComments(section);
        }
      }, {rootMargin: '600px 0px'});
      io.observe(section);
    } else {
      loadComments(section);
    }
  }

  function loadComments(section){
    Promise.all([
      loadScript('https://www.gstatic.com/firebasejs/' + SDK_VERSION + '/firebase-app-compat.js'),
      loadScript('https://www.gstatic.com/firebasejs/' + SDK_VERSION + '/firebase-firestore-compat.js')
    ]).then(function(){
      var app = firebase.initializeApp(FIREBASE_CONFIG);
      var dbRef = firebase.firestore();

      var firestore = {
        collection: function(_, name){ return dbRef.collection(name); },
        addDoc: function(colRef, data){ return colRef.add(data); },
        doc: function(_, colName, id){ return dbRef.collection(colName).doc(id); },
        updateDoc: function(docRef, data){ return docRef.update(data); },
        increment: firebase.firestore.FieldValue.increment,
        serverTimestamp: firebase.firestore.FieldValue.serverTimestamp
      };

      dbRef.collection('comments')
        .where('pageId', '==', pageId())
        .where('status', '==', 'approved')
        .orderBy('createdAt', 'desc')
        .limit(100)
        .get()
        .then(function(snap){
          var comments = [];
          snap.forEach(function(docSnap){
            var d = docSnap.data();
            comments.push({
              id: docSnap.id,
              name: d.name,
              text: d.text,
              reactions: d.reactions,
              createdAt: d.createdAt
            });
          });
          render(section, dbRef, firestore, comments);
        })
        .catch(function(err){
          console.error(err);
          render(section, dbRef, firestore, []);
        });
    }).catch(function(err){
      console.error('Firebase SDK load failed', err);
      section.innerHTML = '';
    });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
