#!/usr/bin/env python3
"""Conservative static SEO optimizer for omkarsir.com."""
from __future__ import annotations

import html
import json
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


def insert_into_head(head: str, tag: str) -> str:
    """Append a tag at the end of <head> content (head is the inner HTML, without </head>)."""
    return head.rstrip() + "\n" + tag + "\n"


# Non-public internal utility pages, payment download delivery pages, and private show pages:
NOINDEX_RE = re.compile(r"^(admin-comments|pdf-chapter-splitter|download-adhunik-bharat-itihas|download-ras-mains-paper-2-pdf)\.html$|^show/")


def should_noindex(rel: str, title: str | None) -> bool:
    return (rel == "404.html" or rel.startswith("admin-comments") or rel == "pdf-chapter-splitter.html" or bool(NOINDEX_RE.search(rel)) or (title or "").startswith("Protected Page"))


def replace_or_insert_named_meta(head: str, name: str, value: str) -> str:
    tag_re = re.compile(r'<meta\b[^>]*\bname=["\']' + re.escape(name) + r'["\'][^>]*>', re.I)
    replacement = f'<meta name="{html.escape(name, quote=True)}" content="{html.escape(value, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return insert_into_head(head, replacement)


def replace_or_insert_property_meta(head: str, prop: str, value: str) -> str:
    tag_re = re.compile(r'<meta\b[^>]*\bproperty=["\']' + re.escape(prop) + r'["\'][^>]*>', re.I)
    replacement = f'<meta property="{html.escape(prop, quote=True)}" content="{html.escape(value, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return insert_into_head(head, replacement)


def replace_or_insert_canonical(head: str, canonical: str) -> str:
    tag_re = re.compile(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*>', re.I)
    replacement = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(replacement, head, count=1)
    return insert_into_head(head, replacement)


def canonical_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return SITE if rel == "index.html" else urljoin(SITE, rel)


def title_for(rel: str, existing: str | None, h1: str | None) -> str:
    if rel == "index.html":
        return "RAS & Rajasthan GK Notes, PYQs and Free Tests | Omkar Sir"
    current = strip_tags(existing or "")
    if current and current.lower() not in {"home", "index", "omkar sir", "new india education"}:
        if "omkar sir" not in current.lower() and len(current) <= 54:
            return f"{current} | Omkar Sir"
        return current
    base = h1 or Path(rel).stem.replace("-", " ").title()
    return f"{base} | Omkar Sir"


def description_for(rel: str, existing: str | None, h1: str | None, first_p: str | None) -> str:
    """Prefer page-specific descriptions and remove unsupported, repetitive superlatives."""
    if rel == "index.html":
        return "RAS और Rajasthan GK की तैयारी के लिए Free Hindi Notes, PYQs, Daily Quiz, Current Affairs, Test Series और Omkar Sir के Courses।"

    def clean(value: str | None) -> str:
        value = strip_tags(value or "")
        value = re.sub(r"\s*भारत का सबसे बेहतरीन कंटेंट.*$", "", value, flags=re.I)
        value = re.sub(
            r"\s*NCERT,\s*RBSE की मूल पुस्तकों व प्रामाणिक स्रोतों से तैयार\s*[—–|,-]*\s*विश्वसनीय एवं बेहतरीन Content\.?",
            "",
            value,
            flags=re.I,
        )
        return re.sub(r"\s+", " ", value).strip(" .|—–,-")

    current = clean(existing)
    if current and len(current) >= 70:
        return current[:157].rstrip(" ।,-") + ("…" if len(current) > 157 else "")

    topic = clean(h1) or Path(rel).stem.replace("-", " ").replace("_", " ").title()
    supporting = clean(first_p)
    if supporting and supporting.lower() not in topic.lower():
        text = f"{topic} — Hindi study notes, explanations and exam-focused practice. {supporting}"
    else:
        text = f"{topic} — Hindi notes, practice questions and revision resources for competitive exam preparation."
    text = re.sub(r"\s+", " ", text).strip()
    return text[:157].rstrip(" ।,-") + ("…" if len(text) > 157 else "")


RAW_TEXT_BLOCK_RE = re.compile(
    r"<!--[\s\S]*?-->|<(?P<tag>script|style|pre|textarea|code|svg|iframe)\b[^>]*>.*?</(?P=tag)\s*>",
    re.I | re.S,
)


def _transform_outside_raw_text(document: str, transform) -> str:
    """Transform normal HTML while leaving scripts, styles and preformatted blocks untouched."""
    output: list[str] = []
    cursor = 0
    for match in RAW_TEXT_BLOCK_RE.finditer(document):
        output.append(transform(document[cursor:match.start()]))
        output.append(match.group(0))
        cursor = match.end()
    output.append(transform(document[cursor:]))
    return "".join(output)


def optimize_loading_hints(document: str, rel: str) -> str:
    """Use async image decoding and lazy-load below-fold images on learning pages.
    Preserve print-ready papers and interactive quiz experiences.
    """
    if rel.startswith(("quiz/", "quizzes/", "show/")):
        return document
    image_index = [0]

    def edit_segment(segment: str) -> str:
        def edit_img(match) -> str:
            tag = match.group(0)
            image_index[0] += 1
            if not re.search(r"\bdecoding\s*=", tag, re.I):
                tag = re.sub(r"\s*/?>$", lambda end: ' decoding="async"' + end.group(0), tag)
            if image_index[0] > 1 and not re.search(r"\bloading\s*=", tag, re.I):
                tag = re.sub(r"\s*/?>$", lambda end: ' loading="lazy"' + end.group(0), tag)
            return tag
        return re.sub(r"<img\b[^>]*>", edit_img, segment, flags=re.I)

    return _transform_outside_raw_text(document, edit_segment)


def minify_large_learning_html(document: str, rel: str, original_size: int) -> str:
    """Reduce redundant source whitespace on large reading pages; do not reformat quiz data."""
    if original_size < 200_000 or rel.startswith(("quiz/", "quizzes/", "show/")):
        return document

    def collapse_inter_tag_space(segment: str) -> str:
        # Keep one collapsible space so adjacent inline words are not accidentally joined.
        return re.sub(r">[ \t\r\n]+<", "> <", segment)

    return _transform_outside_raw_text(document, collapse_inter_tag_space)


INLINE_STYLE_ATTR_RE = re.compile(r"\sstyle=(['\"])(.*?)\1", re.I | re.S)
CLASS_ATTR_RE = re.compile(r"\bclass=(['\"])(.*?)\1", re.I | re.S)
HTML_TAG_RE = re.compile(r"<[A-Za-z][^<>]*>", re.S)
SAFE_TO_DEDUP_STYLE_RE = re.compile(r"[A-Za-z0-9#().,%\s:;!/-]+\Z")


def _css_declarations_with_important(style_value: str) -> str:
    """Convert inline declarations into a class rule while preserving inline-style priority."""
    declarations: list[str] = []
    current: list[str] = []
    quote: str | None = None
    parens = 0
    escaped = False

    def flush() -> None:
        raw = "".join(current).strip()
        current.clear()
        if not raw or ":" not in raw:
            return
        prop, value = raw.split(":", 1)
        prop = prop.strip()
        value = value.strip()
        if not prop or not value:
            return
        if not re.search(r"\s*!important\s*$", value, re.I):
            value += " !important"
        declarations.append(f"{prop}: {value};")

    for char in style_value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and quote:
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
        elif char == "(":
            parens += 1
            current.append(char)
        elif char == ")":
            parens = max(0, parens - 1)
            current.append(char)
        elif char == ";" and parens == 0:
            flush()
        else:
            current.append(char)
    flush()
    return " ".join(declarations)


def deduplicate_repeated_inline_styles(document: str, rel: str, original_size: int) -> str:
    """Move long, frequently repeated inline styles into CSS classes on large study pages.
    Print-ready papers, interactive quizzes and protected/show pages are intentionally excluded.
    """
    if original_size < 150_000 or rel.startswith(("quiz/", "quizzes/", "show/")):
        return document
    if NOINDEX_RE.search(rel) or rel in {"404.html", "admin-comments.html", "pdf-chapter-splitter.html"}:
        return document

    counts: dict[str, int] = {}

    def count_styles(segment: str) -> str:
        for tag_match in HTML_TAG_RE.finditer(segment):
            style_match = INLINE_STYLE_ATTR_RE.search(tag_match.group(0))
            if not style_match:
                continue
            value = html.unescape(style_match.group(2)).strip()
            if len(value) >= 30 and SAFE_TO_DEDUP_STYLE_RE.fullmatch(value):
                counts[value] = counts.get(value, 0) + 1
        return segment

    _transform_outside_raw_text(document, count_styles)
    eligible = [
        value for value, count in counts.items()
        if count >= 8 and len(value) >= 30
    ]
    if not eligible:
        return document

    eligible.sort(key=lambda value: (-counts[value], value))
    class_by_style = {value: f"nied-is-{i:03d}" for i, value in enumerate(eligible, 1)}
    rules: list[str] = []
    for value in eligible:
        declarations = _css_declarations_with_important(value)
        if declarations:
            rules.append(f".{class_by_style[value]} {{{declarations}}}")
        else:
            class_by_style.pop(value, None)
    if not class_by_style:
        return document

    def replace_style_attrs(segment: str) -> str:
        def replace_tag(tag_match: re.Match[str]) -> str:
            tag = tag_match.group(0)
            style_match = INLINE_STYLE_ATTR_RE.search(tag)
            if not style_match:
                return tag
            value = html.unescape(style_match.group(2)).strip()
            class_name = class_by_style.get(value)
            if not class_name:
                return tag
            class_match = CLASS_ATTR_RE.search(tag)
            if class_match:
                old_classes = class_match.group(2).strip()
                if class_name in old_classes.split():
                    return INLINE_STYLE_ATTR_RE.sub("", tag, count=1)
                new_classes = (old_classes + " " + class_name).strip()
                tag = CLASS_ATTR_RE.sub(
                    lambda m: f'class={m.group(1)}{html.escape(new_classes, quote=True)}{m.group(1)}',
                    tag,
                    count=1,
                )
            else:
                tag = re.sub(r"\s*/?>$", lambda end: f' class="{class_name}"' + end.group(0), tag, count=1)
            return INLINE_STYLE_ATTR_RE.sub("", tag, count=1)
        return HTML_TAG_RE.sub(replace_tag, segment)

    updated = _transform_outside_raw_text(document, replace_style_attrs)
    css_block = "\n<style id=\"nied-inline-style-dedup\">\n" + "\n".join(rules) + "\n</style>\n"
    if re.search(r"</head\s*>", updated, re.I):
        updated = re.sub(r"</head\s*>", lambda m: css_block + m.group(0), updated, count=1, flags=re.I)
    else:
        return document
    return updated


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
        head = insert_into_head(head, f"<title>{html.escape(title)}</title>")

    head = replace_or_insert_named_meta(head, "description", description)
    existing_robots = existing_meta(head, "robots")
    if should_noindex(rel, existing_title):
        head = replace_or_insert_named_meta(head, "robots", "noindex, follow")
    else:
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
    updated = deduplicate_repeated_inline_styles(updated, rel, len(original.encode("utf-8")))
    updated = optimize_loading_hints(updated, rel)
    updated = minify_large_learning_html(updated, rel, len(original.encode("utf-8")))
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


_GIT_DATES_CACHE: dict[str, str] | None = None


def get_git_dates() -> dict[str, str]:
    global _GIT_DATES_CACHE
    if _GIT_DATES_CACHE is not None:
        return _GIT_DATES_CACHE
    dates: dict[str, str] = {}
    try:
        res = subprocess.run(
            ["git", "log", "--name-only", "--format=COMMIT:%cs"],
            cwd=ROOT, capture_output=True, text=True, check=True
        )
        current_date = None
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("COMMIT:"):
                current_date = line.split(":", 1)[1]
            elif line and current_date and line not in dates:
                dates[line] = current_date
    except Exception:
        pass
    _GIT_DATES_CACHE = dates
    return dates


def git_lastmod(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    dates = get_git_dates()
    if rel in dates:
        return dates[rel]
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



SEARCH_INDEX_EXCLUDE = {"404.html", "admin-comments.html", "pdf-chapter-splitter.html"}


def write_search_index() -> None:
    entries: list[dict[str, str]] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in SEARCH_INDEX_EXCLUDE:
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        hm = HEAD_RE.search(raw)
        head = hm.group(1) if hm else raw
        if re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^"\']*noindex', head, re.I):
            continue
        title_match = TITLE_RE.search(head)
        title = strip_tags(title_match.group(0)) if title_match else path.stem.replace("-", " ").title()
        desc = (existing_meta(head, "description") or "").strip()
        if len(desc) > 160:
            desc = desc[:157].rstrip() + "…"
        url = "/" if rel == "index.html" else "/" + rel
        entries.append({"title": title, "url": url, "desc": desc})
    (ROOT / "search-index.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Search index contains {len(entries)} pages.")


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*.html"):
        if ".git" not in path.parts and process_html(path):
            changed += 1
    write_sitemap()
    write_search_index()
    print(f"SEO optimizer updated {changed} HTML pages.")


if __name__ == "__main__":
    main()
