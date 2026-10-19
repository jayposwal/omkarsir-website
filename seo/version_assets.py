#!/usr/bin/env python3
"""
Cache-busting for the homepage: rewrites the homepage's references to its own
stylesheet and scripts as  /path?v=<content-hash>.

A changed file gets a new URL, so no browser cache or (older) service worker
can keep serving a stale copy — the service worker never caches ?query URLs.
Run after editing assets/css/home.css, nied-menu.js or nied-latest-posts.js:
    python3 seo/version_assets.py
"""
import hashlib
import re

PAGE = "index.html"
ASSETS = ["assets/css/home.css", "nied-menu.js", "nied-latest-posts.js"]


def main():
    with open(PAGE, encoding="utf-8") as f:
        s = f.read()
    for path in ASSETS:
        with open(path, "rb") as f:
            v = hashlib.md5(f.read()).hexdigest()[:8]
        s, n = re.subn(r"/" + re.escape(path) + r"(\?v=[0-9a-f]+)?(?=['\"])", "/" + path + "?v=" + v, s)
        print(path, "v=" + v, n, "refs")
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(s)


if __name__ == "__main__":
    main()
