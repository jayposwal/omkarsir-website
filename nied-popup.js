/**
 * New India Education (NIEd) - Omkar Sir Website
 * Timed Conversion Popup (RAS Foundation Course 2026 Offer)
 * 
 * Features:
 * - Triggers 15 seconds after page load
 * - Interactive 2-image carousel (Meta poster & App doodle poster)
 * - Live countdown urgency timer (ticks down from 10:00)
 * - Direct Play Store app download redirection on click
 * - Close button (X), ESC key, backdrop click to close
 * - Smart cooldown storage (2 hours) so students aren't disrupted
 * - 100% responsive on all mobile devices & desktops
 */
(function() {
  'use strict';

  var CONFIG = {
    delayMs: 15000, // 15 seconds
    playStoreUrl: 'https://play.google.com/store/apps/details?id=co.april2019.techa',
    storageKey: 'nied_popup_closed_time',
    cooldownHours: 2, // cooldown if closed
    slides: [
      {
        webp: '/assets/popup/ras-foundation-meta.webp',
        jpg: '/assets/popup/ras-foundation-meta.jpg',
        alt: 'RAS Foundation Course 2026 - Pre + Mains'
      },
      {
        webp: '/assets/popup/ras-foundation-app.webp',
        jpg: '/assets/popup/ras-foundation-app.jpg',
        alt: 'RAS Complete Course - New India Education'
      }
    ]
  };

  // Check cooldown unless forced with ?popup=1 or ?testpopup=1
  var urlParams = new URLSearchParams(window.location.search);
  var isForceTest = urlParams.has('popup') || urlParams.has('testpopup');

  function isCoolingDown() {
    if (isForceTest) return false;
    try {
      var closedTime = localStorage.getItem(CONFIG.storageKey);
      if (!closedTime) return false;
      var elapsedMs = Date.now() - parseInt(closedTime, 10);
      return elapsedMs < CONFIG.cooldownHours * 60 * 60 * 1000;
    } catch (e) {
      return false;
    }
  }

  function markClosed() {
    try {
      localStorage.setItem(CONFIG.storageKey, Date.now().toString());
    } catch (e) {}
  }

  function injectStyles() {
    if (document.getElementById('nied-popup-styles')) return;
    var style = document.createElement('style');
    style.id = 'nied-popup-styles';
    style.textContent = [
      '@keyframes niedPopupFadeIn { from { opacity: 0; } to { opacity: 1; } }',
      '@keyframes niedBadgePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.04); } }',
      '#nied-popup-overlay {',
      '  position: fixed; inset: 0; z-index: 99999999;',
      '  background: rgba(10, 15, 29, 0.75);',
      '  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);',
      '  display: flex; align-items: center; justify-content: center;',
      '  padding: 16px;',
      '  opacity: 0; visibility: hidden;',
      '  transition: opacity 0.3s ease, visibility 0.3s ease;',
      '  font-family: "Noto Sans Devanagari", "Hind", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;',
      '  box-sizing: border-box;',
      '  overflow-y: auto;',
      '  -webkit-overflow-scrolling: touch;',
      '}',
      '#nied-popup-overlay * { box-sizing: border-box; }',
      '#nied-popup-overlay.active {',
      '  opacity: 1; visibility: visible;',
      '}',
      '#nied-popup-card {',
      '  position: relative;',
      '  width: 100%; max-width: 390px;',
      '  background: #ffffff;',
      '  border-radius: 20px;',
      '  box-shadow: 0 25px 65px -12px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.2);',
      '  overflow: hidden;',
      '  transform: scale(0.92) translateY(14px);',
      '  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);',
      '  margin: auto;',
      '  display: flex; flex-direction: column;',
      '  flex-shrink: 0;',
      '}',
      '#nied-popup-overlay.active #nied-popup-card {',
      '  transform: scale(1) translateY(0);',
      '}',
      '#nied-popup-close {',
      '  position: absolute; top: 10px; right: 10px;',
      '  width: 34px; height: 34px; border-radius: 50%;',
      '  background: #0f172a;',
      '  border: 2px solid #ffffff;',
      '  color: #ffffff;',
      '  display: flex; align-items: center; justify-content: center;',
      '  cursor: pointer; z-index: 9999;',
      '  transition: transform 0.2s ease, background 0.2s ease;',
      '  box-shadow: 0 4px 14px rgba(0,0,0,0.6);',
      '  padding: 0; outline: none;',
      '}',
      '#nied-popup-close svg { width: 14px; height: 14px; stroke: #ffffff; stroke-width: 3; display: block; }',
      '#nied-popup-close:hover {',
      '  background: #dc2626;',
      '  border-color: #ffffff;',
      '  transform: rotate(90deg) scale(1.1);',
      '}',
      '.nied-slider-wrap {',
      '  position: relative; width: 100%;',
      '  height: 185px;',
      '  background: #0b1329;',
      '  overflow: hidden; cursor: pointer;',
      '}',
      '.nied-slide {',
      '  position: absolute; inset: 0;',
      '  opacity: 0; visibility: hidden;',
      '  transition: opacity 0.45s ease-in-out, visibility 0.45s ease-in-out;',
      '  display: flex; align-items: center; justify-content: center;',
      '}',
      '.nied-slide.active {',
      '  opacity: 1; visibility: visible;',
      '  z-index: 1;',
      '}',
      '.nied-slide picture, .nied-slide img {',
      '  width: 100%; height: 100%;',
      '  object-fit: contain;',
      '  background: #0b1329;',
      '  display: block;',
      '}',
      '.nied-slider-dots {',
      '  position: absolute; bottom: 6px; left: 0; right: 0;',
      '  display: flex; justify-content: center; align-items: center;',
      '  z-index: 10;',
      '}',
      '.nied-dots-pill {',
      '  display: flex; align-items: center; gap: 5px;',
      '  background: rgba(15, 23, 42, 0.7);',
      '  backdrop-filter: blur(4px);',
      '  padding: 3px 8px; border-radius: 999px;',
      '}',
      '.nied-dot {',
      '  width: 6px; height: 6px; border-radius: 50%;',
      '  background: rgba(255, 255, 255, 0.4);',
      '  cursor: pointer; transition: all 0.2s ease;',
      '  border: none; padding: 0;',
      '}',
      '.nied-dot.active {',
      '  width: 16px; border-radius: 8px;',
      '  background: #38bdf8;',
      '}',
      '.nied-popup-body {',
      '  padding: 10px 16px 14px 16px;',
      '  text-align: center;',
      '}',
      '.nied-popup-badge {',
      '  display: inline-flex; align-items: center; gap: 4px;',
      '  background: #fff1f2; color: #e11d48;',
      '  font-size: 0.7rem; font-weight: 800;',
      '  padding: 3px 10px; border-radius: 999px;',
      '  border: 1px solid #fecdd3;',
      '  letter-spacing: 0.3px;',
      '  margin-bottom: 6px;',
      '  animation: niedBadgePulse 2.4s infinite;',
      '}',
      '.nied-popup-title {',
      '  font-size: 1.15rem; font-weight: 800; color: #0f172a;',
      '  margin: 0 0 2px 0; line-height: 1.25;',
      '}',
      '.nied-popup-subtitle {',
      '  font-size: 0.82rem; font-weight: 600; color: #475569;',
      '  margin: 0 0 8px 0; line-height: 1.35;',
      '}',
      '.nied-popup-pricing {',
      '  display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px;',
      '  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;',
      '  padding: 6px 6px; margin-bottom: 8px;',
      '}',
      '.nied-price-box {',
      '  display: flex; flex-direction: column; align-items: center;',
      '  justify-content: center;',
      '}',
      '.nied-price-box:not(:last-child) {',
      '  border-right: 1px dashed #cbd5e1;',
      '}',
      '.nied-price-label { font-size: 0.62rem; color: #64748b; font-weight: 700; margin-bottom: 1px; }',
      '.nied-price-val { font-size: 0.9rem; font-weight: 800; color: #0f172a; line-height: 1.2; }',
      '.nied-price-strike { text-decoration: line-through; color: #94a3b8; font-weight: 600; }',
      '.nied-price-highlight { color: #0284c7; }',
      '.nied-price-highlight-green { color: #16a34a; }',
      '.nied-popup-timer-row {',
      '  display: flex; align-items: center; justify-content: center; gap: 7px;',
      '  font-size: 0.82rem; font-weight: 700; color: #334155;',
      '  margin-bottom: 8px;',
      '}',
      '.nied-timer-pill {',
      '  background: #dc2626; color: #ffffff;',
      '  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;',
      '  font-weight: 800; font-size: 0.95rem; letter-spacing: 1px;',
      '  padding: 2px 7px; border-radius: 6px;',
      '  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.35);',
      '  display: inline-block;',
      '}',
      '.nied-popup-cta {',
      '  display: flex; align-items: center; justify-content: center; gap: 6px;',
      '  width: 100%; padding: 11px 14px;',
      '  background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);',
      '  color: #ffffff; text-decoration: none;',
      '  font-size: 0.96rem; font-weight: 800;',
      '  border-radius: 12px;',
      '  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.42);',
      '  transition: transform 0.16s ease, box-shadow 0.16s ease;',
      '  border: none; cursor: pointer;',
      '  letter-spacing: 0.2px;',
      '}',
      '.nied-popup-cta:hover {',
      '  transform: translateY(-2px);',
      '  box-shadow: 0 10px 26px rgba(37, 99, 235, 0.55);',
      '}',
      '.nied-popup-cta:active {',
      '  transform: translateY(0);',
      '}',
      '.nied-popup-trust {',
      '  font-size: 0.68rem; color: #94a3b8; font-weight: 600;',
      '  margin-top: 6px; display: flex; align-items: center; justify-content: center; gap: 4px;',
      '}',
      '@media (max-width: 480px) {',
      '  #nied-popup-overlay { padding: 12px; align-items: flex-start; }',
      '  #nied-popup-card { border-radius: 18px; max-width: 350px; margin: 14px auto; }',
      '  .nied-slider-wrap { height: 160px; }',
      '  .nied-popup-body { padding: 8px 12px 12px 12px; }',
      '  .nied-popup-title { font-size: 1.08rem; }',
      '  .nied-popup-subtitle { font-size: 0.78rem; margin-bottom: 6px; }',
      '  .nied-popup-pricing { padding: 5px 6px; margin-bottom: 6px; }',
      '  .nied-price-val { font-size: 0.84rem; }',
      '  .nied-price-label { font-size: 0.58rem; }',
      '  .nied-popup-timer-row { font-size: 0.76rem; margin-bottom: 7px; }',
      '  .nied-timer-pill { font-size: 0.9rem; padding: 1px 6px; }',
      '  .nied-popup-cta { font-size: 0.9rem; padding: 10px 12px; border-radius: 11px; }',
      '  .nied-popup-trust { font-size: 0.64rem; margin-top: 4px; }',
      '}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function createPopupDOM() {
    var overlay = document.createElement('div');
    overlay.id = 'nied-popup-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'RAS Foundation Course Special Offer');

    var slidesHtml = CONFIG.slides.map(function(s, idx) {
      return (
        '<div class="nied-slide' + (idx === 0 ? ' active' : '') + '" data-index="' + idx + '">' +
          '<picture>' +
            '<source srcset="' + s.webp + '" type="image/webp">' +
            '<img src="' + s.jpg + '" alt="' + s.alt + '" loading="eager">' +
          '</picture>' +
        '</div>'
      );
    }).join('');

    var dotsHtml = CONFIG.slides.map(function(_, idx) {
      return '<button class="nied-dot' + (idx === 0 ? ' active' : '') + '" data-index="' + idx + '" aria-label="Slide ' + (idx + 1) + '"></button>';
    }).join('');

    overlay.innerHTML =
      '<div id="nied-popup-card">' +
        '<div class="nied-slider-wrap" id="nied-slider">' +
          slidesHtml +
          '<div class="nied-slider-dots"><div class="nied-dots-pill">' + dotsHtml + '</div></div>' +
        '</div>' +
        '<button id="nied-popup-close" aria-label="पॉपअप बंद करें" title="Close"><svg viewBox="0 0 24 24" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>' +
        '<div class="nied-popup-body">' +
          '<div class="nied-popup-badge">🔥 SPECIAL DISCOUNT UNLOCKED!</div>' +
          '<h3 class="nied-popup-title">RAS Foundation Course 2026</h3>' +
          '<p class="nied-popup-subtitle">🎯 Pre + Mains सम्पूर्ण तैयारी — एक ही Course में!</p>' +
          '<div class="nied-popup-pricing">' +
            '<div class="nied-price-box">' +
              '<span class="nied-price-label">MRP</span>' +
              '<span class="nied-price-val nied-price-strike">₹25,000</span>' +
            '</div>' +
            '<div class="nied-price-box">' +
              '<span class="nied-price-label">2 Years</span>' +
              '<span class="nied-price-val nied-price-highlight">₹4,999</span>' +
            '</div>' +
            '<div class="nied-price-box">' +
              '<span class="nied-price-label">5 Years</span>' +
              '<span class="nied-price-val nied-price-highlight-green">₹5,999</span>' +
            '</div>' +
          '</div>' +
          '<div class="nied-popup-timer-row">' +
            '<span>ऑफ़र समाप्त होने में:</span>' +
            '<span class="nied-timer-pill" id="nied-countdown">09:59</span>' +
          '</div>' +
          '<a href="' + CONFIG.playStoreUrl + '" target="_blank" rel="noopener noreferrer" class="nied-popup-cta" id="nied-cta-btn">' +
            '<span>📲</span> <span>अभी App डाउनलोड करें & जॉइन करें</span>' +
          '</a>' +
          '<div class="nied-popup-trust">' +
            '<span>⭐ 6 लाख+ सफल विद्यार्थी</span>' +
            '<span>•</span>' +
            '<span>न्यू इंडिया एजुकेशन</span>' +
          '</div>' +
        '</div>' +
      '</div>';

    document.body.appendChild(overlay);
    return overlay;
  }

  function initPopup() {
    if (isCoolingDown()) return;

    injectStyles();
    var overlay = createPopupDOM();
    var closeBtn = document.getElementById('nied-popup-close');
    var sliderWrap = document.getElementById('nied-slider');
    var slides = overlay.querySelectorAll('.nied-slide');
    var dots = overlay.querySelectorAll('.nied-dot');
    var timerEl = document.getElementById('nied-countdown');

    var currentSlide = 0;
    var slideInterval = null;
    var timerInterval = null;

    function goToSlide(idx) {
      slides[currentSlide].classList.remove('active');
      dots[currentSlide].classList.remove('active');
      currentSlide = (idx + slides.length) % slides.length;
      slides[currentSlide].classList.add('active');
      dots[currentSlide].classList.add('active');
    }

    function startSlider() {
      if (slideInterval) clearInterval(slideInterval);
      slideInterval = setInterval(function() {
        goToSlide(currentSlide + 1);
      }, 3500);
    }

    dots.forEach(function(dot) {
      dot.addEventListener('click', function(e) {
        e.stopPropagation();
        var idx = parseInt(dot.getAttribute('data-index'), 10);
        goToSlide(idx);
        startSlider();
      });
    });

    // Clicking the banner also goes to Play Store
    sliderWrap.addEventListener('click', function(e) {
      if (e.target.classList.contains('nied-dot')) return;
      window.open(CONFIG.playStoreUrl, '_blank', 'noopener,noreferrer');
    });

    // Countdown Timer (10 mins)
    var totalSeconds = 9 * 60 + 59;
    function updateTimer() {
      if (!timerEl) return;
      var mins = Math.floor(totalSeconds / 60);
      var secs = totalSeconds % 60;
      timerEl.textContent = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
      if (totalSeconds > 0) {
        totalSeconds--;
      } else {
        totalSeconds = 5 * 60; // reset to 5 mins if zero
      }
    }

    function show() {
      overlay.classList.add('active');
      startSlider();
      updateTimer();
      if (!timerInterval) {
        timerInterval = setInterval(updateTimer, 1000);
      }
    }

    function hide() {
      overlay.classList.remove('active');
      if (slideInterval) clearInterval(slideInterval);
      if (timerInterval) clearInterval(timerInterval);
      markClosed();
    }

    closeBtn.addEventListener('click', hide);

    // Close when clicking outside modal card
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        hide();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && overlay.classList.contains('active')) {
        hide();
      }
    });

    // Trigger after 15 seconds (or immediately if force test)
    var delay = isForceTest ? 250 : CONFIG.delayMs;
    setTimeout(show, delay);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPopup);
  } else {
    initPopup();
  }
})();
