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
    "rajasthan-itihas.html",
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
        return tag_re.sub(lambda _m: replacement, head, count=1)
    return insert_into_head(head, replacement)


def replace_or_insert_property_meta(head: str, prop: str, value: str) -> str:
    tag_re = re.compile(r'<meta\b[^>]*\bproperty=["\']' + re.escape(prop) + r'["\'][^>]*>', re.I)
    replacement = f'<meta property="{html.escape(prop, quote=True)}" content="{html.escape(value, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(lambda _m: replacement, head, count=1)
    return insert_into_head(head, replacement)


def replace_or_insert_canonical(head: str, canonical: str) -> str:
    tag_re = re.compile(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*>', re.I)
    replacement = f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
    if tag_re.search(head):
        return tag_re.sub(lambda _m: replacement, head, count=1)
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
            base_rel = base_path.relative_to(ROOT).as_posix()
            return urljoin(SITE, DUPLICATE_CANONICAL.get(base_rel, base_rel))
    if rel in DUPLICATE_CANONICAL:
        return urljoin(SITE, DUPLICATE_CANONICAL[rel])
    return urljoin(SITE, rel)


BRAND = "Omkar Sir"
TITLE_MAX = 60
DESC_MAX = 155
BRAND_SUFFIX_RE = re.compile(
    r"(?:\s*[|\-\u2013\u2014:]\s*(?:Omkar\s*Sir(?:\s*Official)?|New\s*India\s*Education(?:\s*\(NIEd\))?|NIEd|NIEOM))+\s*$",
    re.I,
)


def title_core(title_text: str) -> str:
    t = strip_tags(title_text).strip()
    prev = None
    while prev != t:
        prev = t
        t = BRAND_SUFFIX_RE.sub("", t).strip()
    return t


def _cut_words(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit + 1]
    sp = cut.rfind(" ")
    cut = cut[:sp] if sp > limit * 0.6 else text[:limit]
    return cut.rstrip(" ,;:|\u2014\u2013-\u0964(")


VARIANT_LABEL_RE = re.compile(
    r"^(?:Bilingual\s+)?(?:Solution\s+Booklet|Question\s+Paper|Answer\s+Key(?:\s+Sheet)?|Workbook(?:\s*\(Hindi\))?|"
    r"Model\s+Answer(?:\s*\(Hindi\))?|PPT(?:\s*PDF)?|Full\s+Set|Read|English)$",
    re.I,
)


def fit_title(core: str, label: str | None = None) -> str:
    """Return a title <= TITLE_MAX chars ending in ' | Omkar Sir'.
    A variant label (booklet type, 'English') is always kept at the end so twins stay unique.
    Idempotent: fit_title(title_core(fit_title(x))) == fit_title(x)."""
    core = re.sub(r"\s+", " ", core).strip()
    if not core:
        return "RAS Exam Preparation | " + BRAND
    suffix = " | " + BRAND
    parts = re.split(r"\s+(?:\u2014|\||\u2013)\s+", core)
    if label is None and len(parts) > 1 and VARIANT_LABEL_RE.match(parts[-1].strip()):
        label = parts[-1].strip()
        parts = parts[:-1]
    elif label is not None and len(parts) > 1 and parts[-1].strip().lower() == label.lower():
        parts = parts[:-1]
    tail = f" \u2014 {label}" if label else ""
    budget = TITLE_MAX - len(suffix) - len(tail)
    joined = " \u2014 ".join(parts) if label else core
    if len(joined) <= budget:
        return joined + tail + suffix
    while len(parts) > 1:
        parts = parts[:-1]
        cand = " \u2014 ".join(parts)
        if len(cand) >= 12 and len(cand) <= budget:
            return cand + tail + suffix
    return _cut_words(parts[0], budget) + tail + suffix


def clean_title(title_text: str) -> str:
    return fit_title(title_core(title_text))


def title_for(rel: str, existing: str | None, h1: str | None) -> str:
    if rel == "index.html":
        return "RAS Exam 2026 Preparation: Notes, PYQ, Tests | Omkar Sir"
    label = "English" if rel.endswith("-english.html") else None
    current = title_core(existing or "")
    dm = re.match(r"current-affairs/\d{4}-\d{2}-\d{2}\.html$", rel) and re.match(r"^(\d{1,2} \S+ \d{4})", current)
    if dm:
        return fit_title(f"{dm.group(1)} Current Affairs Rajasthan & India")
    if label and re.search(r"\(English\)\s*$", current):
        current = re.sub(r"\s*\(English\)\s*$", "", current)
    if current and current.lower() not in {"home", "index", "omkar sir", "new india education"}:
        return fit_title(current, label)
    base = h1 or Path(rel).stem.replace("-", " ").title()
    return fit_title(base, label)


def cap_desc(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= DESC_MAX:
        return text
    return _cut_words(text, DESC_MAX - 1) + "\u2026"


def description_for(rel: str, existing: str | None, h1: str | None, first_p: str | None) -> str:
    if rel == "index.html":
        return cap_desc("RAS Exam 2026: Notes, Syllabus, PYQ, Test Series और Courses। NCERT, RBSE प्रामाणिक स्रोतों से तैयार — 6 लाख+ सफल विद्यार्थी, 8 साल का अनुभव।")
    current = strip_tags(existing or "")
    boilerplate = ["NCERT, RBSE की मूल पुस्तकों व प्रामाणिक स्रोतों से तैयार", "विश्वसनीय एवं बेहतरीन Content"]
    weak = not current or len(current) < 70 or (all(x in current for x in boilerplate) and len(current) > 150)
    if not weak:
        return cap_desc(current)
    topic = h1 or Path(rel).stem.replace("-", " ").title()
    supporting = strip_tags(first_p or "")
    if supporting:
        text = f"{topic} — RAS और Rajasthan competitive exams की तैयारी के लिए आसान Hindi notes और study material. {supporting}"
    else:
        text = f"{topic} — RAS, RPSC और Rajasthan competitive exams की तैयारी के लिए Hindi study material, notes और revision resources."
    return cap_desc(text)


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
            "url": "https://omkarsir.com/favicon-512.png"
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


# ---------------------------------------------------------------------------
# Extended SEO (2026-10-26): duplicates, hreflang, site-wide JSON-LD graph,
# breadcrumbs, JSON-LD hygiene, image alt, single H1, sitemap index.
# Everything below is idempotent: running the optimizer twice yields no diff.
# ---------------------------------------------------------------------------
ORG_ID = SITE + "#organization"
WEBSITE_ID = SITE + "#website"
PERSON_ID = SITE + "#omkar-sir"
DEFAULT_IMAGE = urljoin(SITE, "og-image.png")
LOGO_URL = urljoin(SITE, "favicon-512.png")
SAME_AS = [
    "https://youtube.com/@thenewindiaeducation",
    "https://t.me/omkarsirofficial",
    "https://instagram.com/omkar_sir_official",
    "https://whatsapp.com/channel/0029Va4yS7h6buMLgA7alj3H",
    "https://play.google.com/store/apps/details?id=co.april2019.techa",
]

# Duplicate pages -> page to keep (same questions / superseded copy). The
# duplicates stay online until the owner approves removal; meanwhile their
# canonical points at the keeper so search engines consolidate signals.
DUPLICATE_CANONICAL = {
    "quizzes/150-2026-08-17-ojuw.html": "quizzes/150-2026-08-17-1ppa.html",
    "quizzes/top-150-mcqs-2026-08-17-8kat.html": "quizzes/150-2026-08-17-1ppa.html",
    "quizzes/modern-hisotry-check-2026-08-17-8h6d.html": "quizzes/modern-history-check-2026-08-17-qd80.html",
    "quizzes/check-15-sawal-2026-08-04-r3p4.html": "quizzes/ras-prelims-exam-2026-08-04-1tsu.html",
    "quizzes/200-pyqs-based-mcq-india-polity-2026-09-16-fibu.html": "quizzes/top-300-mcqs-polity-and-constitution-2026-09-16-6tm2.html",
    "pubadchpater02.html": "lok-prashasan-ch02-siddhant-upagam.html",
    "rajasthanlakes.html": "rajasthan-lakes.html",
    "rajvegetation.html": "rajasthan-bhugol-ch04-vanaspati-vanyajeev.html",
}

# Thin utility pages that should not be indexed (JS-only detail views etc.)
EXTRA_NOINDEX = {"mains-test-detail.html"}

HUB_FOR_DIR = {
    "quizzes": "all-quizzes.html",
    "quiz": "all-quizzes.html",
    "current-affairs": "current-affairs.html",
    "vacancy": "vacancy.html",
}
SERIES_HUB_OVERRIDE = {"prachin-bharat": "prachin-bharat-itihas.html"}
LDJSON_RE = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
GRAPH_RE = re.compile(r'\s*<script type="application/ld\+json" id="seo-graph">.*?</script>', re.S)
HREFLANG_RE = re.compile(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*" data-seo>', re.I)
_TITLE_CACHE: dict[str, str] = {}


def keeper_for(rel: str) -> str | None:
    return DUPLICATE_CANONICAL.get(rel)


def _sub_once(pattern: re.Pattern, repl: str, text: str) -> str:
    return pattern.sub(lambda _m: repl, text, count=1)


def page_title_core(rel: str) -> str:
    """Final (fitted) title of another page without the brand, for breadcrumb names."""
    if rel in _TITLE_CACHE:
        return _TITLE_CACHE[rel]
    p = ROOT / rel
    name = Path(rel).stem.replace("-", " ").title()
    if p.exists():
        raw = p.read_text(encoding="utf-8", errors="ignore")
        hm = HEAD_RE.search(raw)
        tm = TITLE_RE.search(hm.group(1) if hm else raw)
        h1m = H1_RE.search(raw)
        t = title_for(rel, strip_tags(tm.group(0)) if tm else None, strip_tags(h1m.group(1)) if h1m else None)
        name = title_core(t) or name
    _TITLE_CACHE[rel] = name
    return name


def hub_for(rel: str) -> str | None:
    if "/" in rel:
        hub = HUB_FOR_DIR.get(rel.split("/", 1)[0])
        return hub if hub and (ROOT / hub).exists() else None
    m = re.match(r"^([a-z0-9-]+?)-ch\d+[a-z]?-.*?(-english)?\.html$", rel)
    if not m:
        return None
    series = m.group(1)
    cands = [SERIES_HUB_OVERRIDE.get(series, series + ".html")]
    if m.group(2):
        cands.insert(0, series + "-english.html")
    for c in cands:
        if c != rel and (ROOT / c).exists():
            return c
    return None


def breadcrumb_items(rel: str, title: str, canonical: str) -> list[dict]:
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE}]
    hub = hub_for(rel)
    if hub:
        items.append({"@type": "ListItem", "position": 2, "name": page_title_core(hub), "item": urljoin(SITE, hub)})
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": title_core(title) or title, "item": canonical})
    return items


def iter_nodes(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_nodes(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_nodes(v)


def node_types(node: dict) -> set[str]:
    t = node.get("@type")
    return set(t if isinstance(t, list) else [t]) if t else set()


def existing_ld_types(content: str) -> set[str]:
    types: set[str] = set()
    for m in LDJSON_RE.finditer(GRAPH_RE.sub("", content)):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        for n in iter_nodes(data):
            types |= node_types(n)
    return types


def first_ld_image(content: str) -> str | None:
    for m in LDJSON_RE.finditer(GRAPH_RE.sub("", content)):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        for n in iter_nodes(data):
            if node_types(n) & {"Product", "Book", "Course"}:
                img = n.get("image")
                if isinstance(img, list):
                    img = img[0] if img else None
                if isinstance(img, dict):
                    img = img.get("url")
                if isinstance(img, str) and img.startswith(SITE):
                    if (ROOT / img[len(SITE):].split("?")[0]).exists():
                        return img
    return None


def visible_text(content: str) -> str:
    body = re.search(r"<body\b[^>]*>(.*)</body>", content, re.I | re.S)
    return re.sub(r"\s+", " ", strip_tags(body.group(1) if body else content))


def _norm(s: str) -> str:
    return re.sub(r"[^\w\u0900-\u097F]+", "", s).lower()


def patch_existing_jsonld(content: str, rel: str, image: str, canonical: str) -> str:
    """Hygiene on hand-written/generated JSON-LD blocks (not seo-graph):
    - broken logo.png -> real square logo
    - NewsArticle/Article: add image + mainEntityOfPage when missing
    - FAQPage: drop questions that are not visible on the page (Google policy);
      drop the FAQPage entirely when none are visible."""
    vis = None

    def fix_block(m: re.Match) -> str:
        nonlocal vis
        whole, raw = m.group(0), m.group(1)
        if 'id="seo-graph"' in whole[:80]:
            return whole
        try:
            data = json.loads(raw)
        except Exception:
            return whole
        changed = False
        if "https://omkarsir.com/logo.png" in raw:
            data = json.loads(raw.replace("https://omkarsir.com/logo.png", LOGO_URL))
            changed = True
        drop_block = False
        for n in list(iter_nodes(data)):
            t = node_types(n)
            if t & {"NewsArticle", "Article", "BlogPosting"}:
                if "image" not in n:
                    n["image"] = image
                    changed = True
                if "mainEntityOfPage" not in n:
                    n["mainEntityOfPage"] = canonical
                    changed = True
            if "FAQPage" in t and isinstance(n.get("mainEntity"), list):
                if vis is None:
                    vis = _norm(visible_text(content))
                keep = [q for q in n["mainEntity"] if isinstance(q, dict) and _norm(str(q.get("name", "")))[:30] in vis]
                if len(keep) != len(n["mainEntity"]):
                    changed = True
                    if keep:
                        n["mainEntity"] = keep
                    else:
                        n["@type"] = "__drop__"
        if not changed:
            return whole

        def prune(x):
            if isinstance(x, dict):
                return {k: prune(v) for k, v in x.items()}
            if isinstance(x, list):
                return [prune(v) for v in x if not (isinstance(v, dict) and v.get("@type") == "__drop__")]
            return x
        if isinstance(data, dict) and data.get("@type") == "__drop__":
            drop_block = True
        data = prune(data)
        if isinstance(data, dict) and "@graph" in data and not data["@graph"]:
            drop_block = True
        if drop_block:
            return ""
        open_tag = whole[: whole.index(">") + 1]
        return f"{open_tag}\n{json.dumps(data, ensure_ascii=False, indent=2)}\n</script>"

    return LDJSON_RE.sub(fix_block, content)


def build_graph(rel: str, title: str, description: str, canonical: str, image: str, lang: str, content: str) -> str:
    have = existing_ld_types(content)
    org = {
        "@type": ["EducationalOrganization", "Organization"],
        "@id": ORG_ID,
        "name": "New India Education",
        "alternateName": ["NIEOM Academy", "NIEOM", "NIEd", "Omkar Sir"],
        "url": SITE,
        "logo": {"@type": "ImageObject", "url": LOGO_URL, "width": 512, "height": 512},
        "image": DEFAULT_IMAGE,
        "email": "email2omkara@gmail.com",
        "telephone": "+91-7023166962",
        "address": {"@type": "PostalAddress", "addressLocality": "Jaipur", "addressRegion": "Rajasthan", "addressCountry": "IN"},
        "founder": {"@id": PERSON_ID},
        "sameAs": SAME_AS,
    }
    person = {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": "Omkar Singh Gurjar",
        "alternateName": ["Omkar Sir", "ओमकार सर"],
        "jobTitle": "Founder & Educator, New India Education",
        "url": urljoin(SITE, "about.html"),
        "worksFor": {"@id": ORG_ID},
        "knowsAbout": ["RAS Exam", "Rajasthan GK", "Indian History", "Indian Polity", "Rajasthan Economy"],
        "sameAs": SAME_AS[:3],
    }
    website = {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        "url": SITE,
        "name": "Omkar Sir",
        "alternateName": "omkarsir.com",
        "inLanguage": "hi",
        "publisher": {"@id": ORG_ID},
    }
    graph: list[dict] = [org, person, website]
    if rel != "index.html":
        if not (have & {"WebPage", "CollectionPage", "ContactPage", "AboutPage", "ItemPage", "FAQPage"}):
            graph.append({
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": lang,
                "isPartOf": {"@id": WEBSITE_ID},
                "publisher": {"@id": ORG_ID},
                "primaryImageOfPage": {"@type": "ImageObject", "url": image},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            })
        if "BreadcrumbList" not in have:
            graph.append({
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumb",
                "itemListElement": breadcrumb_items(rel, title, canonical),
            })
        if rel.startswith("current-affairs/") and not (have & {"NewsArticle", "Article"}):
            dm = re.search(r"(\d{4}-\d{2}-\d{2})", rel)
            if dm:
                graph.append({
                    "@type": "NewsArticle",
                    "headline": title_core(title)[:110],
                    "description": description,
                    "datePublished": dm.group(1),
                    "inLanguage": lang,
                    "url": canonical,
                    "mainEntityOfPage": canonical,
                    "image": image,
                    "author": {"@id": PERSON_ID},
                    "publisher": {"@id": ORG_ID},
                })
    data = {"@context": "https://schema.org", "@graph": graph}
    return f'<script type="application/ld+json" id="seo-graph">{json.dumps(data, ensure_ascii=False, separators=(",", ":"))}</script>'


def english_pair(rel: str) -> tuple[str, str] | None:
    """(hindi_rel, english_rel) when this page has a -english twin."""
    if rel.endswith("-english.html"):
        hi = rel[: -len("-english.html")] + ".html"
        return (hi, rel) if (ROOT / hi).exists() else None
    en = rel[: -len(".html")] + "-english.html"
    return (rel, en) if (ROOT / en).exists() else None


H1_RESET_RE = re.compile(r'\s*<style id="seo-h1-reset">.*?</style>', re.S)
H1_RESET = '<style id="seo-h1-reset">:where(h1.st){margin:0;font-size:inherit;font-weight:inherit;line-height:inherit}</style>'


def fix_body(content: str, rel: str, h1_text: str | None, indexable: bool) -> str:
    """Body-level fixes that keep the visible design identical."""
    # (a) quiz pages: promote the single start-screen title <div class="st"> to <h1 class="st">.
    #     :where() has zero specificity, so the page's own .st rules still win -> no visual change.
    if indexable and not H1_RE.search(content):
        if len(re.findall(r'<div class="st">', content)) == 1:
            content = re.sub(r'<div class="st">(.*?)</div>', r'<h1 class="st">\1</h1>', content, count=1, flags=re.S)
    if '<h1 class="st">' in content and 'id="seo-h1-reset"' not in content:
        anchor = '<script type="application/ld+json" id="seo-graph">'
        if anchor in content:
            content = content.replace(anchor, H1_RESET + "\n" + anchor, 1)
        else:
            content = re.sub(r"</head>", lambda _m: H1_RESET + "\n</head>", content, count=1, flags=re.I)
    # (b) hidden PDF-cover clone on daily current-affairs pages carries a second <h1>.
    content = content.replace(
        '<h1 style="font-size:22px;color:#1B2A6B;font-weight:800;line-height:1.4;margin-bottom:12px;">',
        '<div style="font-size:22px;color:#1B2A6B;font-weight:800;line-height:1.4;margin-top:.67em;margin-bottom:12px;">',
    )
    if "margin-top:.67em;margin-bottom:12px;\">" in content:
        content = re.sub(
            r'(<div style="font-size:22px;color:#1B2A6B;font-weight:800;line-height:1\.4;margin-top:\.67em;margin-bottom:12px;">.*?)</h1>',
            r"\1</div>", content, count=1, flags=re.S)
    # (c) meaningful alt text for content images that have alt="" (never touches decorative SVG/icons)
    content = fix_empty_alts(content, rel, h1_text)
    # (d) broken internal links found in the audit
    content = content.replace('href="/privacy-policy.html"', 'href="/privacy.html"')
    content = content.replace(
        "https://www.omkarsir.com/quizzes/top-150-mcqs-2026-08-17-3a49.html",
        "https://www.omkarsir.com/quizzes/150-2026-08-17-1ppa.html")
    return content


STORE_NAMES = {
    "adhunik-bharat-itihas": "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    "adhunik": "सम्पूर्ण आधुनिक भारत का इतिहास PDF",
    "rajasthan-itihas": "सम्पूर्ण राजस्थान का इतिहास PDF",
    "rajasthan": "सम्पूर्ण राजस्थान का इतिहास PDF",
    "ras-mains-paper-2": "RAS Mains Paper-II PYQ PDF",
    "ras-p2": "RAS Mains Paper-II PYQ PDF",
    "rajasthan-arthvyavastha": "राजस्थान आर्थिक समीक्षा 2025-26 एवं बजट PDF",
}


def fix_empty_alts(content: str, rel: str, h1_text: str | None) -> str:
    counter = {"n": 0}

    def repl(m: re.Match) -> str:
        tag = m.group(0)
        src = attr_value(tag, "src") or ""
        if not src.startswith(("/assets/", "assets/", "../assets/")) or src.endswith(".svg"):
            return tag
        fname = Path(src).stem
        alt = None
        sm = re.match(r"(.+?)-(poster|cover)(?:-\d+)?$", fname)
        pm = re.match(r"(.+?)-preview-(\d+)$", fname)
        if sm and sm.group(1) in STORE_NAMES:
            alt = f"{STORE_NAMES[sm.group(1)]} — मुखपृष्ठ"
        elif pm and pm.group(1) in STORE_NAMES:
            alt = f"{STORE_NAMES[pm.group(1)]} — नमूना पृष्ठ {pm.group(2)}"
        else:
            fm = re.search(r"fig(\d+)", fname)
            if fm and h1_text:
                alt = f"{h1_text[:80]} — चित्र {fm.group(1)}"
        if not alt:
            return tag
        return re.sub(r'\balt=""', lambda _m: f'alt="{html.escape(alt, quote=True)}"', tag, count=1)

    return re.sub(r'<img\b[^>]*\balt=""[^>]*>', repl, content, flags=re.I)



def process_html(path: Path) -> bool:
    raw_original = path.read_text(encoding="utf-8")
    original = ensure_html_lang(raw_original)

    m = HEAD_RE.search(original)
    if not m:
        return False
    head = m.group(1)
    head = ensure_viewport(head)
    # generated blocks are rebuilt at fixed positions every run (keeps the optimizer idempotent)
    head = GRAPH_RE.sub("", head)
    head = H1_RESET_RE.sub("", head)

    rel = path.relative_to(ROOT).as_posix()
    canonical = canonical_for(path)
    title_match = TITLE_RE.search(head)
    existing_title = strip_tags(title_match.group(0)) if title_match else None
    h1_match = H1_RE.search(original)
    h1 = strip_tags(h1_match.group(1)) if h1_match else None
    if not h1:
        st = re.search(r'<(?:div|h1) class="st">(.*?)</(?:div|h1)>', original, re.S)
        h1 = strip_tags(st.group(1)) if st else None
    p_match = P_RE.search(original)
    first_p = strip_tags(p_match.group(1)) if p_match else None
    title = title_for(rel, existing_title, h1)
    description = description_for(rel, existing_meta(head, "description"), h1, first_p)
    lang_m = re.search(r'<html\b[^>]*\blang=["\']([a-zA-Z-]+)', original, re.I)
    lang = (lang_m.group(1).lower() if lang_m else "hi")[:2]

    if title_match:
        head = _sub_once(TITLE_RE, f"<title>{html.escape(title)}</title>", head)
    else:
        head = insert_into_head(head, f"<title>{html.escape(title)}</title>")

    head = replace_or_insert_named_meta(head, "description", description)
    existing_robots = existing_meta(head, "robots")

    noindex = should_noindex(rel, existing_title, head) or rel in EXTRA_NOINDEX
    if noindex:
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

    # hreflang for Hindi/English twins (e.g. jiv-vigyan-ch01-koshika / -english)
    head = HREFLANG_RE.sub("", head)
    pair = english_pair(rel)
    if pair and not noindex and not keeper_for(pair[0]):
        hi_url, en_url = urljoin(SITE, pair[0]), urljoin(SITE, pair[1])
        links = "".join(
            f'\n<link rel="alternate" hreflang="{code}" href="{url}" data-seo>'
            for code, url in (("hi", hi_url), ("en", en_url), ("x-default", hi_url)))
        head = re.sub(r'(<link\b[^>]*\brel=["\']canonical["\'][^>]*>)', lambda mm: mm.group(1) + links, head, count=1, flags=re.I)

    # og:image must be JPG/PNG for reliable WhatsApp/Telegram previews; product WebP posters stay in Product JSON-LD.
    _pimg = first_ld_image(original)
    image = _pimg if _pimg and _pimg.lower().endswith((".jpg", ".jpeg", ".png")) else DEFAULT_IMAGE
    page_type = "article" if re.search(r"-ch\d+[-.]", rel) or rel.startswith("current-affairs/") else "website"
    if _pimg:
        page_type = "product"
    og = [
        ("og:title", title),
        ("og:description", description),
        ("og:url", canonical),
        ("og:type", page_type),
        ("og:site_name", "Omkar Sir | New India Education"),
        ("og:locale", "en_IN" if lang == "en" else "hi_IN"),
        ("og:image", image),
        ("og:image:alt", title),
    ]
    if image == DEFAULT_IMAGE:
        og += [("og:image:width", "1200"), ("og:image:height", "630")]
    for prop, value in og:
        head = replace_or_insert_property_meta(head, prop, value)

    for name, value in [
        ("twitter:card", "summary_large_image"),
        ("twitter:title", title),
        ("twitter:description", description),
        ("twitter:url", canonical),
        ("twitter:image", image),
        ("twitter:image:alt", title),
    ]:
        head = replace_or_insert_named_meta(head, name, value)

    head = ensure_schema_org(head, rel, title, description, canonical, original)

    updated = original[:m.start(1)] + head + original[m.end(1):]

    # JSON-LD hygiene on existing blocks, then the site-wide graph (rebuilt each run)
    updated = patch_existing_jsonld(updated, rel, image, canonical)
    updated = GRAPH_RE.sub("", updated)
    if not noindex and not rel.startswith("show/"):
        graph = build_graph(rel, title, description, canonical, image, lang, updated)
        updated = re.sub(r"\s*</head>", lambda _m: "\n" + graph + "\n</head>", updated, count=1, flags=re.I)
    updated = fix_body(updated, rel, h1, not noindex)

    if updated != raw_original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _content_lastmods() -> dict[str, str]:
    """Last date each file's content changed, ignoring bot-only SEO/automation commits
    (so a site-wide SEO pass does not make every page look 'modified today')."""
    out: dict[str, str] = {}
    try:
        res = subprocess.run(
            ["git", "-c", "core.quotepath=false", "log", "--format=@@%cs %s", "--name-only", "--", "*.html"],
            cwd=ROOT, capture_output=True, text=True, check=True)
    except Exception:
        return out
    skip = False
    day = ""
    for line in res.stdout.splitlines():
        if line.startswith("@@"):
            day, _, subj = line[2:].partition(" ")
            skip = bool(re.match(r"(SEO:|Auto:)", subj))
            continue
        f = line.strip()
        if f and not skip and f not in out:
            out[f] = day
    return out


SITEMAP_GROUPS = [
    ("sitemap-pages.xml", lambda rel: "/" not in rel),
    ("sitemap-quizzes.xml", lambda rel: rel.startswith(("quizzes/", "quiz/"))),
    ("sitemap-current-affairs.xml", lambda rel: rel.startswith("current-affairs/")),
    ("sitemap-vacancy.xml", lambda rel: rel.startswith("vacancy/")),
]


def write_sitemap() -> None:
    lastmods = _content_lastmods()
    rows: dict[str, list[tuple[str, str]]] = {name: [] for name, _ in SITEMAP_GROUPS}
    total = 0
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or path.name.lower() == "404.html":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("show/") or keeper_for(rel):
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        hm = HEAD_RE.search(raw)
        head = hm.group(1) if hm else ""
        if re.search(r'<meta\b[^>]*\bname=["\']robots["\'][^>]*\bcontent=["\'][^\"\']*noindex', head, re.I):
            continue
        cm = re.search(r'<link\b[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\']([^"\']+)', head, re.I)
        loc = canonical_for(path)
        if cm and html.unescape(cm.group(1)) != loc:
            continue
        lastmod = lastmods.get(rel) or git_lastmod(path)
        for name, pred in SITEMAP_GROUPS:
            if pred(rel):
                rows[name].append((loc, lastmod))
                total += 1
                break
    index_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name, entries in rows.items():
        if not entries:
            continue
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for loc, lastmod in entries:
            lines += ["  <url>", f"    <loc>{html.escape(loc)}</loc>", f"    <lastmod>{lastmod}</lastmod>", "  </url>"]
        lines.append("</urlset>")
        (ROOT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        newest = max(lm for _, lm in entries)
        index_lines += ["  <sitemap>", f"    <loc>{SITE}{name}</loc>", f"    <lastmod>{newest}</lastmod>", "  </sitemap>"]
    index_lines.append("</sitemapindex>")
    (ROOT / "sitemap.xml").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Sitemap index lists {total} indexable HTML URLs across {sum(1 for v in rows.values() if v)} files.")


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


SEARCH_INDEX_EXCLUDE = {"404.html", "admin-comments.html", "pdf-chapter-splitter.html"}


def write_search_index() -> None:
    entries: list[dict[str, str]] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in SEARCH_INDEX_EXCLUDE or keeper_for(rel):
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
            desc = cap_desc(desc)
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
