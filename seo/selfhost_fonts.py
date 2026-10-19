#!/usr/bin/env python3
"""
Self-host every Google Fonts stylesheet used by the static pages.

For each distinct fonts.googleapis.com/css2 URL found in the HTML, downloads the
CSS (as Chrome sees it, i.e. woff2 + unicode-range subsets), stores the font
files under /assets/fonts/ and writes /assets/fonts/gf-<hash>.css. The <link>
in every page is then pointed at that same-origin file and the Google
preconnects are removed. Idempotent; run again after adding pages that use a
new Google Fonts URL, then commit assets/fonts/ too.

Usage: python3 seo/selfhost_fonts.py
"""
import glob
import hashlib
import os
import re
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
FONT_DIR = 'assets/fonts'
LINK_RE = re.compile(r'<link\s+href="(https://fonts\.googleapis\.com/css2\?[^"]+)"\s+rel="stylesheet"\s*/?>')
PRECONNECT_RE = re.compile(
    r'[ \t]*<link\s+rel=["\']preconnect["\']\s+href=["\']https://fonts\.(googleapis|gstatic)\.com["\'][^>]*>[ \t]*\n?', re.I)
FACE_RE = re.compile(r'/\* (\S+) \*/\s*@font-face \{(.*?)\}', re.S)


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build_css(url):
    """Download one Google Fonts stylesheet + its files; return local CSS path."""
    url = url.replace('&amp;', '&')
    name = 'gf-' + hashlib.md5(url.encode()).hexdigest()[:8] + '.css'
    out_path = os.path.join(FONT_DIR, name)
    if os.path.exists(out_path):
        return '/' + out_path
    css = fetch(url).decode()
    out = ['/* Self-hosted copy of ' + url + ' */']
    for m in FACE_RE.finditer(css):
        subset, body = m.group(1), m.group(2)
        family = re.search(r"font-family: '([^']+)'", body).group(1)
        src = re.search(r'url\((\S+?)\)', body).group(1)
        # Variable fonts share one file across weights, so name files by source hash.
        fname = '%s-%s-%s.woff2' % (re.sub(r'\W+', '-', family.lower()), subset,
                                     hashlib.md5(src.encode()).hexdigest()[:6])
        fpath = os.path.join(FONT_DIR, fname)
        if not os.path.exists(fpath):
            with open(fpath, 'wb') as f:
                f.write(fetch(src))
        out.append('/* %s */\n@font-face {%s}' % (subset, body.replace(src, '/' + fpath)))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    return '/' + out_path


def main():
    os.makedirs(FONT_DIR, exist_ok=True)
    local = {}
    changed = 0
    for path in glob.glob('**/*.html', recursive=True):
        with open(path, encoding='utf-8') as f:
            orig = f.read()
        s = orig
        for m in LINK_RE.finditer(orig):
            url = m.group(1)
            if url not in local:
                local[url] = build_css(url)
            s = s.replace(m.group(0), '<link rel="stylesheet" href="%s">' % local[url])
        if 'fonts.googleapis.com/css' not in s:
            s = PRECONNECT_RE.sub('', s)
        if s != orig:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(s)
            changed += 1
    print('stylesheets', len(local), 'pages changed', changed)


if __name__ == '__main__':
    main()
