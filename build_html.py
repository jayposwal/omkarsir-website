# -*- coding: utf-8 -*-
import json, html

with open('/Users/omkarsingh/Desktop/omkarsir-website/revise_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

json_data_str = json.dumps(questions, ensure_ascii=False)

html_content = f'''<!DOCTYPE html>
<html lang="hi" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>RAS Revise — RPSC Previous Year Questions & Active Revision | Omkar Sir</title>
<meta name="description" content="RAS Pre और RPSC परीक्षाओं के लिए Previous Year Questions (PYQs) और महत्वपूर्ण प्रश्नों का सम्पूर्ण Active Revision System। विषय-वार प्रश्न, तुरंत उत्तर और प्रमाणिक विस्तृत व्याख्या।">
<meta name="keywords" content="RAS PYQ, RPSC RAS Pre 2026, RAS Revision, Self Revise, Omkar Sir, New India Education, Rajasthan GK MCQs, RAS Prelims Practice">
<meta name="author" content="Omkar Singh Gurjar">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://omkarsir.com/revise">

<!-- Favicons & Manifest -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#1B2A6B" id="metaThemeColor">

<!-- Open Graph / Social -->
<meta property="og:title" content="RAS Revise — Previous Year Questions & Active Revision | Omkar Sir">
<meta property="og:description" content="RAS Pre और RPSC परीक्षाओं के लिए Previous Year Questions का एक्टिव रिवीजन सिस्टम। स्क्रॉल करें, हल करें, तुरंत व्याख्या देखें।">
<meta property="og:type" content="website">
<meta property="og:url" content="https://omkarsir.com/revise">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:locale" content="hi_IN">
<meta property="og:site_name" content="Omkar Sir | New India Education">
<meta name="twitter:card" content="summary_large_image">

<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-WCK16L4WZX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-WCK16L4WZX');
</script>

<!-- Fonts & Instant Theme Loader -->
<link rel="preload" href="/assets/fonts/hind-400-devanagari.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/nied-fonts.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>
  (function(){{
    var t = 'light';
    try {{
      var saved = localStorage.getItem('omkarsir_revise_theme');
      if (saved === 'dark' || (!saved && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
        t = 'dark';
      }}
    }} catch(e) {{}}
    document.documentElement.setAttribute('data-theme', t);
  }})();
</script>

<style>
/* CSS RESET & VARIABLES (SelfRevise inspired clean warm palette) */
:root {{
  --bg-base: #FBF9F5;
  --bg-surface: #FFFFFF;
  --bg-subtle: #F3EFE6;
  --bg-hover: #EFE9DD;
  --border-light: #E7E0D3;
  --border-strong: #D5CBBA;
  --text-main: #1F1D1A;
  --text-soft: #635E55;
  --text-muted: #8F887C;
  --brand-navy: #1B2A6B;
  --brand-orange: #FF6B00;
  --brand-orange-light: #FFF0E5;
  --color-correct: #16A34A;
  --bg-correct: #DCFCE7;
  --border-correct: #86EFAC;
  --color-wrong: #DC2626;
  --bg-wrong: #FEE2E2;
  --border-wrong: #FCA5A5;
  --gold: #D97706;
  --bg-gold: #FEF3C7;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 14px rgba(0,0,0,0.06);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  --font-sans: 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}}

[data-theme="dark"] {{
  --bg-base: #131110;
  --bg-surface: #1E1B18;
  --bg-subtle: #292522;
  --bg-hover: #342F2C;
  --border-light: #342F2B;
  --border-strong: #48413B;
  --text-main: #F5F2EB;
  --text-soft: #A8A196;
  --text-muted: #736C61;
  --brand-navy: #4B6BFB;
  --brand-orange: #FF801F;
  --brand-orange-light: #3B2312;
  --color-correct: #22C55E;
  --bg-correct: #052E16;
  --border-correct: #166534;
  --color-wrong: #EF4444;
  --bg-wrong: #450A0A;
  --border-wrong: #991B1B;
  --gold: #FBBF24;
  --bg-gold: #382404;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 14px rgba(0,0,0,0.4);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font-sans);
  background-color: var(--bg-base);
  color: var(--text-main);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  transition: background-color 0.2s ease, color 0.2s ease;
}}

/* APP CONTAINER */
.app-wrapper {{
  max-width: 780px;
  margin: 0 auto;
  padding: 0 16px 120px 16px;
}}

/* STICKY TOP HEADER */
.sticky-top-wrap {{
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--bg-base);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 20px;
}}

.header-inner {{
  max-width: 780px;
  margin: 0 auto;
  padding: 12px 16px 10px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}

.brand-section {{
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}}

.brand-icon {{
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, var(--brand-navy), #0B1647);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  box-shadow: 0 2px 6px rgba(27,42,107,0.25);
  flex-shrink: 0;
}}

.brand-meta h1 {{
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
  display: flex;
  align-items: center;
  gap: 6px;
}}

.brand-meta h1 span.tag {{
  font-size: 10px;
  background-color: var(--brand-orange-light);
  color: var(--brand-orange);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-weight: 700;
}}

.brand-meta p {{
  font-size: 12px;
  color: var(--text-soft);
  margin-top: 1px;
}}

.header-actions {{
  display: flex;
  align-items: center;
  gap: 6px;
}}

.btn-icon {{
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border-light);
  background-color: var(--bg-surface);
  color: var(--text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 15px;
  transition: all 0.15s ease;
  position: relative;
}}
.btn-icon:hover {{
  background-color: var(--bg-hover);
  border-color: var(--border-strong);
}}

.btn-icon .badge {{
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: var(--brand-orange);
  color: #fff;
  font-size: 9px;
  font-family: var(--font-mono);
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 10px;
  display: none;
}}

/* STATS STRIP */
.stats-strip {{
  max-width: 780px;
  margin: 0 auto;
  padding: 6px 16px 12px 16px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}}

.stat-pill {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 6px 8px;
  text-align: center;
}}

.stat-val {{
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.2;
}}

.stat-lbl {{
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 2px;
}}

/* THIN PROGRESS LINE */
.progress-line-track {{
  height: 3px;
  width: 100%;
  background-color: var(--border-light);
  overflow: hidden;
}}

.progress-line-fill {{
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--brand-navy), var(--brand-orange));
  transition: width 0.3s ease;
}}

/* SEARCH BAR OVERLAY / COLLAPSIBLE */
.search-container {{
  display: none;
  padding: 0 16px 12px 16px;
  max-width: 780px;
  margin: 0 auto;
}}

.search-container.active {{
  display: block;
}}

.search-input-box {{
  position: relative;
  width: 100%;
}}

.search-input-box input {{
  width: 100%;
  padding: 10px 36px 10px 38px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-strong);
  background-color: var(--bg-surface);
  color: var(--text-main);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
}}
.search-input-box input:focus {{
  border-color: var(--brand-navy);
  box-shadow: 0 0 0 3px rgba(27,42,107,0.1);
}}

.search-input-box .search-icon {{
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 14px;
}}

.search-input-box .clear-search {{
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  display: none;
}}

/* HORIZONTAL SUBJECT PILLS BAR */
.subject-tabs-wrap {{
  overflow-x: auto;
  white-space: nowrap;
  padding-bottom: 8px;
  margin-bottom: 12px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}}
.subject-tabs-wrap::-webkit-scrollbar {{
  display: none;
}}

.subject-tabs {{
  display: inline-flex;
  gap: 6px;
}}

.subj-chip {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--text-soft);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}}
.subj-chip:hover {{
  background-color: var(--bg-hover);
  color: var(--text-main);
}}
.subj-chip.active {{
  background-color: var(--brand-navy);
  color: #fff;
  border-color: var(--brand-navy);
  font-weight: 600;
}}

/* STATUS FILTER BAR */
.status-filters {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}}

.status-pills {{
  display: flex;
  gap: 6px;
}}

.status-chip {{
  background-color: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s ease;
}}
.status-chip:hover {{
  color: var(--text-main);
}}
.status-chip.active {{
  background-color: var(--bg-subtle);
  color: var(--text-main);
  border-color: var(--border-light);
  font-weight: 600;
}}

.results-count {{
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}

/* QUESTION CARD */
.question-feed {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}

.question-card {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  position: relative;
}}
.question-card:hover {{
  border-color: var(--border-strong);
}}

/* CARD HEADER */
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}}

.card-badges {{
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}}

.badge-num {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  background-color: var(--bg-subtle);
  color: var(--text-main);
  padding: 3px 8px;
  border-radius: 6px;
}}

.badge-subj {{
  font-size: 11px;
  font-weight: 500;
  color: var(--brand-navy);
  background-color: rgba(27,42,107,0.08);
  padding: 3px 8px;
  border-radius: 6px;
}}

[data-theme="dark"] .badge-subj {{
  background-color: rgba(75,107,251,0.15);
  color: #8CA0FC;
}}

.badge-exam {{
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}}

.btn-star {{
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: var(--text-muted);
  padding: 2px 6px;
  border-radius: 6px;
  transition: all 0.15s ease;
  line-height: 1;
}}
.btn-star:hover {{
  color: var(--gold);
}}
.btn-star.starred {{
  color: var(--gold);
}}

/* QUESTION TEXT */
.question-stem {{
  font-size: 16px;
  font-weight: 600;
  line-height: 1.65;
  color: var(--text-main);
  margin-bottom: 16px;
}}

/* OPTIONS LIST */
.options-list {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}

.option-btn {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 11px 14px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  width: 100%;
  color: var(--text-main);
  font-family: var(--font-sans);
  font-size: 14.5px;
  line-height: 1.5;
  outline: none;
}}
.option-btn:hover:not(.disabled) {{
  background-color: var(--bg-hover);
  border-color: var(--border-strong);
}}

.option-key {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  background-color: var(--bg-subtle);
  color: var(--text-soft);
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
}}

.option-text {{
  flex: 1;
}}

/* OPTION STATES: CORRECT & WRONG */
.option-btn.state-correct {{
  background-color: var(--bg-correct) !important;
  border-color: var(--border-correct) !important;
  color: var(--color-correct) !important;
  font-weight: 600;
}}
.option-btn.state-correct .option-key {{
  background-color: var(--color-correct);
  color: #fff;
}}

.option-btn.state-wrong {{
  background-color: var(--bg-wrong) !important;
  border-color: var(--border-wrong) !important;
  color: var(--color-wrong) !important;
}}
.option-btn.state-wrong .option-key {{
  background-color: var(--color-wrong);
  color: #fff;
}}

.option-btn.disabled {{
  cursor: default;
}}

/* EXPLANATION ACCORDION */
.explanation-box {{
  margin-top: 16px;
  border-top: 1px dashed var(--border-light);
  padding-top: 14px;
  display: none;
}}

.explanation-box.visible {{
  display: block;
  animation: fadeIn 0.25s ease-out;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(-4px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.exp-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}}

.exp-badge-correct {{
  font-size: 12px;
  font-weight: 700;
  color: var(--color-correct);
  background-color: var(--bg-correct);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}

.exp-toggle-btn {{
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  text-decoration: underline;
}}

.exp-body {{
  font-size: 13.5px;
  color: var(--text-soft);
  line-height: 1.7;
  background-color: var(--bg-subtle);
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--brand-navy);
}}

.exp-body strong {{
  color: var(--text-main);
}}

/* EMPTY STATE */
.empty-state {{
  text-align: center;
  padding: 48px 16px;
  color: var(--text-muted);
  display: none;
}}
.empty-state.active {{
  display: block;
}}
.empty-state h3 {{
  font-size: 18px;
  margin-bottom: 6px;
  color: var(--text-main);
}}

/* FLOATING BAR (NEXT UNATTEMPTED) */
.floating-actions {{
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99;
  display: flex;
  align-items: center;
  gap: 10px;
}}

.btn-floating {{
  background: linear-gradient(135deg, var(--brand-navy), #0B1647);
  color: #fff;
  border: none;
  padding: 11px 20px;
  border-radius: var(--radius-full);
  font-size: 13.5px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 4px 18px rgba(0,0,0,0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  white-space: nowrap;
}}
.btn-floating:hover {{
  transform: scale(1.02);
  box-shadow: 0 6px 22px rgba(0,0,0,0.3);
}}
.btn-floating:active {{
  transform: scale(0.98);
}}

.btn-scroll-top {{
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-strong);
  color: var(--text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  font-size: 16px;
}}

/* MODAL RESET CONFIRMATION */
.modal-overlay {{
  position: fixed;
  inset: 0;
  background-color: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 16px;
}}
.modal-overlay.open {{
  display: flex;
}}

.modal-box {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  max-width: 400px;
  width: 100%;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.25);
  text-align: center;
}}

.modal-box h3 {{
  font-size: 18px;
  margin-bottom: 8px;
}}

.modal-box p {{
  font-size: 13.5px;
  color: var(--text-soft);
  margin-bottom: 20px;
}}

.modal-btns {{
  display: flex;
  gap: 10px;
}}

.modal-btns button {{
  flex: 1;
  padding: 10px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}}

.btn-cancel {{
  background-color: var(--bg-subtle);
  color: var(--text-main);
}}

.btn-confirm-reset {{
  background-color: var(--color-wrong);
  color: #fff;
}}

/* FOOTER BRAND BANNER */
.ecosystem-footer {{
  margin-top: 48px;
  background: linear-gradient(135deg, rgba(27,42,107,0.05), rgba(255,107,0,0.06));
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 24px;
  text-align: center;
}}

.ecosystem-footer h4 {{
  font-size: 16px;
  font-weight: 700;
  color: var(--brand-navy);
  margin-bottom: 4px;
}}

[data-theme="dark"] .ecosystem-footer h4 {{
  color: #8CA0FC;
}}

.ecosystem-footer p {{
  font-size: 13px;
  color: var(--text-soft);
  margin-bottom: 16px;
}}

.footer-links {{
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}}

.btn-app-download {{
  background-color: var(--brand-orange);
  color: #fff;
  padding: 9px 18px;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}

.btn-whatsapp {{
  background-color: #25D366;
  color: #fff;
  padding: 9px 18px;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}}

.btn-home-link {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-strong);
  color: var(--text-main);
  padding: 9px 18px;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}}

@media (max-width: 600px) {{
  .stats-strip {{
    grid-template-columns: repeat(2, 1fr);
  }}
  .question-card {{
    padding: 16px;
  }}
  .question-stem {{
    font-size: 15px;
  }}
  .option-btn {{
    font-size: 13.5px;
    padding: 10px 12px;
  }}
}}
</style>
</head>
<body>

<!-- STICKY TOP WRAPPER -->
<div class="sticky-top-wrap">
  <div class="header-inner">
    <a href="/" class="brand-section" title="मुख्य वेबसाइट पर जाएँ">
      <div class="brand-icon">✓</div>
      <div class="brand-meta">
        <h1>RAS REVISE <span class="tag">ACTIVE</span></h1>
        <p>Omkar Sir • New India Education</p>
      </div>
    </a>

    <div class="header-actions">
      <button class="btn-icon" id="searchToggleBtn" title="खोजें (Search)" aria-label="खोजें">
        🔍
      </button>
      <button class="btn-icon" id="bookmarkFilterBtn" title="सहेजे गए प्रश्न (Starred)" aria-label="सहेजे गए प्रश्न">
        ⭐
        <span class="badge" id="starBadgeCount">0</span>
      </button>
      <button class="btn-icon" id="themeToggleBtn" title="थीम बदलें" aria-label="थीम बदलें">
        🌓
      </button>
      <button class="btn-icon" id="resetBtn" title="प्रगति रीसेट करें" aria-label="प्रगति रीसेट">
        🔄
      </button>
    </div>
  </div>

  <!-- COLLAPSIBLE SEARCH BAR -->
  <div class="search-container" id="searchContainer">
    <div class="search-input-box">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" placeholder="प्रश्न या विषय खोजें (जैसे: चम्बल, राज्यपाल, 1857, नीति आयोग)..." autocomplete="off">
      <button class="clear-search" id="clearSearchBtn">✕</button>
    </div>
  </div>

  <!-- STATS STRIP -->
  <div class="stats-strip">
    <div class="stat-pill">
      <div class="stat-val" id="statSolved">0 / 245</div>
      <div class="stat-lbl">हल किए</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val" id="statCorrect" style="color:var(--color-correct)">0 ✅</div>
      <div class="stat-lbl">सही जवाब</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val" id="statAccuracy">0%</div>
      <div class="stat-lbl">सटीकता (Accuracy)</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val" id="statStreak">🔥 0</div>
      <div class="stat-lbl">Streak</div>
    </div>
  </div>

  <!-- THIN PROGRESS LINE -->
  <div class="progress-line-track">
    <div class="progress-line-fill" id="progressBar"></div>
  </div>
</div>

<!-- MAIN CONTENT WRAPPER -->
<div class="app-wrapper">

  <!-- SUBJECT HORIZONTAL SCROLL CHIPS -->
  <div class="subject-tabs-wrap">
    <div class="subject-tabs" id="subjectTabs">
      <button class="subj-chip active" data-subject="all">🌟 सभी विषय (245)</button>
      <button class="subj-chip" data-subject="राजस्थान इतिहास">📜 राजस्थान इतिहास (35)</button>
      <button class="subj-chip" data-subject="कला व संस्कृति">🎭 कला व संस्कृति (35)</button>
      <button class="subj-chip" data-subject="राजस्थान भूगोल">🏜️ राजस्थान भूगोल (35)</button>
      <button class="subj-chip" data-subject="राजस्थान राजव्यवस्था">🏛️ राजस्थान राजव्यवस्था (35)</button>
      <button class="subj-chip" data-subject="अर्थव्यवस्था">🌾 अर्थव्यवस्था (35)</button>
      <button class="subj-chip" data-subject="भारतीय संविधान">🇮🇳 भारतीय संविधान (35)</button>
      <button class="subj-chip" data-subject="सामान्य विज्ञान">🔬 सामान्य विज्ञान (35)</button>
    </div>
  </div>

  <!-- STATUS FILTERS & RESULTS COUNT -->
  <div class="status-filters">
    <div class="status-pills" id="statusPills">
      <button class="status-chip active" data-status="all">सभी</button>
      <button class="status-chip" data-status="unattempted">⏳ अनसुलझे</button>
      <button class="status-chip" data-status="incorrect">❌ गलत हुए</button>
      <button class="status-chip" data-status="starred">⭐ सहेजे गए</button>
    </div>
    <div class="results-count" id="resultsCount">245 प्रश्न उपलब्ध</div>
  </div>

  <!-- QUESTIONS FEED -->
  <div class="question-feed" id="questionFeed">
    <!-- Question Cards injected by JavaScript -->
  </div>

  <!-- EMPTY STATE (NO MATCH) -->
  <div class="empty-state" id="emptyState">
    <h3>कोई प्रश्न नहीं मिला</h3>
    <p>आपके चुने गए फ़िल्टर या खोज शब्द के अनुसार कोई प्रश्न नहीं मिला।</p>
  </div>

  <!-- FOOTER ECOSYSTEM BANNER -->
  <div class="ecosystem-footer">
    <h4>RAS 2026 संपूर्ण तैयारी — New India Education</h4>
    <p>पूर्ण वीडियो कोर्स, विषयवार क्लास नोट्स और RAS टेस्ट सीरीज के लिए Omkar Sir का आधिकारिक ऐप डाउनलोड करें।</p>
    <div class="footer-links">
      <a href="https://play.google.com/store/apps/details?id=co.april2019.techa" target="_blank" rel="noopener" class="btn-app-download">
        📲 Android App (TECHA)
      </a>
      <a href="https://wa.me/917023166962?text=Sir%20RAS%20Revise%20ke%20bare%20me%20jankari%20chahiye" target="_blank" rel="noopener" class="btn-whatsapp">
        💬 WhatsApp Mentorship
      </a>
      <a href="/" class="btn-home-link">
        🌐 omkarsir.com
      </a>
    </div>
  </div>

</div>

<!-- FLOATING ACTION BUTTONS -->
<div class="floating-actions">
  <button class="btn-floating" id="nextUnattemptedBtn">
    ⬇️ अगला अनसुलझा प्रश्न
  </button>
  <button class="btn-scroll-top" id="scrollTopBtn" title="ऊपर जाएँ" aria-label="ऊपर जाएँ">
    ↑
  </button>
</div>

<!-- RESET CONFIRMATION MODAL -->
<div class="modal-overlay" id="resetModal">
  <div class="modal-box">
    <h3>🔄 प्रगति रीसेट करें?</h3>
    <p>क्या आप अपने द्वारा हल किए गए सभी प्रश्नों का स्कोर और उत्तर रीसेट करना चाहते हैं? यह क्रिया पूर्ववत नहीं की जा सकती।</p>
    <div class="modal-btns">
      <button class="btn-cancel" id="cancelResetBtn">रद्द करें</button>
      <button class="btn-confirm-reset" id="confirmResetBtn">हाँ, रीसेट करें</button>
    </div>
  </div>
</div>

<!-- QUESTIONS DATA & INTERACTIVE LOGIC -->
<script>
// DATASET
const QUESTIONS = {json_data_str};

// LOCAL STORAGE KEY
const STORAGE_KEY = 'omkarsir_revise_state_v1';

// STATE
let state = {{
  answers: {{}},
  starred: [],
  theme: document.documentElement.getAttribute('data-theme') || 'light',
  currentSubject: 'all',
  currentStatus: 'all',
  searchQuery: ''
}};

// LOAD STATE
try {{
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {{
    const parsed = JSON.parse(saved);
    state.answers = parsed.answers || {{}};
    state.starred = parsed.starred || [];
    if (parsed.theme) state.theme = parsed.theme;
  }}
}} catch(e) {{}}

// APPLY THEME
function applyTheme(t) {{
  state.theme = t;
  document.documentElement.setAttribute('data-theme', t);
  const metaTheme = document.getElementById('metaThemeColor');
  if (metaTheme) {{
    metaTheme.setAttribute('content', t === 'dark' ? '#131110' : '#1B2A6B');
  }}
  try {{
    localStorage.setItem('omkarsir_revise_theme', t);
  }} catch(e) {{}}
  saveState();
}}
applyTheme(state.theme);

// SAVE STATE
function saveState() {{
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify({{
      answers: state.answers,
      starred: state.starred,
      theme: state.theme
    }}));
  }} catch(e) {{}}
}}

// DOM ELEMENTS
const questionFeed = document.getElementById('questionFeed');
const emptyState = document.getElementById('emptyState');
const statSolved = document.getElementById('statSolved');
const statCorrect = document.getElementById('statCorrect');
const statAccuracy = document.getElementById('statAccuracy');
const statStreak = document.getElementById('statStreak');
const progressBar = document.getElementById('progressBar');
const starBadgeCount = document.getElementById('starBadgeCount');
const resultsCount = document.getElementById('resultsCount');

// UPDATE STATS
function updateStats() {{
  const total = QUESTIONS.length;
  const answeredKeys = Object.keys(state.answers);
  const solvedCount = answeredKeys.length;
  
  let correctCount = 0;
  answeredKeys.forEach(id => {{
    if (state.answers[id].isCorrect) correctCount++;
  }});
  
  const wrongCount = solvedCount - correctCount;
  const accuracy = solvedCount > 0 ? Math.round((correctCount / solvedCount) * 100) : 0;
  
  // Calculate Current Streak
  let streak = 0;
  for (let i = 0; i < QUESTIONS.length; i++) {{
    const qid = QUESTIONS[i].id;
    if (state.answers[qid]) {{
      if (state.answers[qid].isCorrect) streak++;
      else streak = 0;
    }}
  }}

  statSolved.textContent = `${{solvedCount}} / ${{total}}`;
  statCorrect.textContent = `${{correctCount}} ✅`;
  statAccuracy.textContent = `${{accuracy}}%`;
  statStreak.textContent = `🔥 ${{streak}}`;
  
  const pct = Math.round((solvedCount / total) * 100);
  progressBar.style.width = pct + '%';

  // Star Badge
  if (state.starred.length > 0) {{
    starBadgeCount.style.display = 'block';
    starBadgeCount.textContent = state.starred.length;
  }} else {{
    starBadgeCount.style.display = 'none';
  }}
}}

// RENDER QUESTIONS
function renderQuestions() {{
  const query = state.searchQuery.toLowerCase().trim();
  
  const filtered = QUESTIONS.filter(q => {{
    // Subject filter
    if (state.currentSubject !== 'all' && q.subj !== state.currentSubject) return false;
    
    // Status filter
    const isAnswered = !!state.answers[q.id];
    const isStarred = state.starred.includes(q.id);
    const isCorrect = isAnswered && state.answers[q.id].isCorrect;

    if (state.currentStatus === 'unattempted' && isAnswered) return false;
    if (state.currentStatus === 'incorrect' && (!isAnswered || isCorrect)) return false;
    if (state.currentStatus === 'starred' && !isStarred) return false;

    // Search query
    if (query) {{
      const qText = (q.text + ' ' + q.exp + ' ' + q.opts.map(o => o.v).join(' ')).toLowerCase();
      if (!qText.includes(query)) return false;
    }}

    return true;
  }});

  resultsCount.textContent = `${{filtered.length}} प्रश्न प्रदर्शित`;

  if (filtered.length === 0) {{
    questionFeed.innerHTML = '';
    emptyState.classList.add('active');
    return;
  }} else {{
    emptyState.classList.remove('active');
  }}

  let html = '';
  filtered.forEach(q => {{
    const ansState = state.answers[q.id];
    const isAnswered = !!ansState;
    const isStarred = state.starred.includes(q.id);

    html += `
      <div class="question-card" id="qcard-${{q.id}}" data-qid="${{q.id}}">
        <div class="card-header">
          <div class="card-badges">
            <span class="badge-num">Q${{q.id}}</span>
            <span class="badge-subj">${{q.subj}}</span>
            <span class="badge-exam">${{q.exam}}</span>
          </div>
          <button class="btn-star ${{isStarred ? 'starred' : ''}}" data-star-id="${{q.id}}" title="${{isStarred ? 'सहेजा गया' : 'सहेजें'}}" aria-label="सहेजें">
            ${{isStarred ? '★' : '☆'}}
          </button>
        </div>

        <div class="question-stem">${{escapeHtml(q.text)}}</div>

        <div class="options-list">
          ${{q.opts.map(opt => {{
            let optClass = 'option-btn';
            if (isAnswered) {{
              optClass += ' disabled';
              if (opt.k === q.ans) {{
                optClass += ' state-correct';
              }} else if (opt.k === ansState.selected && !ansState.isCorrect) {{
                optClass += ' state-wrong';
              }}
            }}
            return `
              <button class="${{optClass}}" data-qid="${{q.id}}" data-key="${{opt.k}}" ${{isAnswered ? 'disabled' : ''}}>
                <span class="option-key">${{opt.k}}</span>
                <span class="option-text">${{escapeHtml(opt.v)}}</span>
              </button>
            `;
          }}).join('')}}
        </div>

        <div class="explanation-box ${{isAnswered ? 'visible' : ''}}" id="exp-${{q.id}}">
          <div class="exp-header">
            <span class="exp-badge-correct">✓ सही उत्तर: विकल्प (${{q.ans}})</span>
            <button class="exp-toggle-btn" onclick="toggleExp(${{q.id}})">व्याख्या छुपाएं/दिखाएं</button>
          </div>
          <div class="exp-body" id="exp-body-${{q.id}}">
            <strong>अवधारणात्मक व्याख्या:</strong><br>
            ${{escapeHtml(q.exp)}}
          </div>
        </div>
      </div>
    `;
  }});

  questionFeed.innerHTML = html;
  bindCardEvents();
}}

// ESCAPE HTML HELPER
function escapeHtml(str) {{
  if (!str) return '';
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
}}

// CARD EVENTS (Option Click, Star Click)
function bindCardEvents() {{
  // Option Clicks
  const optionBtns = questionFeed.querySelectorAll('.option-btn:not(.disabled)');
  optionBtns.forEach(btn => {{
    btn.addEventListener('click', function() {{
      const qid = parseInt(this.getAttribute('data-qid'));
      const key = this.getAttribute('data-key');
      handleOptionSelect(qid, key);
    }});
  }});

  // Star Clicks
  const starBtns = questionFeed.querySelectorAll('.btn-star');
  starBtns.forEach(btn => {{
    btn.addEventListener('click', function(e) {{
      e.stopPropagation();
      const qid = parseInt(this.getAttribute('data-star-id'));
      toggleStar(qid, this);
    }});
  }});
}}

// OPTION SELECT HANDLER
function handleOptionSelect(qid, selectedKey) {{
  if (state.answers[qid]) return; // already answered

  const question = QUESTIONS.find(q => q.id === qid);
  if (!question) return;

  const isCorrect = (selectedKey === question.ans);
  state.answers[qid] = {{
    selected: selectedKey,
    isCorrect: isCorrect
  }};

  saveState();
  updateStats();

  // Haptic feedback if supported
  if (navigator.vibrate) {{
    try {{
      navigator.vibrate(isCorrect ? [30] : [20, 40, 20]);
    }} catch(e) {{}}
  }}

  // Update card DOM in place without full re-render
  const card = document.getElementById(`qcard-${{qid}}`);
  if (!card) return;

  const btns = card.querySelectorAll('.option-btn');
  btns.forEach(btn => {{
    btn.classList.add('disabled');
    btn.setAttribute('disabled', 'true');
    const key = btn.getAttribute('data-key');
    if (key === question.ans) {{
      btn.classList.add('state-correct');
    }} else if (key === selectedKey && !isCorrect) {{
      btn.classList.add('state-wrong');
    }}
  }});

  // Show explanation
  const expBox = document.getElementById(`exp-${{qid}}`);
  if (expBox) {{
    expBox.classList.add('visible');
  }}
}}

// TOGGLE STAR / BOOKMARK
function toggleStar(qid, btnElem) {{
  const idx = state.starred.indexOf(qid);
  if (idx !== -1) {{
    state.starred.splice(idx, 1);
    btnElem.classList.remove('starred');
    btnElem.textContent = '☆';
  }} else {{
    state.starred.push(qid);
    btnElem.classList.add('starred');
    btnElem.textContent = '★';
  }}
  saveState();
  updateStats();

  // If we are currently in 'starred' status filter, re-render
  if (state.currentStatus === 'starred') {{
    renderQuestions();
  }}
}}

// TOGGLE EXPLANATION BODY
window.toggleExp = function(qid) {{
  const body = document.getElementById(`exp-body-${{qid}}`);
  if (body) {{
    body.style.display = (body.style.display === 'none') ? 'block' : 'none';
  }}
}};

// SUBJECT TABS EVENT
const subjectTabs = document.getElementById('subjectTabs');
subjectTabs.addEventListener('click', function(e) {{
  const btn = e.target.closest('.subj-chip');
  if (!btn) return;
  subjectTabs.querySelectorAll('.subj-chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.currentSubject = btn.getAttribute('data-subject');
  renderQuestions();
}});

// STATUS PILLS EVENT
const statusPills = document.getElementById('statusPills');
statusPills.addEventListener('click', function(e) {{
  const btn = e.target.closest('.status-chip');
  if (!btn) return;
  statusPills.querySelectorAll('.status-chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.currentStatus = btn.getAttribute('data-status');
  renderQuestions();
}});

// SEARCH EVENTS
const searchToggleBtn = document.getElementById('searchToggleBtn');
const searchContainer = document.getElementById('searchContainer');
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');

searchToggleBtn.addEventListener('click', function() {{
  searchContainer.classList.toggle('active');
  if (searchContainer.classList.contains('active')) {{
    searchInput.focus();
  }}
}});

searchInput.addEventListener('input', function() {{
  state.searchQuery = this.value;
  clearSearchBtn.style.display = this.value ? 'block' : 'none';
  renderQuestions();
}});

clearSearchBtn.addEventListener('click', function() {{
  searchInput.value = '';
  state.searchQuery = '';
  this.style.display = 'none';
  renderQuestions();
  searchInput.focus();
}});

// BOOKMARK HEADER BUTTON FILTER
const bookmarkFilterBtn = document.getElementById('bookmarkFilterBtn');
bookmarkFilterBtn.addEventListener('click', function() {{
  statusPills.querySelectorAll('.status-chip').forEach(b => {{
    if (b.getAttribute('data-status') === 'starred') b.classList.add('active');
    else b.classList.remove('active');
  }});
  state.currentStatus = 'starred';
  renderQuestions();
}});

// THEME TOGGLE
const themeToggleBtn = document.getElementById('themeToggleBtn');
themeToggleBtn.addEventListener('click', function() {{
  const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme);
}});

// RESET MODAL
const resetBtn = document.getElementById('resetBtn');
const resetModal = document.getElementById('resetModal');
const cancelResetBtn = document.getElementById('cancelResetBtn');
const confirmResetBtn = document.getElementById('confirmResetBtn');

resetBtn.addEventListener('click', function() {{
  resetModal.classList.add('open');
}});

cancelResetBtn.addEventListener('click', function() {{
  resetModal.classList.remove('open');
}});

confirmResetBtn.addEventListener('click', function() {{
  state.answers = {{}};
  state.starred = [];
  saveState();
  updateStats();
  renderQuestions();
  resetModal.classList.remove('open');
}});

// NEXT UNATTEMPTED BUTTON
const nextUnattemptedBtn = document.getElementById('nextUnattemptedBtn');
nextUnattemptedBtn.addEventListener('click', function() {{
  const cards = Array.from(questionFeed.querySelectorAll('.question-card'));
  let target = null;
  for (let card of cards) {{
    const qid = parseInt(card.getAttribute('data-qid'));
    if (!state.answers[qid]) {{
      target = card;
      break;
    }}
  }}

  if (target) {{
    target.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    // subtle highlight animation
    target.style.transition = 'box-shadow 0.3s ease, border-color 0.3s ease';
    target.style.borderColor = 'var(--brand-orange)';
    target.style.boxShadow = '0 0 0 4px var(--brand-orange-light)';
    setTimeout(() => {{
      target.style.borderColor = '';
      target.style.boxShadow = '';
    }}, 1200);
  }} else {{
    alert('शानदार! आपने वर्तमान फ़िल्टर के सभी प्रश्न हल कर लिए हैं!');
  }}
}});

// SCROLL TO TOP BUTTON
const scrollTopBtn = document.getElementById('scrollTopBtn');
scrollTopBtn.addEventListener('click', function() {{
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}});

// INITIAL RENDER
updateStats();
renderQuestions();
</script>

</body>
</html>'''

# Write to revise.html
with open('/Users/omkarsingh/Desktop/omkarsir-website/revise.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

# Write to revise/index.html
with open('/Users/omkarsingh/Desktop/omkarsir-website/revise/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Generated revise.html ({len(html_content)} bytes)")
print(f"Generated revise/index.html ({len(html_content)} bytes)")
