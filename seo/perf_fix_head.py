#!/usr/bin/env python3
"""
One-time / idempotent performance fix for <head> across all static pages.

1. Moves <meta charset> + <meta name="viewport"> to the very top of <head>
   (charset must be within the first 1024 bytes; AdSense/gtag were before it).
2. Replaces the Google Fonts Poppins+Hind stylesheet with the self-hosted
   /assets/fonts/nied-fonts.css (same-origin, no extra DNS/TLS to
   fonts.googleapis.com + fonts.gstatic.com) and preloads the Hindi body font.
   Google preconnects are dropped when the page no longer uses Google Fonts.
3. Pages using nied-menu.js get a #nied-navbar mount at the top of <body> and
   a reserved min-height for it, so the JS-injected navbar doesn't push the
   page down (Cumulative Layout Shift).

Usage: python3 seo/perf_fix_head.py
"""
import glob
import re

FONT_URLS = {
    "https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Hind:wght@400;500;600&display=swap",
    "https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Hind:wght@400;500;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=Hind:wght@400;500;600;700&family=Poppins:wght@600;700;800&display=swap",
}
SELF_HOSTED = (
    '<link rel="preload" href="/assets/fonts/hind-400-devanagari.woff2" as="font" type="font/woff2" crossorigin>\n'
    '<link rel="stylesheet" href="/assets/fonts/nied-fonts.css">'
)
CHARSET_RE = re.compile(r'[ \t]*<meta\s+charset=["\']?utf-8["\']?\s*/?>[ \t]*\n?', re.I)
VIEWPORT_RE = re.compile(r'[ \t]*<meta\s+name=["\']viewport["\'][^>]*>[ \t]*\n?', re.I)
HEAD_OPEN_RE = re.compile(r'<head\b[^>]*>', re.I)
NAVBAR_STYLE = ('<style id="nied-navbar-reserve">#nied-navbar{min-height:72px}'
                '@media(max-width:520px){#nied-navbar{min-height:62px}}</style>')
BODY_OPEN_RE = re.compile(r'<body\b[^>]*>', re.I)
PRECONNECT_RE = re.compile(
    r'[ \t]*<link\s+rel=["\']preconnect["\']\s+href=["\']https://fonts\.(googleapis|gstatic)\.com["\'][^>]*>[ \t]*\n?', re.I)


def fix(s):
    head = HEAD_OPEN_RE.search(s)
    if not head:
        return s
    # 1. charset + viewport first
    cs = CHARSET_RE.search(s)
    vp = VIEWPORT_RE.search(s)
    if cs:
        top = '<meta charset="UTF-8">\n'
        if vp:
            top += vp.group(0).strip() + '\n'
        s = CHARSET_RE.sub('', s, count=1)
        if vp:
            s = VIEWPORT_RE.sub('', s, count=1)
        head = HEAD_OPEN_RE.search(s)
        s = s[:head.end()] + '\n' + top + s[head.end():].lstrip('\n')
    # 2. self-hosted fonts
    for url in FONT_URLS:
        tag_re = re.compile(r'<link\s+href="' + re.escape(url) + r'"\s+rel="stylesheet"\s*/?>')
        if tag_re.search(s) and 'nied-fonts.css' not in s:
            s = tag_re.sub(SELF_HOSTED, s, count=1)
    if 'fonts.googleapis.com/css' not in s:
        s = PRECONNECT_RE.sub('', s)
    # 3. reserve navbar space
    if 'nied-menu.js' in s and '#nied-navbar{min-height' not in s:
        s = s.replace('</head>', NAVBAR_STYLE + '\n</head>', 1)
        if 'id="nied-navbar"' not in s:
            body = BODY_OPEN_RE.search(s)
            if body:
                s = s[:body.end()] + '\n<div id="nied-navbar"></div>' + s[body.end():]
    return s


def main():
    changed = 0
    for path in glob.glob('**/*.html', recursive=True):
        with open(path, encoding='utf-8') as f:
            orig = f.read()
        new = fix(orig)
        if new != orig:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            changed += 1
    print('changed', changed)


if __name__ == '__main__':
    main()
