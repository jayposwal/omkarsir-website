#!/usr/bin/env python3
"""Comprehensive Google-friendly and AI-friendly SEO optimizer for omkarsir.com."""
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

# Printable duplicates of quizzes and static booklet variations
BOOKLET_SUFFIX_RE = re.compile(
    r"-(bilingual-question-paper|question-paper|bilingual-solution-booklet|solution-booklet|answer-key|ppt-pdf|workbook-hi|bilingual-workbook|bilingual-full-set|bilingual-model-answer|model-answer-hi|read)\.html$",
    re.I
)

# Utility / Admin / Internal pages that should not appear in search results
EXCLUDE_REL = {
    "404.html",
    "admin-comments.html",
    "pdf-chapter-splitter.html",
    "download-adhunik-bharat-itihas.html",
    "download-ras-mains-paper-2-pdf.html",
    "download-rajasthan-history.html",
}


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


def should_noindex(rel: str, title: str | None, head: str = "") -> bool:
    if rel in EXCLUDE_REL or rel.startswith("show/"):
        return True
    if (title or "").strip().startswith("Protected Page"):
        return True
    if BOOKLET_SUFFIX_RE.search(rel):
        return True
    if head:
        m = re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\']([^"\']*)["\']', head, re.I)
        if m and "noindex" in m.group(1).lower():
            return True
    return False


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
    if rel == "index.html":
        return SITE
    # For duplicate quiz booklets, point canonical to primary interactive quiz
    if BOOKLET_SUFFIX_RE.search(rel):
        base_name = BOOKLET_SUFFIX_RE.sub(".html", path.name)
        base_path = path.parent / base_name
        if base_path.exists():
            return urljoin(SITE, base_path.relative_to(ROOT).as_posix())
    return urljoin(SITE, rel)


def clean_title(title_text: str) -> str:
    title = strip_tags(title_text).strip()
    title = re.sub(r"\s*\|\s*Omkar\s*Sir.*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s*\|\s*New\s*India\s*Education.*$", "", title, flags=re.I).strip()
    return f"{title} | Omkar Sir" if title else "RAS Exam Preparation | Omkar Sir"


def title_for(rel: str, existing: str | None, h1: str | None) -> str:
    if rel == "index.html":
        return "RAS Exam 2026 Preparation | RAS Pre & Mains Notes, Test Series — Omkar Sir"
    current = strip_tags(existing or "")
    if current and current.lower() not in {"home", "index", "omkar sir", "new india education"}:
        return clean_title(current)
    base = h1 or Path(rel).stem.replace("-", " ").title()
    return f"{base} | Omkar Sir"


def description_for(rel: str, existing: str | None, h1: str | None, first_p: str | None) -> str:
    if rel == "index.html":
        return "RAS Exam 2026: Notes, Syllabus, PYQ, Test Series और Courses। NCERT, RBSE प्रामाणिक स्रोतों से तैयार — 6 लाख+ सफल विद्यार्थी, 8 साल का अनुभव।"
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


def infer_subject(text: str) -> str:
    t = text.lower()
    if "भूगोल" in t or "geography" in t or "atlas" in t:
        return "राजस्थान भूगोल (Rajasthan Geography)"
    if "इतिहास" in t or "history" in t or "aagman" in t or "british" in t:
        return "राजस्थान एवं भारतीय इतिहास (History)"
    if "कला" in t or "संस्कृति" in t or "culture" in t:
        return "राजस्थान कला एवं संस्कृति (Art & Culture)"
    if "अर्थव्यवस्था" in t or "economy" in t or "आर्थिक" in t or "eco survey" in t:
        return "राजस्थान अर्थव्यवस्था एवं आर्थिक समीक्षा (Economy)"
    if "राजव्यवस्था" in t or "polity" in t or "संविधान" in t or "constitution" in t:
        return "भारतीय संविधान एवं राज्यव्यवस्था (Polity)"
    if "विज्ञान" in t or "science" in t or "technology" in t or "जीव विज्ञान" in t:
        return "सामान्य विज्ञान एवं प्रौद्योगिकी (General Science & Technology)"
    if "current" in t or "समसामयिकी" in t or "sujas" in t:
        return "समसामयिकी (Current Affairs)"
    if "math" in t or "reasoning" in t or "गणित" in t or "तर्कशक्ति" in t:
        return "गणित एवं तर्कशक्ति (Maths & Reasoning)"
    if "ethics" in t or "नीतिशास्त्र" in t or "vyavhar" in t or "व्यवहार" in t:
        return "प्रशासकीय नीतिशास्त्र एवं व्यवहार (Ethics & Behavior)"
    if "lok-prashasan" in t or "लोक प्रशासन" in t:
        return "लोक प्रशासन (Public Administration)"
    return "RPSC RAS Exam Preparation"


def infer_quiz_questions_count(text: str, filename: str) -> int | None:
    m = re.search(r"(?:top-)?(\d+)-(?:mcq|sawal|pyq|random)", filename, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*(?:प्रश्न|MCQ|MCqs|सवाल)", text, re.I)
    if m:
        return int(m.group(1))
    nums = re.findall(r'"num"\s*:\s*\d+', text)
    if nums:
        return len(nums)
    return None


def generate_json_ld(rel: str, title: str, description: str, canonical: str, original: str) -> str:
    subject = infer_subject(rel + " " + title + " " + description)
    author = {
        "@type": "Person",
        "name": "Omkar Singh Gurjar",
        "alternateName": "Omkar Sir",
        "jobTitle": "Founder & Educator, New India Education",
        "url": "https://omkarsir.com/about.html"
    }
    publisher = {
        "@type": "EducationalOrganization",
        "name": "New India Education",
        "url": "https://omkarsir.com",
        "logo": {
            "@type": "ImageObject",
            "url": "https://omkarsir.com/logo.png"
        }
    }

    if rel.startswith("quizzes/") or rel.startswith("quiz/"):
        num_q = infer_quiz_questions_count(original, Path(rel).name)
        schema: dict = {
            "@context": "https://schema.org",
            "@type": "Quiz",
            "name": title,
            "description": description,
            "url": canonical,
            "inLanguage": "hi",
            "isAccessibleForFree": True,
            "educationalLevel": "Competitive Examination (RPSC RAS)",
            "about": {
                "@type": "Thing",
                "name": subject
            },
            "provider": publisher,
            "author": author
        }
        if num_q:
            schema["numberOfQuestions"] = num_q
    elif rel.startswith("show/"):
        schema = {
            "@context": "https://schema.org",
            "@type": "LearningResource",
            "name": title,
            "description": description,
            "url": canonical,
            "inLanguage": "hi",
            "isAccessibleForFree": True,
            "provider": publisher,
            "author": author
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "LearningResource",
            "name": title,
            "description": description,
            "url": canonical,
            "learningResourceType": "Study Notes",
            "inLanguage": "hi",
            "isAccessibleForFree": True,
            "educationalLevel": "Competitive Examination (RPSC RAS)",
            "about": {
                "@type": "Thing",
                "name": subject
            },
            "provider": publisher,
            "author": author
        }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'


def ensure_html_lang(content: str) -> str:
    m = re.search(r"<html\b([^>]*)>", content, re.I)
    if m:
        attrs = m.group(1)
        if not re.search(r"\blang\s*=", attrs, re.I):
            new_tag = f'<html lang="hi"{attrs}>'
            return content[:m.start(0)] + new_tag + content[m.end(0):]
    return content


def ensure_viewport(head: str) -> str:
    if not re.search(r'<meta\b[^>]*\bname=["\']viewport["\']', head, re.I):
        vp_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        return vp_tag + "\n" + head
    return head


def ensure_schema_org(head: str, rel: str, title: str, description: str, canonical: str, original: str) -> str:
    if not re.search(r'<script\b[^>]*type=["\']application/ld\+json["\']', original, re.I):
        json_ld_script = generate_json_ld(rel, title, description, canonical, original)
        return insert_into_head(head, json_ld_script)
    return head


def process_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    original = ensure_html_lang(original)

    m = HEAD_RE.search(original)
    if not m:
        return False
    head = m.group(1)
    head = ensure_viewport(head)

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

    if should_noindex(rel, existing_title, head):
        if existing_robots and "nofollow" in existing_robots.lower():
            head = replace_or_insert_named_meta(head, "robots", "noindex, nofollow")
        else:
            head = replace_or_insert_named_meta(head, "robots", "noindex, follow")
    else:
        # Google AI Overviews and Snippet Directives
        head = replace_or_insert_named_meta(
            head, "robots", "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
        )

    head = replace_or_insert_named_meta(head, "author", "Omkar Singh Gurjar")
    head = replace_or_insert_named_meta(head, "referrer", "strict-origin-when-cross-origin")
    head = replace_or_insert_named_meta(head, "theme-color", "#1B2A6B")
    head = replace_or_insert_canonical(head, canonical)

    page_type = "article" if re.search(r"-ch\d+[-.]", rel) or rel.startswith("current-affairs/") else "website"
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

    head = ensure_schema_org(head, rel, title, description, canonical, original)

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


def load_existing_sitemap() -> dict[str, str]:
    sitemap_path = ROOT / "sitemap.xml"
    if not sitemap_path.exists():
        return {}
    txt = sitemap_path.read_text(encoding="utf-8", errors="ignore")
    return dict(re.findall(r"<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>", txt))


def write_sitemap() -> None:
    existing_dates = load_existing_sitemap()
    rows: list[tuple[str, str]] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or path.name.lower() == "404.html":
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        hm = HEAD_RE.search(raw)
        head = hm.group(1) if hm else ""
        if re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^\"\']*noindex', head, re.I):
            continue
        loc = canonical_for(path)
        lastmod = existing_dates.get(loc)
        if not lastmod:
            lastmod = git_lastmod(path)
        rows.append((loc, lastmod))

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
        if re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\']([^"\']*)["\']', head, re.I):
            rm = re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\']([^"\']*)["\']', head, re.I)
            if "noindex" in rm.group(1).lower():
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
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" not in path.parts and process_html(path):
            changed += 1
    write_sitemap()
    write_search_index()
    print(f"SEO optimizer updated {changed} HTML pages.")


if __name__ == "__main__":
    main()
