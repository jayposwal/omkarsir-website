import html
import re
import os
import sys
from html.parser import HTMLParser

WEBSITE_DIR = '/Users/omkarsingh/Desktop/omkarsir-website'
DOWNLOADS_HTML = '/Users/omkarsingh/Downloads/समाजशास्त्र  SOCIOLOGY (RAS MAINS) /SOCIOLOGY_RASMAINS_.html'

print("Reading source HTML file...")
with open(DOWNLOADS_HTML, 'r', encoding='utf-8', errors='ignore') as f:
    raw = f.read()

# Parse CSS for bold and italic classes
style_match = re.search(r'<style[^>]*>(.*?)</style>', raw, re.DOTALL)
bold_classes = set()
italic_classes = set()
if style_match:
    for sel, rules in re.findall(r'(\.[a-zA-Z0-9_-]+)\s*\{([^}]+)\}', style_match.group(1)):
        cls = sel[1:]
        r_clean = rules.replace(' ', '')
        if 'font-weight:700' in r_clean or 'font-weight:bold' in r_clean:
            bold_classes.add(cls)
        if 'font-style:italic' in r_clean:
            italic_classes.add(cls)

text = html.unescape(raw)

class Node:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs) if attrs else {}
        self.children = []
        self.parent = None

    def get_text(self):
        res = []
        for c in self.children:
            if isinstance(c, str):
                res.append(c)
            elif isinstance(c, Node):
                res.append(c.get_text())
        return ''.join(res)

    def render_inline(self):
        res = []
        for c in self.children:
            if isinstance(c, str):
                res.append(html.escape(c, quote=False))
            elif isinstance(c, Node):
                if c.tag == 'br':
                    res.append('<br>')
                    continue
                t = c.render_inline()
                classes = c.attrs.get('class', '').split()
                is_bold = any(cls in bold_classes for cls in classes)
                is_italic = any(cls in italic_classes for cls in classes)
                if is_bold and is_italic:
                    res.append(f'<strong><em>{t}</em></strong>')
                elif is_bold:
                    res.append(f'<strong>{t}</strong>')
                elif is_italic:
                    res.append(f'<em>{t}</em>')
                else:
                    res.append(t)
        return ''.join(res)

class DocParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node('root')
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        if tag in ('br', 'hr', 'img'):
            node = Node(tag, attrs)
            node.parent = self.current
            self.current.children.append(node)
            return
        node = Node(tag, attrs)
        node.parent = self.current
        self.current.children.append(node)
        self.current = node

    def handle_endtag(self, tag):
        if tag in ('br', 'hr', 'img'):
            return
        p = self.current
        while p and p.tag != tag and p.parent:
            p = p.parent
        if p and p.parent:
            self.current = p.parent

    def handle_data(self, data):
        self.current.children.append(data)

def get_table_rows(table_node):
    rows = []
    def find_tr(n):
        for child in n.children:
            if isinstance(child, Node):
                if child.tag == 'tr':
                    rows.append(child)
                else:
                    find_tr(child)
    find_tr(table_node)
    return rows

def get_row_cells(row_node):
    cells = []
    for child in row_node.children:
        if isinstance(child, Node) and child.tag in ('td', 'th'):
            cells.append(child)
    return cells

def render_cell_paragraphs(cell):
    paras = [c for c in cell.children if isinstance(c, Node) and c.tag == 'p']
    if paras:
        p_htmls = []
        for p in paras:
            ptxt = p.get_text().strip()
            if ptxt and ptxt != '&nbsp;':
                p_htmls.append(f'<p>{p.render_inline()}</p>')
        return ''.join(p_htmls)
    else:
        txt = cell.render_inline().strip()
        return f'<p>{txt}</p>' if txt else ''

# Locate the 7 chapter offsets dynamically
ch_starts = []
for i in range(7):
    m = re.search(rf'<table[^>]*>(?:(?!<table).)*?अध्याय\s*{i}(?:(?!<table).)*?</table>', text, re.DOTALL)
    if m:
        ch_starts.append((m.start(), i))
ch_starts.sort()
ch_offsets = [pos for pos, idx in ch_starts] + [len(text)]
print(f"Detected {len(ch_starts)} chapter start offsets: {ch_offsets}")

CHAPTER_CONFIGS = [
    {
        "src_idx": 0,
        "out_file": "samajshastra-ch01-parichay.html",
        "badge": "🔭 अध्याय 1/7 — समाजशास्त्र",
        "h1": "समाजशास्त्र — परिचय एवं पाठ्यक्रम रूपरेखा",
        "sub": "RAS मुख्य परीक्षा, पेपर-I, यूनिट-3 — भारतीय समाज में समाजशास्त्रीय चिंतन | RAS Pre + Mains",
        "page_title": "अध्याय 1: समाजशास्त्र — परिचय एवं पाठ्यक्रम रूपरेखा | Omkar Sir",
        "desc": "समाजशास्त्र — परिचय एवं पाठ्यक्रम रूपरेखा (RAS Mains Paper 1, Unit 3). समाजशास्त्र का उद्भव, प्रमुख भारतीय समाजशास्त्री (घुर्ये, श्रीनिवास, देसाई, मुकर्जी) एवं सम्पूर्ण पाठ्यक्रम।",
        "prev_link": "samajshastra.html",
        "prev_label": "← समाजशास्त्र मुख्य पृष्ठ",
        "next_link": "samajshastra-ch02-jati-varg.html",
        "next_label": "अध्याय 2: जाति एवं वर्ग की अवधारणा →",
    },
    {
        "src_idx": 1,
        "out_file": "samajshastra-ch02-jati-varg.html",
        "badge": "🏛️ अध्याय 2/7 — समाजशास्त्र",
        "h1": "जाति एवं वर्ग की अवधारणा",
        "sub": "भारतीय समाज में जाति एवं वर्ग के बदलते आयाम — अवधारणा, सिद्धांत एवं परिवर्तनशील स्वरूप | RAS Pre + Mains",
        "page_title": "अध्याय 2: जाति एवं वर्ग की अवधारणा — समाजशास्त्र | Omkar Sir",
        "desc": "जाति एवं वर्ग की अवधारणा — सामाजिक स्तरीकरण, वर्ण बनाम जाति, उत्पत्ति के सिद्धांत, घुर्ये की 6 विशेषताएं, जजमानी व्यवस्था, प्रभु जाति, वर्ग के बदलते आयाम एवं तुलनात्मक विश्लेषण।",
        "prev_link": "samajshastra-ch01-parichay.html",
        "prev_label": "← अध्याय 1: समाजशास्त्र — परिचय",
        "next_link": "samajshastra-ch03-parivartan.html",
        "next_label": "अध्याय 3: समकालीन समाज में परिवर्तन →",
    },
    {
        "src_idx": 2,
        "out_file": "samajshastra-ch03-parivartan.html",
        "badge": "🔄 अध्याय 3/7 — समाजशास्त्र",
        "h1": "समकालीन भारतीय समाज में परिवर्तन",
        "sub": "संस्कृतीकरण, पश्चिमीकरण, आधुनिकीकरण, लौकिकीकरण, नगरीकरण एवं वैश्वीकरण — परिवर्तन की छह प्रमुख प्रक्रियाएं | RAS Pre + Mains",
        "page_title": "अध्याय 3: समकालीन भारतीय समाज में परिवर्तन — समाजशास्त्र | Omkar Sir",
        "desc": "समकालीन भारतीय समाज में परिवर्तन — संस्कृतीकरण (Srinivas), पश्चिमीकरण, आधुनिकीकरण (Yogendra Singh), लौकिकीकरण, नगरीकरण एवं वैश्वीकरण की प्रक्रियाएं व प्रभाव।",
        "prev_link": "samajshastra-ch02-jati-varg.html",
        "prev_label": "← अध्याय 2: जाति एवं वर्ग की अवधारणा",
        "next_link": "samajshastra-ch04-samajik-pranali.html",
        "next_label": "अध्याय 4: भारतीय सामाजिक प्रणाली की अवधारणाएँ →",
    },
    {
        "src_idx": 3,
        "out_file": "samajshastra-ch04-samajik-pranali.html",
        "badge": "🕉️ अध्याय 4/7 — समाजशास्त्र",
        "h1": "भारतीय सामाजिक प्रणाली की अवधारणाएँ",
        "sub": "धर्म, कर्म, पुरुषार्थ एवं आश्रम व्यवस्था — भारतीय सामाजिक व्यवस्था से संबंधित अवधारणाएं | RAS Pre + Mains",
        "page_title": "अध्याय 4: भारतीय सामाजिक प्रणाली की अवधारणाएँ — समाजशास्त्र | Omkar Sir",
        "desc": "भारतीय सामाजिक प्रणाली की अवधारणाएँ — धर्म (लक्षण, प्रकार), कर्म का सिद्धांत, पुनर्जन्म, 16 संस्कार, पुरुषार्थ (धर्म, अर्थ, काम, मोक्ष), आश्रम व्यवस्था एवं ऋण।",
        "prev_link": "samajshastra-ch03-parivartan.html",
        "prev_label": "← अध्याय 3: समकालीन समाज में परिवर्तन",
        "next_link": "samajshastra-ch05-parivar-vivah.html",
        "next_label": "अध्याय 5: परिवार, विवाह, वृद्धजन एवं सोशल मीडिया →",
    },
    {
        "src_idx": 4,
        "out_file": "samajshastra-ch05-parivar-vivah.html",
        "badge": "👨‍👩‍👧‍👦 अध्याय 5/7 — समाजशास्त्र",
        "h1": "परिवार, विवाह, वृद्धजन, दिव्यांगजन एवं सोशल मीडिया",
        "sub": "वर्तमान भारतीय समाज में परिवार एवं विवाह, वृद्धजनों व दिव्यांगजनों के मुद्दे, तथा साइबर अपराध व सोशल मीडिया का प्रभाव | RAS Pre + Mains",
        "page_title": "अध्याय 5: परिवार, विवाह, वृद्धजन, दिव्यांगजन एवं साइबर-सोशल मीडिया — समाजशास्त्र | Omkar Sir",
        "desc": "परिवार व विवाह के बदलते स्वरूप, समकालीन मुद्दे, वृद्धजनों व दिव्यांगजनों की समस्याएं एवं नीतियां, साइबर अपराध व सोशल मीडिया का भारतीय समाज पर प्रभाव।",
        "prev_link": "samajshastra-ch04-samajik-pranali.html",
        "prev_label": "← अध्याय 4: भारतीय सामाजिक प्रणाली",
        "next_link": "samajshastra-ch06-chunautiyan.html",
        "next_label": "अध्याय 6: भारतीय समाज की चुनौतियाँ →",
    },
    {
        "src_idx": 5,
        "out_file": "samajshastra-ch06-chunautiyan.html",
        "badge": "⚠️ अध्याय 6/7 — समाजशास्त्र",
        "h1": "भारतीय समाज के समक्ष चुनौतियाँ एवं सामाजिक समस्याएं",
        "sub": "दहेज, तलाक, भ्रष्टाचार, गरीबी, वेश्यावृत्ति, बेरोजगारी एवं नशाखोरी — भारतीय समाज के समक्ष प्रमुख चुनौतियां | RAS Pre + Mains",
        "page_title": "अध्याय 6: भारतीय समाज के समक्ष चुनौतियाँ एवं सामाजिक समस्याएं — समाजशास्त्र | Omkar Sir",
        "desc": "भारतीय समाज के समक्ष 7 प्रमुख चुनौतियां — दहेज, तलाक, भ्रष्टाचार, गरीबी, वेश्यावृत्ति, बेरोजगारी व नशाखोरी — सिद्धांत, कानून, सरकारी योजनाएं व राजस्थान संदर्भ।",
        "prev_link": "samajshastra-ch05-parivar-vivah.html",
        "prev_label": "← अध्याय 5: परिवार, विवाह एवं सोशल मीडिया",
        "next_link": "samajshastra-ch07-kamzor-varg.html",
        "next_label": "अध्याय 7: कमज़ोर वर्गों की समस्याएं (राजस्थान विशेष) →",
    },
    {
        "src_idx": 6,
        "out_file": "samajshastra-ch07-kamzor-varg.html",
        "badge": "🤝 अध्याय 7/7 — समाजशास्त्र",
        "h1": "भारतीय समाज के कमज़ोर वर्गों की समस्याएं (राजस्थान विशेष)",
        "sub": "महिलाएं, हाशिए के समूह, दलित, अनुसूचित जाति एवं अनुसूचित जनजाति — राजस्थान विशेष संदर्भ एवं कल्याणकारी योजनाएं | RAS Pre + Mains",
        "page_title": "अध्याय 7: भारतीय समाज के कमज़ोर वर्गों की समस्याएं (राजस्थान विशेष) — समाजशास्त्र | Omkar Sir",
        "desc": "कमज़ोर वर्गों की समस्याएं — महिलाएं, हाशिए के समूह (OBC, अल्पसंख्यक, दिव्यांग), दलित/SC, ST — राजस्थान की कुप्रथाएं, संवैधानिक सुरक्षा एवं राज्य-स्तरीय कल्याणकारी योजनाएं।",
        "prev_link": "samajshastra-ch06-chunautiyan.html",
        "prev_label": "← अध्याय 6: भारतीय समाज की चुनौतियाँ",
        "next_link": "samajshastra.html",
        "next_label": "📚 मुख्य पृष्ठ पर वापस →",
    },
]

CSS_TEMPLATE = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Hind',sans-serif;background:#F8F9FA;color:#1A1A2E;line-height:1.7}
h1,h2,h3{font-family:'Poppins',sans-serif}
.tri{height:4px;background:linear-gradient(90deg,#FF6B00 33%,#fff 33% 66%,#00A651 66%)}
.ch-hero{background:linear-gradient(135deg,#FFF8F2,#FFFDF0);padding:38px 6% 30px;border-bottom:1px solid #FFE0C0;text-align:center}
.ch-badge{display:inline-block;background:#FFF3E8;border:1px solid #FFD0A0;color:#FF6B00;padding:5px 16px;border-radius:50px;font-size:12px;font-weight:700;margin-bottom:12px}
.ch-hero h1{font-size:clamp(22px,3.6vw,32px);font-weight:800;margin-bottom:6px}
.ch-hero .ch-sub{color:#888;font-size:13.5px}
.ch-wrap{max-width:840px;margin:0 auto;padding:34px 6% 20px}
.toc-box{background:#fff;border:2px solid #FFE0C0;border-radius:14px;padding:18px 22px;margin-bottom:30px}
.toc-title{font-family:'Poppins',sans-serif;font-weight:800;color:#FF6B00;font-size:15px;margin-bottom:10px}
.toc-list{padding-left:22px;font-size:13.5px;color:#444}
.toc-list li{margin-bottom:6px}
.ch-h2{font-size:19px;font-weight:800;margin:32px 0 14px;color:#1A1A2E;display:flex;align-items:center;gap:10px;border-bottom:2px solid #FFE0C0;padding-bottom:8px}
.ch-h2-num{background:#FF6B00;color:#fff;min-width:28px;height:28px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:12.5px;flex-shrink:0;font-family:'Poppins',sans-serif;font-weight:700}
.ch-h3{font-size:15.5px;font-weight:700;margin:20px 0 8px;color:#1B2A6B}
p{font-size:14.5px;color:#333;margin-bottom:12px}
.ch-list{margin:0 0 14px 0;padding-left:22px}
.ch-list li{font-size:14.5px;color:#333;margin-bottom:6px}
.ch-quote{background:#FFF3E8;border-left:4px solid #FF6B00;padding:14px 18px;margin:16px 0;font-size:14px;color:#444;border-radius:0 10px 10px 0}
.ch-quote p{margin-bottom:6px}
.ch-quote p:last-child{margin-bottom:0}
.profile-box{background:#F3F5FF;border:1.5px solid #DCE1FF;border-radius:12px;padding:14px 18px;margin:16px 0}
.site-box{background:#FFF8F2;border:1.5px solid #FFD9B3;border-radius:12px;padding:14px 18px;margin:16px 0}
.site-title{font-weight:800;color:#B45300;font-size:14.5px;margin-bottom:8px}
.profile-title{font-weight:800;color:#1B2A6B;font-size:14.5px;margin-bottom:8px}
.tip-box{background:#FFFBEA;border:1.5px solid #FFE58F;border-radius:12px;padding:14px 18px;margin:16px 0}
.tip-title{font-weight:800;color:#AD8B00;font-size:14.5px;margin-bottom:8px}
.angle-box{background:#E8F5E9;border:1.5px solid #A5D6A7;border-radius:12px;padding:14px 18px;margin:16px 0}
.angle-title{font-weight:800;color:#2E7D32;font-size:14.5px;margin-bottom:8px}
.warn-box{background:#FFF0F0;border:1.5px solid #FFB3B3;border-radius:12px;padding:14px 18px;margin:16px 0;font-size:13.5px;color:#991B1B}
.warn-box p{color:#991B1B;margin-bottom:6px}
.warn-box p:last-child{margin-bottom:0}
.example-box{background:#F0FBF6;border:1.5px solid #A7E8C8;border-radius:12px;padding:14px 18px;margin:16px 0}
.example-title{font-weight:800;color:#0F7B4E;font-size:14.5px;margin-bottom:8px}
.twocol-box{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:18px 0}
.twocol-col{background:#F8F9FC;border:1.5px solid #E8EAF0;border-radius:12px;padding:14px 16px}
.twocol-col p{margin-bottom:6px;font-size:13.5px}
.twocol-col p:last-child{margin-bottom:0}
@media (max-width:640px){.twocol-box{grid-template-columns:1fr}}
.tbl-wrap{overflow-x:auto;margin:18px 0;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.ch-table{width:100%;border-collapse:collapse;font-size:13.5px;background:#fff}
.ch-table th{background:#1B2A6B;color:#fff;padding:10px 14px;text-align:left;font-weight:700}
.ch-table td{padding:9px 13px;border-bottom:1px solid #F0F0F0;vertical-align:top}
.ch-table tr:nth-child(even) td{background:#FAFAFC}
.ch-nav{display:flex;justify-content:space-between;gap:12px;max-width:840px;margin:20px auto 40px;padding:0 6%;flex-wrap:wrap}
.ch-nav-btn{flex:1;min-width:200px;text-align:center;padding:13px 18px;background:#fff;border:2px solid #E8EAF0;border-radius:12px;text-decoration:none;color:#1A1A2E;font-weight:600;font-size:13.5px;transition:all .2s}
.ch-nav-btn:hover{border-color:#FF6B00;color:#FF6B00}
.ch-nav-next{text-align:right}
footer{background:#1A1A2E;padding:32px 6%;text-align:center;color:#aaa;font-size:13px}
.footer-logo{font-family:'Poppins',sans-serif;font-size:20px;font-weight:800;color:white;margin-bottom:6px}
.footer-logo span{color:#FF6B00}
footer a{color:#FF6B00;text-decoration:none;margin:0 8px}
.ch-ad-wrap{margin:34px 0}
.ch-ad-label{font-size:11px;font-weight:700;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;text-align:center}
.c-card{background:white;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06);transition:all .25s ease;display:flex;flex-direction:column;text-decoration:none;color:inherit;border:1px solid #E8EAF0;position:relative;cursor:default;max-width:480px;margin:0 auto}
.c-card:hover{transform:translateY(-5px);box-shadow:0 14px 30px rgba(0,0,0,.1)}
.c-badge{position:absolute;top:12px;right:12px;padding:4px 12px;border-radius:20px;font-size:.68rem;font-weight:700;letter-spacing:.3px;text-transform:uppercase;z-index:2}
.c-badge-hot{background:linear-gradient(135deg,#ff6f00,#ffca28);color:white}
.c-card-head{padding:22px 18px 14px;background:linear-gradient(135deg,#1B2A6B,#2b3f9e);color:white;min-height:82px;display:flex;align-items:center;gap:10px}
.c-card-head.head-ras{background:linear-gradient(135deg,#4a148c,#6a1b9a)}
.c-card-head.head-gk{background:linear-gradient(135deg,#0d47a1,#1565c0)}
.c-icon{font-size:1.6rem;flex-shrink:0}
.c-title{font-size:.92rem;font-weight:700;color:white;margin:0;line-height:1.35;font-family:'Poppins',sans-serif}
.c-body{padding:10px 18px 0}
.c-tags{display:flex;flex-wrap:wrap;gap:5px}
.c-tag{background:#f0f2f8;color:#555;padding:3px 9px;border-radius:20px;font-size:.68rem;font-weight:600}
.c-foot{padding:12px 18px 16px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.c-price-wrap{display:flex;flex-direction:column}
.c-price{font-size:1.05rem;font-weight:800;color:#e53935}
.c-orig{font-size:.72rem;color:#aaa;text-decoration:line-through}
.c-arrow{font-size:.72rem;font-weight:700;color:#fff;background:#FF6B00;padding:7px 14px;border-radius:20px;text-decoration:none;white-space:nowrap}
.c-arrow:hover{background:#E05500}
"""

AD_RAS = """<div class="ch-ad-wrap">
  <div class="ch-ad-label">📢 विज्ञापन</div>
  <div class="c-card" data-category="ras">
    <span class="c-badge c-badge-hot">🔥 सबसे लोकप्रिय</span>
    <div class="c-card-head head-ras"><div class="c-icon">📘</div><h3 class="c-title">RAS Foundation Course 2026 🕉️</h3></div>
    <div class="c-body"><div class="c-tags"><span class="c-tag">Multiple Validity</span><span class="c-tag">Tests</span></div></div>
    <div class="c-foot"><div class="c-price-wrap"><span class="c-price">₹4,999</span><span class="c-orig">₹25,000</span></div><a href="https://play.google.com/store/apps/details?id=co.april2019.techa" class="c-arrow">Join Now →</a></div>
  </div>
</div>"""

AD_GK = """<div class="ch-ad-wrap">
  <div class="ch-ad-label">📢 विज्ञापन</div>
  <div class="c-card" data-category="gk">
    <div class="c-card-head head-gk"><div class="c-icon">📦</div><h3 class="c-title">ALL IN ONE Subscription — सम्पूर्ण GK एक ही स्थान पर</h3></div>
    <div class="c-body"><div class="c-tags"><span class="c-tag">Multiple Validity</span><span class="c-tag">Tests</span></div></div>
    <div class="c-foot"><div class="c-price-wrap"><span class="c-price">₹899</span><span class="c-orig">₹4,999</span></div><a href="https://play.google.com/store/apps/details?id=co.april2019.techa" class="c-arrow">Join Now →</a></div>
  </div>
</div>"""

# Build each of the 7 chapter files
for cfg in CHAPTER_CONFIGS:
    src_idx = cfg["src_idx"]
    out_file = cfg["out_file"]
    badge = cfg["badge"]
    h1 = cfg["h1"]
    sub = cfg["sub"]
    page_title = cfg["page_title"]
    desc = cfg["desc"]
    prev_link = cfg["prev_link"]
    prev_label = cfg["prev_label"]
    next_link = cfg["next_link"]
    next_label = cfg["next_label"]

    ch_start = ch_offsets[src_idx]
    ch_end = ch_offsets[src_idx + 1]
    ch_raw = text[ch_start:ch_end]

    parser = DocParser()
    parser.feed(ch_raw)

    body_blocks = []
    # Identify headings to plan ad insertion points
    total_children = len(parser.root.children)
    ad1_pos = int(total_children * 0.30)
    ad2_pos = int(total_children * 0.70)
    ad1_inserted = False
    ad2_inserted = False

    for idx, child in enumerate(parser.root.children):
        if not ad1_inserted and idx >= ad1_pos:
            body_blocks.append(AD_RAS)
            ad1_inserted = True
        if not ad2_inserted and idx >= ad2_pos:
            body_blocks.append(AD_GK)
            ad2_inserted = True

        if isinstance(child, Node):
            if child.tag == 'table':
                rows = get_table_rows(child)
                if not rows:
                    continue
                # Skip chapter title header table
                tbl_text = child.get_text().strip()
                if f"अध्याय {src_idx}" in tbl_text and ("पेपर-I" in tbl_text or "स्वरूप" in tbl_text or "प्रक्रियाएं" in tbl_text or "अवधारणाएं" in tbl_text or "प्रभाव" in tbl_text or "चुनौतियां" in tbl_text or "योजनाएं" in tbl_text or idx < 3):
                    continue

                # 1x1 Callout table
                if len(rows) == 1 and len(get_row_cells(rows[0])) == 1:
                    cell = get_row_cells(rows[0])[0]
                    cell_text = cell.get_text().strip()
                    if not cell_text or cell_text == '&nbsp;':
                        continue
                    if '📖 प्रस्तावना' in cell_text or cell_text.startswith('📖') or 'प्रस्तावना' in cell_text[:20]:
                        paras = [p for p in cell.children if isinstance(p, Node) and p.tag == 'p']
                        p_htmls = [p.render_inline() for p in paras if p.get_text().strip() and not 'प्रस्तावना' in p.get_text()]
                        if not p_htmls:
                            clean_t = re.sub(r'^[📖\s]*प्रस्तावना[\s—]*', '', cell.render_inline()).strip()
                            p_htmls = [clean_t]
                        content = ''.join(f'<p>{p}</p>' for p in p_htmls)
                        body_blocks.append(f'<div class="site-box"><div class="site-title">📖 प्रस्तावना</div>{content}</div>')
                    elif '📑 विषय-सूची' in cell_text or 'विषय-सूची' in cell_text[:20]:
                        paras = [p for p in cell.children if isinstance(p, Node) and p.tag == 'p']
                        items = []
                        for p in paras:
                            ptxt = p.get_text().strip()
                            if ptxt and not 'विषय-सूची' in ptxt:
                                it_clean = re.sub(r'^\d{1,2}\.\s*', '', ptxt)
                                items.append(it_clean)
                        if items:
                            body_blocks.append('<div class="toc-box"><div class="toc-title">📋 इस अध्याय में (विषय-सूची)</div><ol class="toc-list">' + ''.join(f'<li>{it}</li>' for it in items) + '</ol></div>')
                    elif '💡 आसान भाषा में समझें' in cell_text:
                        # Extract title line
                        first_line = cell_text.splitlines()[0] if '\n' in cell_text else cell_text[:70]
                        first_line = re.sub(r'<[^>]+>', '', first_line).strip()
                        body_paras = render_cell_paragraphs(cell)
                        body_blocks.append(f'<div class="tip-box"><div class="tip-title">💡 आसान भाषा में समझें</div>{body_paras}</div>')
                    elif cell_text.startswith('💬') or '💬' in cell_text[:10]:
                        body_paras = render_cell_paragraphs(cell)
                        body_blocks.append(f'<div class="ch-quote">{body_paras}</div>')
                    elif '⚠️' in cell_text[:20]:
                        body_paras = render_cell_paragraphs(cell)
                        body_blocks.append(f'<div class="warn-box">{body_paras}</div>')
                    elif '✅' in cell_text[:20]:
                        body_paras = render_cell_paragraphs(cell)
                        body_blocks.append(f'<div class="example-box"><div class="example-title">✅ उदाहरण / केस स्टडी / प्रमाण</div>{body_paras}</div>')
                    else:
                        body_paras = render_cell_paragraphs(cell)
                        body_blocks.append(f'<div class="profile-box">{body_paras}</div>')
                elif len(rows) == 1 and len(get_row_cells(rows[0])) == 2:
                    # 2-col side by side card
                    cells = get_row_cells(rows[0])
                    c1_html = render_cell_paragraphs(cells[0])
                    c2_html = render_cell_paragraphs(cells[1])
                    body_blocks.append(f'<div class="twocol-box"><div class="twocol-col">{c1_html}</div><div class="twocol-col">{c2_html}</div></div>')
                else:
                    # Multi-row or multi-col data table
                    tbl_html = ['<div class="tbl-wrap"><table class="ch-table">']
                    # Treat first row as header if it has headers or bold
                    for r_idx, r in enumerate(rows):
                        cells = get_row_cells(r)
                        if r_idx == 0:
                            tbl_html.append('<thead><tr>')
                            for c in cells:
                                c_txt = c.render_inline().strip()
                                tbl_html.append(f'<th>{c_txt}</th>')
                            tbl_html.append('</tr></thead><tbody>')
                        else:
                            tbl_html.append('<tr>')
                            for c in cells:
                                c_txt = c.render_inline().strip()
                                tbl_html.append(f'<td>{c_txt}</td>')
                            tbl_html.append('</tr>')
                    tbl_html.append('</tbody></table></div>')
                    body_blocks.append(''.join(tbl_html))

            elif child.tag == 'p':
                ptxt = child.get_text().strip()
                if not ptxt or ptxt == '&nbsp;':
                    continue
                if 'WWW.OMKARSIR.COM' in ptxt or 'PAGE-' in ptxt or ptxt == 'समाजशास्त्र SOCIOLOGY':
                    continue
                # Major section heading: 01. ...
                m = re.match(r'^(\d{2})\.\s+(.*)$', ptxt)
                if m:
                    sec_num = int(m.group(1))
                    sec_title = m.group(2)
                    body_blocks.append(f'<h2 class="ch-h2"><span class="ch-h2-num">{sec_num}</span><span class="ch-h2-text">{sec_title}</span></h2>')
                elif any(ptxt.startswith(icon) for icon in ['📌', '📖', '🔷', '🔶', '🎯', '📜', '🏛️', '⭐', '🌿', '🔑', '👉', '📍', '💠', '🔺']):
                    body_blocks.append(f'<h3 class="ch-h3">{child.render_inline()}</h3>')
                else:
                    body_blocks.append(f'<p>{child.render_inline()}</p>')

    content_html = '\n'.join(body_blocks)

    full_page = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-adsense-account" content="ca-pub-8493304986550617"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8493304986550617" crossorigin="anonymous"></script>
<title>{page_title}</title>
<meta name="keywords" content="RAS Exam 2026, RAS Mains, State PCS, UPSC IAS, {h1}, समाजशास्त्र, Sociology, Rajasthan GK, Omkar Sir">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://omkarsir.com/{out_file}">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:locale" content="hi_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:url" content="https://omkarsir.com/{out_file}">
<meta name="twitter:image" content="https://omkarsir.com/og-image.png">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="https://omkarsir.com/{out_file}">
<meta name="description" content="{desc}">
<link rel="preload" href="/assets/fonts/hind-400-devanagari.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/nied-fonts.css">
<style>
{CSS_TEMPLATE}
</style>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LearningResource",
  "name": "{page_title}",
  "description": "{desc}",
  "url": "https://omkarsir.com/{out_file}",
  "inLanguage": "hi",
  "isAccessibleForFree": true,
  "educationalLevel": "Competitive Exam Preparation",
  "about": ["RAS Exam 2026", "RAS Mains", "UPSC IAS", "State PCS", "Rajasthan GK", "Sociology", "समाजशास्त्र"],
  "provider": {{"@type": "EducationalOrganization", "name": "New India Education", "url": "https://omkarsir.com"}},
  "author": {{"@type": "Person", "name": "Omkar Singh Gurjar"}}
}}
</script>
<meta name="author" content="Omkar Singh Gurjar">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#1B2A6B">
<meta property="og:site_name" content="Omkar Sir | New India Education">
<meta property="og:image:alt" content="{page_title}">
<style id="nied-navbar-reserve">#nied-navbar{{min-height:72px}}@media(max-width:520px){{#nied-navbar{{min-height:62px}}}}</style>
</head>
<body>
<div id="nied-navbar"></div>
<div class="tri"></div>

<section class="ch-hero">
  <div class="ch-badge">{badge}</div>
  <h1>{h1}</h1>
  <div class="ch-sub">{sub}</div>
</section>

<div class="ch-wrap">
{content_html}
</div>

<div class="ch-nav">
  <a href="{prev_link}" class="ch-nav-btn">{prev_label}</a>
  <a href="{next_link}" class="ch-nav-btn ch-nav-next">{next_label}</a>
</div>

<footer>
  <div class="footer-logo">Omkar Sir<span>.</span></div>
  <div style="font-size:12.5px;margin-bottom:8px">New India Education, Jaipur, Rajasthan</div>
  <div><a href="samajshastra.html">📚 सभी अध्याय</a> <a href="courses.html">Courses</a> <a href="index.html">Home</a></div>
</footer>
<script src="/nied-menu.js" defer></script>
</body>
</html>
"""
    dest_path = os.path.join(WEBSITE_DIR, out_file)
    with open(dest_path, 'w', encoding='utf-8') as out_f:
        out_f.write(full_page)
    print(f"Generated {out_file}: {len(full_page):,} bytes, {len(body_blocks)} blocks.")

# Now update samajshastra.html (Hub page)
hub_file = os.path.join(WEBSITE_DIR, "samajshastra.html")
hub_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-adsense-account" content="ca-pub-8493304986550617"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8493304986550617" crossorigin="anonymous"></script>
<title>समाजशास्त्र (Sociology) — सम्पूर्ण 7 अध्याय | RAS Mains | Omkar Sir</title>
<meta name="keywords" content="RAS Exam 2026, RAS Mains Paper 1, समाजशास्त्र, Sociology, Rajasthan GK, Omkar Sir">
<meta property="og:title" content="समाजशास्त्र (Sociology) — सम्पूर्ण 7 अध्याय | RAS Mains | Omkar Sir">
<meta property="og:description" content="समाजशास्त्र (Sociology) — RAS Mains Paper 1, Unit 3 के लिए सम्पूर्ण 7 अध्यायों में विस्तृत, परीक्षा-उन्मुख हिंदी नोट्स। NCERT, RBSE व प्रामाणिक स्रोतों से तैयार।">
<meta property="og:type" content="website">
<meta property="og:url" content="https://omkarsir.com/samajshastra.html">
<meta property="og:image" content="https://omkarsir.com/og-image.png">
<meta property="og:locale" content="hi_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="समाजशास्त्र (Sociology) — सम्पूर्ण 7 अध्याय | RAS Mains | Omkar Sir">
<meta name="twitter:description" content="समाजशास्त्र (Sociology) — RAS Mains Paper 1, Unit 3 के लिए सम्पूर्ण 7 अध्यायों में विस्तृत, परीक्षा-उन्मुख हिंदी नोट्स।">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="https://omkarsir.com/samajshastra.html">
<meta name="description" content="समाजशास्त्र (Sociology) — RAS Mains Paper 1, Unit 3 के लिए सम्पूर्ण 7 अध्यायों में विस्तृत, परीक्षा-उन्मुख हिंदी नोट्स। NCERT, RBSE व प्रामाणिक स्रोतों से तैयार।">
<link rel="preload" href="/assets/fonts/hind-400-devanagari.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/nied-fonts.css">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Hind',sans-serif;background:#F8F9FA;color:#1A1A2E}}
h1,h2,h3{{font-family:'Poppins',sans-serif}}
.tri{{height:4px;background:linear-gradient(90deg,#FF6B00 33%,#fff 33% 66%,#00A651 66%)}}
.hero{{background:linear-gradient(135deg,#FFF8F2,#FFFDF0);padding:54px 6% 40px;text-align:center;border-bottom:1px solid #FFE0C0}}
.hero-badge{{display:inline-block;background:#FFF3E8;border:1px solid #FFD0A0;color:#FF6B00;padding:6px 18px;border-radius:50px;font-size:12.5px;font-weight:600;margin-bottom:16px}}
.hero h1{{font-size:clamp(24px,4vw,38px);font-weight:800;margin-bottom:10px}}
.hero h1 span{{color:#FF6B00}}
.hero p{{color:#666;font-size:14.5px;max-width:580px;margin:0 auto 8px;line-height:1.6}}
.hero .credibility{{font-size:13px;font-weight:700;color:#1B2A6B;margin-top:10px}}
.idx-wrap{{max-width:900px;margin:0 auto;padding:40px 6% 60px}}
.idx-grid{{display:flex;flex-direction:column;gap:14px}}
.idx-card{{background:#fff;border:2px solid #E8EAF0;border-radius:16px;padding:18px 20px;display:flex;align-items:center;gap:16px;text-decoration:none;color:inherit;transition:all .2s}}
.idx-card:hover{{border-color:#FF6B00;transform:translateX(4px);box-shadow:0 8px 24px rgba(255,107,0,.1)}}
.idx-num{{font-family:'Poppins',sans-serif;font-weight:800;color:#FFD0A0;font-size:26px;width:44px;flex-shrink:0;text-align:center}}
.idx-icon{{font-size:28px;flex-shrink:0}}
.idx-body{{flex:1;min-width:0}}
.idx-body h3{{font-size:15.5px;font-weight:700;margin-bottom:2px}}
.idx-body p{{font-size:12.5px;color:#777}}
.idx-arrow{{color:#FF6B00;font-size:18px;flex-shrink:0}}
footer{{background:#1A1A2E;padding:36px 6%;text-align:center;color:#aaa;font-size:13px}}
.footer-logo{{font-family:'Poppins',sans-serif;font-size:22px;font-weight:800;color:white;margin-bottom:8px}}
.footer-logo span{{color:#FF6B00}}
footer a{{color:#FF6B00;text-decoration:none;margin:0 8px}}
</style>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LearningResource",
  "name": "समाजशास्त्र (Sociology) — सम्पूर्ण 7 अध्याय | RAS Mains Paper 1",
  "description": "समाजशास्त्र (Sociology) — RAS Mains Paper 1, Unit 3 के लिए सम्पूर्ण 7 अध्यायों में विस्तृत, परीक्षा-उन्मुख हिंदी नोट्स।",
  "url": "https://omkarsir.com/samajshastra.html",
  "inLanguage": "hi",
  "isAccessibleForFree": true,
  "educationalLevel": "Competitive Exam Preparation",
  "about": ["RAS Exam 2026", "RAS Mains", "UPSC IAS", "State PCS", "Rajasthan GK", "Sociology", "समाजशास्त्र"],
  "provider": {{"@type": "EducationalOrganization", "name": "New India Education", "url": "https://omkarsir.com"}},
  "author": {{"@type": "Person", "name": "Omkar Singh Gurjar"}}
}}
</script>
<meta name="author" content="Omkar Singh Gurjar">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="theme-color" content="#1B2A6B">
<meta property="og:site_name" content="Omkar Sir | New India Education">
<meta property="og:image:alt" content="समाजशास्त्र (Sociology) | Omkar Sir">
<meta name="twitter:url" content="https://omkarsir.com/samajshastra.html">
<meta name="twitter:image" content="https://omkarsir.com/og-image.png">
<style id="nied-navbar-reserve">#nied-navbar{{min-height:72px}}@media(max-width:520px){{#nied-navbar{{min-height:62px}}}}</style>
</head>
<body>
<div id="nied-navbar"></div>
<div class="tri"></div>

<section class="hero">
  <div class="hero-badge">📚 Complete Series — 7 अध्याय | RAS Mains Paper 1</div>
  <h1>समाजशास्त्र <span>(Sociology)</span></h1>
  <p>जाति एवं वर्ग की अवधारणा, समकालीन भारतीय समाज में परिवर्तन, कर्म-धर्म-पुरुषार्थ, परिवार-विवाह के मुद्दे, समाज की चुनौतियाँ एवं कमज़ोर वर्गों की समस्याएं (राजस्थान विशेष) — RAS Mains के लिए विस्तृत, परीक्षा-उन्मुख अध्ययन सामग्री।</p>
  <div class="credibility">🏆 NCERT, RBSE की मूल पुस्तकों व प्रामाणिक स्रोतों से तैयार — विश्वसनीय एवं बेहतरीन Content</div>
</section>

<div class="idx-wrap">
  <div class="idx-grid">
    <a href="samajshastra-ch01-parichay.html" class="idx-card">
      <div class="idx-num">01</div>
      <div class="idx-icon">🔭</div>
      <div class="idx-body">
        <h3>समाजशास्त्र — परिचय एवं पाठ्यक्रम रूपरेखा</h3>
        <p>Introduction to Sociology, Emergence &amp; Indian Sociological Thought | RAS Mains Unit-3</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch02-jati-varg.html" class="idx-card">
      <div class="idx-num">02</div>
      <div class="idx-icon">🏛️</div>
      <div class="idx-body">
        <h3>जाति एवं वर्ग की अवधारणा</h3>
        <p>Concept of Caste and Class — Theories, Features &amp; Changing Dimensions</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch03-parivartan.html" class="idx-card">
      <div class="idx-num">03</div>
      <div class="idx-icon">🔄</div>
      <div class="idx-body">
        <h3>समकालीन भारतीय समाज में परिवर्तन</h3>
        <p>Processes of Change — Sanskritization, Westernization, Modernization, Secularization &amp; Globalization</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch04-samajik-pranali.html" class="idx-card">
      <div class="idx-num">04</div>
      <div class="idx-icon">🕉️</div>
      <div class="idx-body">
        <h3>भारतीय सामाजिक प्रणाली की अवधारणाएँ</h3>
        <p>Indian Social System Concepts — Dharma, Karma, Purushartha, Ashram, Sanskar &amp; Rin</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch05-parivar-vivah.html" class="idx-card">
      <div class="idx-num">05</div>
      <div class="idx-icon">👨‍👩‍👧‍👦</div>
      <div class="idx-body">
        <h3>परिवार, विवाह, वृद्धजन, दिव्यांगजन एवं सोशल मीडिया</h3>
        <p>Family, Marriage, Elderly, Persons with Disabilities, Cybercrime &amp; Social Media Impact</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch06-chunautiyan.html" class="idx-card">
      <div class="idx-num">06</div>
      <div class="idx-icon">⚠️</div>
      <div class="idx-body">
        <h3>भारतीय समाज के समक्ष चुनौतियाँ एवं सामाजिक समस्याएं</h3>
        <p>Challenges before Indian Society — Dowry, Divorce, Corruption, Poverty, Unemployment, Drug Addiction</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
    <a href="samajshastra-ch07-kamzor-varg.html" class="idx-card">
      <div class="idx-num">07</div>
      <div class="idx-icon">🤝</div>
      <div class="idx-body">
        <h3>भारतीय समाज के कमज़ोर वर्गों की समस्याएं (राजस्थान विशेष)</h3>
        <p>Problems of Weaker Sections — Women, Marginalized, SC, ST &amp; Welfare Schemes in Rajasthan</p>
      </div>
      <span class="idx-arrow">→</span>
    </a>
  </div>
</div>

<footer>
  <div class="footer-logo">Omkar Sir<span>.</span></div>
  <div style="font-size:12.5px;margin-bottom:8px">New India Education, Jaipur, Rajasthan</div>
  <div><a href="courses.html">Courses</a> <a href="all-notes.html">सभी Notes</a> <a href="index.html">Home</a></div>
</footer>
<script src="/nied-menu.js" defer></script>
</body>
</html>
"""
with open(hub_file, 'w', encoding='utf-8') as h_f:
    h_f.write(hub_html)
print(f"Updated hub page {hub_file}: {len(hub_html):,} bytes.")
print("ALL 7 CHAPTERS + HUB PAGE GENERATED SUCCESSFULLY!")
