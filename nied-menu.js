(function(){
  function esc(s){
    var d = document.createElement('div');
    d.textContent = (s===null||s===undefined) ? '' : String(s);
    return d.innerHTML;
  }

  function injectStyles(){
    if(document.getElementById('nied-menu-style')) return;
    var css = '#nied-navbar{font-family:"Noto Sans Devanagari",Arial,sans-serif;position:sticky;top:0;z-index:9999;}'
      + '.nied-nav-inner{background:#1B2A6B;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:10px 20px;flex-wrap:wrap;box-shadow:0 2px 10px rgba(0,0,0,.18);position:relative;}'
      + '.nied-logo{color:#fff;font-weight:700;font-size:1.05rem;text-decoration:none;}'
      + '.nied-burger{display:none;background:none;border:none;color:#fff;font-size:1.6rem;cursor:pointer;line-height:1;padding:4px 8px;}'
      + '.nied-menu{list-style:none;display:flex;gap:4px;margin:0;padding:0;align-items:center;}'
      + '.nied-menu li{position:relative;}'
      + '.nied-top-link{display:block;color:#fff;text-decoration:none;padding:11px 14px;border-radius:8px;font-weight:600;font-size:.92rem;cursor:pointer;}'
      + '.nied-top-link:hover{background:#FF6B00;}'
      + '.nied-caret{font-size:.7em;}'
      + '.nied-dropdown{display:none;position:absolute;top:100%;left:0;background:#fff;min-width:230px;list-style:none;margin:6px 0 0;padding:6px;border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);z-index:100;}'
      + '.nied-has-dropdown.open .nied-dropdown{display:block;}'
      + '.nied-dropdown li a{display:block;padding:9px 12px;color:#1B2A6B;text-decoration:none;border-radius:7px;font-size:.9rem;font-weight:500;}'
      + '.nied-dropdown li a:hover{background:#FFF1E6;color:#FF6B00;}'
      + '@media (max-width:880px){'
      + '.nied-burger{display:block;}'
      + '.nied-menu{display:none;flex-direction:column;width:100%;align-items:stretch;background:#1B2A6B;position:absolute;left:0;top:100%;padding:8px 14px 14px;box-shadow:0 10px 24px rgba(0,0,0,.25);max-height:80vh;overflow-y:auto;}'
      + '.nied-menu.open{display:flex;}'
      + '.nied-menu > li{width:100%;}'
      + '.nied-top-link{padding:12px 10px;border-bottom:1px solid rgba(255,255,255,.12);}'
      + '.nied-dropdown{position:static;box-shadow:none;background:#24398f;margin:0 0 0 12px;width:calc(100% - 12px);border-radius:8px;}'
      + '.nied-dropdown li a{color:#fff;}'
      + '.nied-dropdown li a:hover{background:#FF6B00;color:#fff;}'
      + '}';
    var style = document.createElement('style');
    style.id = 'nied-menu-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function render(mount, menu){
    injectStyles();
    var logo = menu.logo || {text:'New India Education', url:'/'};
    var html = '<div class="nied-nav-inner"><a class="nied-logo" href="' + esc(logo.url) + '">' + esc(logo.text) + '</a>'
      + '<button class="nied-burger" id="niedBurger" aria-label="Menu">&#9776;</button>'
      + '<ul class="nied-menu" id="niedMenuList">';
    (menu.items || []).forEach(function(item){
      if(item.type === 'dropdown'){
        html += '<li class="nied-has-dropdown"><a class="nied-top-link">' + esc(item.label) + ' <span class="nied-caret">&#9662;</span></a><ul class="nied-dropdown">';
        (item.children || []).forEach(function(ch){
          html += '<li><a href="' + esc(ch.url) + '">' + esc(ch.label) + '</a></li>';
        });
        html += '</ul></li>';
      } else {
        html += '<li><a class="nied-top-link" href="' + esc(item.url) + '">' + esc(item.label) + '</a></li>';
      }
    });
    html += '</ul></div>';
    mount.innerHTML = html;

    var burger = mount.querySelector('#niedBurger');
    var list = mount.querySelector('#niedMenuList');
    if(burger){
      burger.addEventListener('click', function(){ list.classList.toggle('open'); });
    }
    mount.querySelectorAll('.nied-has-dropdown > a.nied-top-link').forEach(function(a){
      a.addEventListener('click', function(e){
        e.preventDefault();
        var parent = a.parentElement;
        var wasOpen = parent.classList.contains('open');
        mount.querySelectorAll('.nied-has-dropdown.open').forEach(function(li){ li.classList.remove('open'); });
        if(!wasOpen) parent.classList.add('open');
      });
    });
    document.addEventListener('click', function(e){
      if(!mount.contains(e.target)){
        mount.querySelectorAll('.nied-has-dropdown.open').forEach(function(li){ li.classList.remove('open'); });
      }
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
