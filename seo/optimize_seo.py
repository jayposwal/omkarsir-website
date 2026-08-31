#!/usr/bin/env python3
"""Conservative static SEO optimizer for omkarsir.com."""
from __future__ import annotations

import html
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

SITE = "https://omkarsir.com/"
ROOT = Path(__file__).resolve().parents[1]
HEAD_RE = re.compile(r"<head\b[^>]*>(.*?)</head>", re.I | re.S)
TITLE_RE = re.compile(r"<title\b[^>]*>.*?</title>", re.I | re.S)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.I | re.S)


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def attr_value(tag: str, name: str) -> str | None:
    m = re.search(rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return html.unescape(m.group(2).strip()) if m else None


def existing_meta(head: str, name: str) -> str | None:
    m = re.search(r'<meta\b[^>]*\bname=["\']' + re.escape(name) + r'["\'][^>]*>', head, re.I)
    return attr_value(m.group(0), "content") if m else None


def replace_or_insert_named_meta(head: str, name: str, value: str) -> str:
    tag_re = re.compile(r'<meta\b[^>]*\bname=["\']' + re.escape(name) + r'["\'][^>]*>', re.I)
    replacement = f'<meta name="{html.escape(name, quote=True)}" content="{html.escape(value, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return head.replace("\n</head>", f"\n{replacement}\n</head>", 1)


def replace_or_insert_property_meta(head: str, prop: str, value: str) -> str:
    tag_re = re.compile(r'<meta\b[^>]*\bproperty=["\']' + re.escape(prop) + r'["\'][^>]*>', re.I)
    replacement = f'<meta property="{html.escape(prop, quote=True)}" content="{html.escape(value, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return head.replace("\n</head>", f"\n{replacement}\n</head>", 1)


def replace_or_insert_canonical(head: str, canonical: str) -> str:
    tag_re = re.compile(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*>', re.I)
    replacement = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return head.replace("\n</head>", f"\n{replacement}\n</head>", 1)


def canonical_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return SITE if rel == "index.html" else urljoin(SITE, rel)


def title_for(rel: str, existing: str | None, h1: str | None) -> str:
    if rel == "index.html":
        return "RAS & Rajasthan GK Preparation | Omkar Sir"
    current = strip_tags(existing or "")
    if current and current.lower() not in {"home", "index", "omkar sir", "new india education"}:
        if "omkar sir" not in current.lower() and len(current) <= 54:
            return f"{current} | Omkar Sir"
        return current
    base = h1 or Path(rel).stem.replace("-", " ").title()
    return f"{base} | Omkar Sir"


def description_for(rel: str, existing: str | None, h1: str | None, first_p: str | None) -> str:
    if rel == "index.html":
        return "RAS और Rajasthan GK की तैयारी के लिए Hindi Notes, Syllabus, PYQ, Test Series और Courses — Omkar Sir / New India Education."
    current = strip_tags(existing or "")
    boilerplate = ["NCERT, RBSE की मूल पुस्तकों व प्रामाणिक स्रोतों से तैयार", "विश्वसनीय एवं बेहतरीन Content"]
    weak = not current or len(current) < 70 or (all(x in current for x in boilerplate) and len(current) > 150)
    if not weak:
        return current[:157].rstrip(" ।,-") + ("…" if len(current) > 157 else "")
    topic = h1 or Path(rel).stem.replace("-", " ").title()
    supporting = strip_tags(first_p or "")
    if supporting:
        text = f"{topic} — RAS और Rajasthan competitive exams की तैयारी के लिए आसान Hindi notes और study material. {supporting}"
    else:
        text = f"{topic} — RAS, RPSC और Rajasthan competitive exams की तैयारी के लिए Hindi study material, notes और revision resources."
    return text[:157].rstrip(" ।,-") + ("…" if len(text) > 157 else "")


def process_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    m = HEAD_RE.search(original)
    if not m:
        return False
    head = m.group(1)
    rel = path.relative_to(ROOT).as_posix()
    canonical = canonical_for(path)
    title_match = TITLE_RE.search(head)
    existing_title = strip_tags(title_match.group(0)) if title_match else None
    h1_match = H1_RE.search(original)
    h1 = strip_tags(h1_match.group(1)) if h1_match else None
    p_match = P_RE.search(original)
    first_p = strip_tags(p_match.group(1)) if p_match else None
    title = title_for(rel, existing_title, h1)
    description = description_for(rel, existing_meta(head, "description"), h1, first_p)

    if title_match:
        head = TITLE_RE.sub(f"<title>{html.escape(title)}</title>", head, count=1)
    else:
        head = head.replace("\n</head>", f"\n<title>{html.escape(title)}</title>\n</head>", 1)

    head = replace_or_insert_named_meta(head, "description", description)
    head = replace_or_insert_named_meta(head, "robots", "index, follow, max-image-preview:large")
    head = replace_or_insert_named_meta(head, "author", "Omkar Singh Gurjar")
    head = replace_or_insert_named_meta(head, "referrer", "strict-origin-when-cross-origin")
    head = replace_or_insert_named_meta(head, "theme-color", "#1B2A6B")
    head = replace_or_insert_canonical(head, canonical)

    page_type = "article" if re.search(r"-ch\d+[-.]", rel) else "website"
    for prop, value in [
        ("og:title", title),
        ("og:description", description),
        ("og:url", canonical),
        ("og:type", page_type),
        ("og:site_name", "Omkar Sir | New India Education"),
        ("og:locale", "hi_IN"),
        ("og:image", urljoin(SITE, "og-image.png")),
        ("og:image:alt", title),
    ]:
        head = replace_or_insert_property_meta(head, prop, value)

    for name, value in [
        ("twitter:card", "summary_large_image"),
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:url", canonical),
        ("twitter:image", urljoin(SITE, "og-image.png")),
    ]:
        head = replace_or_insert_named_meta(head, name, value)

    updated = original[:m.start(1)] + head + original[m.end(1):]
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def git_lastmod(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path.relative_to(ROOT).as_posix()],
            cwd=ROOT, capture_output=True, text=True, check=True
        )
        value = result.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
    except Exception:
        pass
    return date.today().isoformat()


def write_sitemap() -> None:
    rows: list[tuple[str, str]] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or path.name.lower() == "404.html":
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        hm = HEAD_RE.search(raw)
        if hm and re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^\"\']*noindex', hm.group(1), re.I):
            continue
        rows.append((canonical_for(path), git_lastmod(path)))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in rows:
        lines += ["  <url>", f"    <loc>{html.escape(loc)}</loc>", f"    <lastmod>{lastmod}</lastmod>", "  </url>"]
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Sitemap contains {len(rows)} indexable HTML URLs.")


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*.html"):
        if ".git" not in path.parts and process_html(path):
            changed += 1
    write_sitemap()
    print(f"SEO optimizer updated {changed} HTML pages.")


if __name__ == "__main__":
    main()
