#!/usr/bin/env python3
"""Generate unified, simple ₹49 landing pages for the 10 India GK PDF subjects
and upgrade their cards in store.html to the uniform ₹49 card layout.
"""
from html import escape as E
import json
import os
import re
from urllib.parse import quote

ROOT = "/Users/omkarsingh/Desktop/omkarsir-website"
WA_NUMBER = "917023166962"

# Put Razorpay links (e.g. "https://rzp.io/rzp/...") in rzp_hi / rzp_en when ready.
# While empty, the Buy button opens a prefilled ₹49 WhatsApp checkout message.
INDIA_GK_PDFS = [
    {
        "slug": "prachin-bharat-itihas-pdf.html",
        "title": "सम्पूर्ण प्राचीन भारत का इतिहास",
        "en_title": "Ancient Indian History",
        "tag": "प्राचीन इतिहास",
        "badge": "🏛️ RAS Pre + Mains",
        "desc": "प्रागैतिहासिक काल, सिंधु सभ्यता, वैदिक संस्कृति, जैन-बौद्ध धर्म, महाजनपद, मौर्य व गुप्त काल का सम्पूर्ण संकलन।",
        "cover": "/assets/store/pdf-cover-prachin-bharat-itihas.svg",
        "sample": "/assets/store/samples/ancient-india-sample-10-pages.pdf",
        "hub": "/prachin-bharat-itihas.html",
        "hi_pages": 136,
        "en_pages": 159,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "प्रागैतिहासिक भारत एवं इतिहास के स्रोत",
            "सिंधु घाटी सभ्यता",
            "वैदिक काल",
            "जैन धर्म एवं बौद्ध धर्म",
            "महाजनपद एवं मगध का उदय",
            "मौर्य साम्राज्य",
            "मौर्योत्तर काल",
            "गुप्त साम्राज्य — स्वर्ण युग",
            "गुप्तोत्तर काल एवं हर्षवर्धन",
            "संगम युग एवं दक्षिण भारत",
        ],
    },
    {
        "slug": "madhyakalin-bharat-itihas-pdf.html",
        "title": "सम्पूर्ण मध्यकालीन भारत का इतिहास",
        "en_title": "Medieval Indian History",
        "tag": "मध्यकालीन इतिहास",
        "badge": "🕌 RAS Pre + Mains",
        "desc": "दिल्ली सल्तनत, मुगल काल, प्रशासन, भक्ति-सूफी आंदोलन, समाज व संस्कृति का परीक्षा-केंद्रित संकलन।",
        "cover": "/assets/store/pdf-cover-madhyakalin-bharat-itihas.svg",
        "sample": "/assets/store/samples/medieval-india-sample-10-pages.pdf",
        "hub": None,
        "hi_pages": 145,
        "en_pages": 169,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "प्रारंभिक मध्यकाल व त्रिपक्षीय संघर्ष",
            "दिल्ली सल्तनत — राजनीतिक व प्रशासनिक व्यवस्था",
            "विजयनगर एवं बहमनी साम्राज्य",
            "भक्ति एवं सूफी आंदोलन",
            "मुगल साम्राज्य — बाबर से औरंगजेब तक",
            "मुगल प्रशासन, मनसबदारी एवं भू-राजस्व",
            "मध्यकालीन कला, स्थापत्य एवं साहित्य",
            "मराठा शक्ति का उदय व क्षेत्रीय राज्य",
        ],
    },
    {
        "slug": "bharatiya-kala-sanskriti-pdf.html",
        "title": "सम्पूर्ण भारतीय कला एवं संस्कृति",
        "en_title": "Indian Art & Culture",
        "tag": "कला एवं संस्कृति",
        "badge": "🎨 RAS Pre + Mains",
        "desc": "स्थापत्य, मंदिर-शैलियाँ, मूर्तिकला, चित्रकला, शास्त्रीय नृत्य-संगीत, साहित्य व दर्शन की स्पष्ट समझ।",
        "cover": "/assets/store/pdf-cover-bharatiya-kala-sanskriti.svg",
        "sample": "/assets/store/samples/indian-art-culture-sample-10-pages.pdf",
        "hub": "/bharatiya-kala-sanskriti.html",
        "hi_pages": 126,
        "en_pages": 156,
        "extra_note": "उत्तर-लेखन व मॉडल उत्तर सामग्री उपलब्ध",
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "प्रागैतिहासिक एवं सिंधु घाटी कला",
            "प्राचीन भारत की कला (वैदिक से गुप्तोत्तर काल)",
            "मध्यकालीन भारत की मंदिर वास्तुकला",
            "सल्तनत एवं मुगल काल की वास्तुकला",
            "प्रदर्शनकारी कला — शास्त्रीय नृत्य, संगीत, रंगमंच",
            "चित्रकला परंपराएँ",
            "साहित्य — वैदिक से क्षेत्रीय भाषाएँ",
            "शिल्प एवं गुफा स्थापत्य कला",
            "प्राचीन व मध्यकालीन धार्मिक आंदोलन व दर्शन",
        ],
    },
    {
        "slug": "bharatiya-rajvyavastha-pdf.html",
        "title": "भारतीय राजव्यवस्था एवं संविधान",
        "en_title": "Indian Polity & Constitution",
        "tag": "राजव्यवस्था व संविधान",
        "badge": "⚖️ 306+ पृष्ठ · Complete",
        "desc": "संविधान निर्माण, मौलिक अधिकार, संसद, न्यायपालिका, संघवाद, स्थानीय स्वशासन व संवैधानिक निकाय एक क्रमबद्ध PDF में।",
        "cover": "/assets/store/pdf-cover-bharatiya-rajvyavastha.svg",
        "sample": "/assets/store/samples/indian-polity-sample-10-pages.pdf",
        "hub": "/samvidhan.html",
        "hi_pages": 306,
        "en_pages": 348,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "संविधान निर्माण, उद्देशिका एवं नागरिकता",
            "मौलिक अधिकार, नीति निदेशक तत्व एवं मूल कर्तव्य",
            "संविधान संशोधन एवं आधारभूत ढाँचा सिद्धांत",
            "संघ कार्यपालिका — राष्ट्रपति, प्रधानमंत्री एवं मंत्रिपरिषद",
            "संघ विधायिका (संसद) एवं संघ न्यायपालिका",
            "संघ-राज्य संबंध एवं आपातकालीन प्रावधान",
            "स्थानीय स्वशासन — पंचायती राज व नगरीय निकाय",
            "निर्वाचन तंत्र एवं संवैधानिक/सांविधिक निकाय",
            "सुशासन — लोकपाल, CVC, CIC व नागरिक चार्टर",
        ],
    },
    {
        "slug": "bharatiya-arthvyavastha-pdf.html",
        "title": "सम्पूर्ण भारतीय अर्थव्यवस्था",
        "en_title": "Indian Economy",
        "tag": "भारतीय अर्थव्यवस्था",
        "badge": "📈 530 पृष्ठ · V2",
        "desc": "आर्थिक विकास, कृषि, उद्योग, LPG सुधार, RBI-बैंकिंग, केंद्रीय बजट व विश्व अर्थव्यवस्था का सम्पूर्ण संकलन।",
        "cover": "/assets/store/pdf-cover-bharatiya-arthvyavastha.svg",
        "sample": "/assets/store/samples/economy-sample-10-pages.pdf",
        "hub": "/arthavyavastha.html",
        "hi_pages": 530,
        "en_pages": 242,
        "extra_note": "उत्तर-लेखन व मॉडल उत्तर सामग्री उपलब्ध",
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "आर्थिक विकास एवं मापन",
            "कृषि: विकास, सुधार एवं नीतियाँ",
            "उद्योग: नीति, LPG सुधार एवं MSME",
            "सेवा क्षेत्र एवं आधारभूत संरचना",
            "अंतर्राष्ट्रीय व्यापार एवं भुगतान संतुलन",
            "सार्वजनिक वित्त, केंद्रीय बजट एवं राजकोषीय नीति",
            "भारतीय रिजर्व बैंक, मौद्रिक नीति व बैंकिंग सुधार",
            "गरीबी, बेरोज़गारी, स्वास्थ्य एवं शिक्षा योजनाएँ",
            "विश्व अर्थव्यवस्था — WTO, विश्व बैंक एवं IMF",
        ],
    },
    {
        "slug": "vishwa-bhugol-pdf.html",
        "title": "सम्पूर्ण विश्व भूगोल",
        "en_title": "World Geography",
        "tag": "विश्व भूगोल",
        "badge": "🌐 RAS Prelims",
        "desc": "पर्वत, पठार, मरुस्थल, प्रमुख नदियाँ-झीलें, प्राकृतिक वनस्पति, कृषि, औद्योगिक प्रदेश व पर्यावरणीय मुद्दे।",
        "cover": "/assets/store/pdf-cover-vishwa-bhugol.svg",
        "sample": "/assets/store/samples/world-geography-sample-10-pages.pdf",
        "hub": "/vishwa-bhugol.html",
        "hi_pages": 84,
        "en_pages": 95,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "विश्व के भौतिक स्वरूप (पर्वत, पठार, मैदान, मरुस्थल)",
            "विश्व की प्रमुख नदियाँ एवं झीलें",
            "विश्व की प्राकृतिक वनस्पति एवं बायोम",
            "विश्व कृषि प्रणालियाँ एवं फसलें",
            "विश्व के प्रमुख औद्योगिक प्रदेश एवं उद्योग",
            "प्रमुख अंतर्राष्ट्रीय परिवहन नेटवर्क",
            "वैश्विक पर्यावरणीय मुद्दे एवं सम्मेलन",
        ],
    },
    {
        "slug": "jiv-vigyan-biology-pdf.html",
        "title": "सम्पूर्ण जीव विज्ञान",
        "en_title": "Biology",
        "tag": "जीव विज्ञान",
        "badge": "🧬 293 पृष्ठ · Complete",
        "desc": "कोशिका, पादप व मानव शरीर तंत्र, रोग-प्रतिरक्षा, आनुवंशिकी, जैव प्रौद्योगिकी, CRISPR व पारिस्थितिकी।",
        "cover": "/assets/store/pdf-cover-jiv-vigyan-biology.svg",
        "sample": "/assets/store/samples/biology-sample-10-pages.pdf",
        "hub": "/jiv-vigyan.html",
        "hi_pages": 293,
        "en_pages": 322,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "कोशिका संरचना एवं कार्य",
            "पादप आकारिकी, पोषण, वृद्धि नियामक व जनन",
            "मानव क्रिया विज्ञान (पाचन, श्वसन, परिसंचरण, तंत्रिका तंत्र)",
            "आहार, पोषण, प्रतिरक्षा तंत्र एवं मानव रोग",
            "सूक्ष्मजीव, किण्वन एवं जैव-प्रौद्योगिकी",
            "GMO, टीके, CRISPR एवं mRNA तकनीक",
            "जैव-विविधता, संरक्षण एवं पारिस्थितिकीय संतुलन",
            "राजस्थान संदर्भ में कृषि, उद्यान, वानिकी व पशुपालन",
        ],
    },
    {
        "slug": "bhautik-vigyan-physics-pdf.html",
        "title": "सम्पूर्ण भौतिक विज्ञान",
        "en_title": "Physics",
        "tag": "भौतिक विज्ञान",
        "badge": "⚛️ RAS Pre + Mains",
        "desc": "दैनिक जीवन में भौतिकी, गति, ऊर्जा, गुरुत्वाकर्षण, प्रकाश, ऊष्मा, विद्युत, चुम्बकत्व व नाभिकीय विज्ञान।",
        "cover": "/assets/store/pdf-cover-bhautik-vigyan-physics.svg",
        "sample": "/assets/store/samples/physics-sample-10-pages.pdf",
        "hub": "/bhautik-vigyan.html",
        "hi_pages": 130,
        "en_pages": 144,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "रोज़मर्रा जीवन में भौतिकी",
            "गति, बल, कार्य, शक्ति एवं ऊर्जा",
            "गुरुत्वाकर्षण एवं उपग्रह गति",
            "प्रकाश एवं इसके गुणधर्म (लेंस, दर्पण, वर्ण विक्षेपण)",
            "ऊष्मा एवं ऊष्मागतिकी",
            "स्थिर वैद्युतिकी, धारा विद्युत एवं चुंबकत्व",
            "ध्वनि एवं विद्युत-चुंबकीय तरंगें",
            "चिकित्सा निदान एवं नाभिकीय विखंडन-संलयन",
        ],
    },
    {
        "slug": "rasayan-vigyan-chemistry-pdf.html",
        "title": "सम्पूर्ण रसायन विज्ञान",
        "en_title": "Chemistry",
        "tag": "रसायन विज्ञान",
        "badge": "🧪 RAS Pre + Mains",
        "desc": "परमाणु संरचना, धातु-अधातु, अम्ल-क्षार-pH, औषधियाँ, कार्बन यौगिक, ईंधन, रेडियोधर्मिता व हरित रसायन।",
        "cover": "/assets/store/pdf-cover-rasayan-vigyan-chemistry.svg",
        "sample": "/assets/store/samples/chemistry-sample-10-pages.pdf",
        "hub": "/rasayan-vigyan.html",
        "hi_pages": 151,
        "en_pages": 166,
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "दैनिक जीवन में रसायन",
            "परमाणु संरचना एवं रासायनिक बंध",
            "धातु, अधातु, उपधातु, अयस्क एवं मिश्रधातु",
            "अम्ल, क्षार, लवण, pH एवं बफर",
            "औषधियाँ, परिरक्षक, कीटनाशक एवं उर्वरक",
            "कार्बन एवं इसके यौगिक, बहुलक",
            "ईंधन, ऑक्टेन रेटिंग, रेडियोधर्मिता व हरित रसायन",
        ],
    },
    {
        "slug": "praudyogiki-technology-pdf.html",
        "title": "सम्पूर्ण विज्ञान एवं प्रौद्योगिकी",
        "en_title": "Science & Technology",
        "tag": "विज्ञान एवं प्रौद्योगिकी",
        "badge": "🚀 RAS Pre + Mains",
        "desc": "AI-ML, साइबर सुरक्षा, रोबोटिक्स, नैनो-क्वांटम टेक, ISRO अंतरिक्ष व रक्षा मिसाइल कार्यक्रम एक जगह।",
        "cover": "/assets/store/pdf-cover-praudyogiki-technology.svg",
        "sample": "/assets/store/samples/technology-sample-10-pages.pdf",
        "hub": "/vigyan-praudyogiki.html",
        "hi_pages": 164,
        "en_pages": 185,
        "extra_note": "उत्तर-लेखन व मॉडल उत्तर सामग्री उपलब्ध",
        "price": 49,
        "mrp": 199,
        "rzp_hi": "",
        "rzp_en": "",
        "topics": [
            "कंप्यूटर विज्ञान, नेटवर्किंग एवं दूरसंचार",
            "इंटरनेट एवं सूचना-संचार प्रौद्योगिकी (ICT)",
            "AI-ML, Big Data, IoT, Blockchain व साइबर सुरक्षा",
            "रोबोटिक्स, नैनोटेक्नोलॉजी एवं क्वांटम कंप्यूटिंग",
            "जैव प्रौद्योगिकी एवं आनुवंशिक अभियांत्रिकी",
            "भारतीय अंतरिक्ष कार्यक्रम (ISRO मिशन)",
            "रक्षा प्रौद्योगिकी एवं भारतीय मिसाइल कार्यक्रम",
            "डिजिटल इंडिया, S&T नीतियाँ व प्रमुख वैज्ञानिक संस्थान",
        ],
    },
]


def wa_link(item, edition_label):
    msg = (
        f"नमस्ते Omkar Sir, मुझे {item['title']} ({item['en_title']}) की "
        f"{edition_label} PDF (₹{item['price']}) खरीदनी है। कृपया पेमेंट/डाउनलोड लिंक भेजें।"
    )
    return f"https://wa.me/{WA_NUMBER}?text={quote(msg)}"


def seo_graph(item):
    url = f"https://omkarsir.com/{item['slug']}"
    name = f"{item['title']} PDF | Omkar Sir"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": ["EducationalOrganization", "Organization"],
                    "@id": "https://omkarsir.com/#organization",
                    "name": "New India Education",
                    "alternateName": ["NIEOM Academy", "NIEOM", "NIEd", "Omkar Sir"],
                    "url": "https://omkarsir.com/",
                    "logo": {
                        "@type": "ImageObject",
                        "url": "https://omkarsir.com/favicon-512.png",
                        "width": 512,
                        "height": 512,
                    },
                    "image": "https://omkarsir.com/og-image.png",
                    "email": "email2omkara@gmail.com",
                    "telephone": "+91-7023166962",
                },
                {
                    "@type": "WebSite",
                    "@id": "https://omkarsir.com/#website",
                    "url": "https://omkarsir.com/",
                    "name": "Omkar Sir",
                    "inLanguage": "hi",
                    "publisher": {"@id": "https://omkarsir.com/#organization"},
                },
                {
                    "@type": "WebPage",
                    "@id": f"{url}#webpage",
                    "url": url,
                    "name": name,
                    "description": item["desc"],
                    "inLanguage": "hi",
                    "isPartOf": {"@id": "https://omkarsir.com/#website"},
                },
            ],
        },
        ensure_ascii=False,
    )


def product_ld(item):
    url = f"https://omkarsir.com/{item['slug']}"
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": f"{item['title']} ({item['en_title']}) PDF",
            "description": item["desc"],
            "image": f"https://omkarsir.com{item['cover']}",
            "url": url,
            "brand": {"@type": "Organization", "name": "New India Education"},
            "offers": {
                "@type": "Offer",
                "price": str(item["price"]),
                "priceCurrency": "INR",
                "availability": "https://schema.org/InStock",
                "url": url,
            },
        },
        ensure_ascii=False,
    )


def render_page(item):
    url = f"https://omkarsir.com/{item['slug']}"
    page_title = f"{item['title']} PDF (₹{item['price']}) | Omkar Sir"
    off_pct = round((item["mrp"] - item["price"]) * 100 / item["mrp"])
    wa_hi = wa_link(item, "हिंदी")
    wa_en = wa_link(item, "English")
    buy_hi = item["rzp_hi"] or wa_hi
    buy_en = item["rzp_en"] or wa_en

    hub_hero_link = (
        f'<a href="{E(item["hub"])}">📖 मुफ़्त ऑनलाइन अध्याय पढ़ें →</a>'
        if item["hub"]
        else ""
    )
    hub_sample_btn = (
        f'<a class="btn-outline" href="{E(item["hub"])}">मुफ़्त ऑनलाइन नोट्स देखें</a>'
        if item["hub"]
        else ""
    )
    hub_footer_link = (
        f'<a href="{E(item["hub"])}">मुफ़्त नोट्स</a>' if item["hub"] else ""
    )
    topics_li = "\n            ".join(f"<li>{E(t)}</li>" for t in item["topics"])

    return f"""<!doctype html>
<html lang="hi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{E(page_title)}</title>
  <meta name="description" content="{E(item['desc'])} हिंदी ({item['hi_pages']} पृष्ठ) व English ({item['en_pages']} पृष्ठ) संस्करण सिर्फ़ ₹{item['price']} में।">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <meta name="author" content="Omkar Singh Gurjar">
  <meta name="theme-color" content="#1B2A6B">
  <link rel="canonical" href="{E(url)}">
  <meta property="og:type" content="product">
  <meta property="og:site_name" content="Omkar Sir | New India Education">
  <meta property="og:locale" content="hi_IN">
  <meta property="og:title" content="{E(page_title)}">
  <meta property="og:description" content="{E(item['desc'])}">
  <meta property="og:url" content="{E(url)}">
  <meta property="og:image" content="https://omkarsir.com/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{E(page_title)}">
  <meta name="twitter:description" content="{E(item['desc'])}">
  <meta name="twitter:image" content="https://omkarsir.com/og-image.png">
  <link rel="stylesheet" href="/assets/fonts/nied-fonts.css">
  <link rel="stylesheet" href="/assets/css/pdf-store-page.css">
  <style id="nied-navbar-reserve">#nied-navbar{{min-height:72px}}@media(max-width:520px){{#nied-navbar{{min-height:62px}}}}</style>
  <script type="application/ld+json">{product_ld(item)}</script>
  <script type="application/ld+json" id="seo-graph">{seo_graph(item)}</script>
</head>
<body>
  <div id="nied-navbar"></div>

  <main>
    <section class="hero">
      <div class="wrap">
        <nav class="crumb" aria-label="Breadcrumb">
          <a href="/">होम</a> › <a href="/store.html">PDF Store</a> › <span>{E(item['tag'])}</span>
        </nav>

        <div class="hero-grid">
          <div>
            <span class="pill">🇮🇳 भारत GK · {E(item['badge'])}</span>
            <h1>{E(item['title'])}<span>{E(item['en_title'])}</span></h1>
            <p class="lead">{E(item['desc'])}</p>
            <ul class="specs">
              <li>📘 हिंदी: {item['hi_pages']} पृष्ठ</li>
              <li>📗 English: {item['en_pages']} पृष्ठ</li>
              <li>📱 Mobile &amp; Print Ready</li>
            </ul>
            <div class="hero-links">
              <a href="{E(item['sample'])}" target="_blank" rel="noopener">📄 10-Page Free Sample देखें →</a>
              {hub_hero_link}
            </div>
          </div>

          <aside class="buy-card" id="buy" aria-label="खरीद कार्ड">
            <div class="buy-top">
              <img class="buy-cover" src="{E(item['cover'])}" alt="{E(item['title'])} PDF कवर" width="240" height="336">
              <div>
                <span class="off-tag">{off_pct}% छूट · सीमित समय</span>
                <div class="price-row">
                  <span class="price-now">₹{item['price']}</span>
                  <span class="price-old">₹{item['mrp']}</span>
                </div>
                <p class="buy-sub" id="edSummary">हिंदी संस्करण · {item['hi_pages']} पृष्ठ PDF</p>
              </div>
            </div>

            <div class="edition-switch" role="group" aria-label="भाषा चुनें">
              <button type="button" class="ed-btn active" data-ed="hi" data-pages="{item['hi_pages']} पृष्ठ" data-label="हिंदी PDF" data-url="{E(buy_hi)}">
                <b>📘 हिंदी PDF</b>
                <span>{item['hi_pages']} पृष्ठ · ₹{item['price']}</span>
              </button>
              <button type="button" class="ed-btn" data-ed="en" data-pages="{item['en_pages']} pages" data-label="English PDF" data-url="{E(buy_en)}">
                <b>📗 English PDF</b>
                <span>{item['en_pages']} pages · ₹{item['price']}</span>
              </button>
            </div>

            <a id="mainBuyBtn" class="btn-primary" href="{E(buy_hi)}" target="_blank" rel="noopener">
              ₹{item['price']} में हिंदी PDF खरीदें →
            </a>
            <a class="btn-outline" href="{E(item['sample'])}" target="_blank" rel="noopener">
              📄 पहले 10 पेज Sample देखें
            </a>
            <p class="secure-note">🔒 UPI / PhonePe / GPay से तुरंत खरीद · सहायता: 7023166962</p>
          </aside>
        </div>
      </div>
    </section>

    <section class="sec white">
      <div class="wrap">
        <div class="sample-bar">
          <div>
            <h2>खरीदने से पहले 10 पेज पढ़कर परखें</h2>
            <p>Sample में असली PDF के शुरुआती 10 पन्ने दिए गए हैं ताकि आप भाषा, तालिकाएँ और क्वालिटी देखकर निश्चिंत हो सकें।</p>
          </div>
          <div class="sample-actions">
            <a class="btn-primary" href="{E(item['sample'])}" target="_blank" rel="noopener">📄 Sample PDF खोलें →</a>
            {hub_sample_btn}
          </div>
        </div>
      </div>
    </section>

    <section class="sec">
      <div class="wrap">
        <h2 class="sec-h">इस PDF की मुख्य विशेषताएँ</h2>
        <p class="sec-sub">RAS Pre + Mains, SSC, Railway व सभी प्रतियोगी परीक्षाओं के तेज़ revision के लिए तैयार।</p>
        <div class="grid-3">
          <article class="info-card">
            <span class="ic">📚</span>
            <b>एक विषय, एक फ़ाइल</b>
            <p>सभी अध्याय क्रम से एक ही PDF में — बार-बार अलग फ़ाइलें ढूँढने की ज़रूरत नहीं।</p>
          </article>
          <article class="info-card">
            <span class="ic">🗣️</span>
            <b>सरल भाषा व सार</b>
            <p>NCERT व मानक पुस्तकों पर आधारित आसान व्याख्या, तालिकाएँ और प्रमुख तथ्य।</p>
          </article>
          <article class="info-card">
            <span class="ic">🖨️</span>
            <b>Offline व Print Friendly</b>
            <p>एक बार सेव करें और बिना इंटरनेट मोबाइल, टैबलेट या प्रिंट निकालकर पढ़ें।</p>
          </article>
        </div>
      </div>
    </section>

    <section class="sec white">
      <div class="wrap">
        <h2 class="sec-h">विषय-सूची (क्या-क्या कवर है)</h2>
        <p class="sec-sub">नीचे क्लिक करके पूरे सिलेबस की झलक देखें।</p>
        <div class="acc">
          <details open>
            <summary>📖 {E(item['title'])} — मुख्य अध्याय</summary>
            <div class="acc-body">
              <ul class="topic-list">
                {topics_li}
              </ul>
            </div>
          </details>
        </div>
      </div>
    </section>

    <section class="sec">
      <div class="wrap">
        <h2 class="sec-h">3 आसान स्टेप्स में PDF प्राप्त करें</h2>
        <p class="sec-sub">पूरी प्रक्रिया सरल और सुरक्षित है।</p>
        <ol class="grid-3 steps">
          <li class="info-card">
            <b>भाषा और Sample देखें</b>
            <p>ऊपर हिंदी या English संस्करण चुनें और 10-पेज sample देखकर क्वालिटी जाँचें।</p>
          </li>
          <li class="info-card">
            <b>₹{item['price']} का भुगतान करें</b>
            <p>“अभी खरीदें” बटन पर क्लिक कर UPI / PhonePe / GPay से ₹{item['price']} का पेमेंट करें।</p>
          </li>
          <li class="info-card">
            <b>तुरंत PDF पाएँ</b>
            <p>पेमेंट कन्फ़र्म होते ही आपको पूरी PDF का सीधा डाउनलोड लिंक प्राप्त हो जाएगा।</p>
          </li>
        </ol>
      </div>
    </section>

    <section class="sec white">
      <div class="wrap">
        <h2 class="sec-h">अक्सर पूछे जाने वाले सवाल</h2>
        <div class="acc" style="margin-top:14px">
          <details>
            <summary>क्या यह Printed किताब है या Digital PDF?</summary>
            <div class="acc-body">यह Digital PDF E-Book है जिसे आप फ़ोन, लैपटॉप में पढ़ सकते हैं और चाहें तो प्रिंट करा सकते हैं। डाक से कोई किताब नहीं भेजी जाती।</div>
          </details>
          <details>
            <summary>क्या हिंदी और English दोनों अलग-अलग उपलब्ध हैं?</summary>
            <div class="acc-body">हाँ, इस विषय की हिंदी ({item['hi_pages']} पृष्ठ) और English ({item['en_pages']} पृष्ठ) दोनों PDF उपलब्ध हैं। ऊपर अपनी भाषा चुनकर खरीद सकते हैं।</div>
          </details>
          <details>
            <summary>पेमेंट के बाद कोई दिक्कत आए तो सहायता कहाँ मिलेगी?</summary>
            <div class="acc-body">पेमेंट स्क्रीनशॉट/ID के साथ WhatsApp <strong>7023166962</strong> या <strong>email2omkara@gmail.com</strong> पर संदेश भेजें, तुरंत सहायता दी जाएगी।</div>
          </details>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <b>ओंकार सर · New India Education</b>
    <p>RAS एवं सभी प्रतियोगी परीक्षाओं की प्रामाणिक अध्ययन सामग्री</p>
    <div class="f-links">
      <a href="/store.html">PDF Store</a>
      <a href="/all-notes.html">Free Notes</a>
      {hub_footer_link}
      <a href="/refund-policy.html">Refund Policy</a>
      <a href="/contact.html">Contact</a>
    </div>
  </footer>

  <div class="sticky-buy">
    <div>
      <div class="sb-price">₹{item['price']}<s>₹{item['mrp']}</s></div>
      <div class="sb-sub" id="stickySub">हिंदी PDF · {item['hi_pages']} पृष्ठ</div>
    </div>
    <a id="stickyBuyBtn" class="btn-primary" href="{E(buy_hi)}" target="_blank" rel="noopener">अभी खरीदें →</a>
  </div>

  <script>
    (function(){{
      var btns = document.querySelectorAll('.ed-btn');
      var mainBtn = document.getElementById('mainBuyBtn');
      var stickyBtn = document.getElementById('stickyBuyBtn');
      var summary = document.getElementById('edSummary');
      var stickySub = document.getElementById('stickySub');
      btns.forEach(function(btn){{
        btn.addEventListener('click', function(){{
          btns.forEach(function(b){{ b.classList.remove('active'); }});
          btn.classList.add('active');
          var url = btn.getAttribute('data-url');
          var label = btn.getAttribute('data-label');
          var pages = btn.getAttribute('data-pages');
          mainBtn.href = url;
          mainBtn.textContent = '₹{item['price']} में ' + label + ' खरीदें →';
          stickyBtn.href = url;
          summary.textContent = label + ' · ' + pages;
          stickySub.textContent = label + ' · ' + pages;
        }});
      }});
    }})();
  </script>
  <script src="/nied-menu.js" defer></script>
</body>
</html>
"""


def render_store_card(item):
    off_pct = round((item["mrp"] - item["price"]) * 100 / item["mrp"])
    short_desc = item["desc"]
    if len(short_desc) > 105:
        short_desc = short_desc[:102].rsplit(" ", 1)[0] + "..."
    return (
        f'      <article class="card" data-title="{E(item["title"] + " " + item["en_title"])}" data-category="भारत GK">\n'
        f'        <a class="thumb refreshed-thumb" href="/{E(item["slug"])}" aria-label="{E(item["title"])} PDF">\n'
        f'          <span class="badge">{E(item["badge"])}</span>\n'
        f'          <img src="{E(item["cover"])}" alt="{E(item["title"])} पुस्तक का कवर" width="800" height="1120" loading="lazy" decoding="async">\n'
        f'          <span class="seal">{off_pct}%<small>छूट</small></span>\n'
        f'        </a>\n'
        f'        <div class="body">\n'
        f'          <span class="tag">{E(item["tag"])}</span>\n'
        f'          <h3><a href="/{E(item["slug"])}">{E(item["title"])}</a></h3>\n'
        f'          <p>{E(short_desc)}</p>\n'
        f'          <div class="meta"><span>हिंदी: {item["hi_pages"]} पृष्ठ</span><span>English: {item["en_pages"]} पृष्ठ</span><span>Digital PDF</span></div>\n'
        f'          <div class="price"><b>₹{item["price"]}</b><s>₹{item["mrp"]}</s><em>{off_pct}% छूट</em></div>\n'
        f'          <div class="actions"><a class="btn" href="/{E(item["slug"])}">देखें और खरीदें →</a><a class="ghost" href="{E(item["sample"])}" target="_blank" rel="noopener">📄 10-Page Sample</a></div>\n'
        f'        </div>\n'
        f'      </article>'
    )


def update_store_html():
    store_path = os.path.join(ROOT, "store.html")
    with open(store_path, "r", encoding="utf-8") as f:
        store = f.read()

    for item in INDIA_GK_PDFS:
        slug = item["slug"]
        pattern = re.compile(
            r'<article class="card[^"]*"[^>]*>(?:(?!</article>).)*?href="/' + re.escape(slug) + r'"(?:(?!</article>).)*?</article>',
            re.S,
        )
        new_card = render_store_card(item)
        store, count = pattern.subn(lambda _m: new_card, store, count=1)
        assert count == 1, f"Could not find unique card for {slug} in store.html (found {count})"

    # Ensure refreshed-thumb shows the badge & discount seal cleanly on ₹49 cards
    store = store.replace(
        ".refreshed-thumb .badge,.refreshed-thumb .seal{display:none}",
        ".refreshed-thumb .badge{font-size:11.5px}.refreshed-thumb .seal{width:50px;height:50px;font-size:15px}",
    )
    store = store.replace(
        "<span>🔒 नए PDF के Razorpay लिंक क्रम से जोड़े जाएँगे</span>",
        "<span>💎 भारत GK के 10 विषय अब ₹49 में उपलब्ध</span>",
    )

    with open(store_path, "w", encoding="utf-8") as f:
        f.write(store)


def main():
    for item in INDIA_GK_PDFS:
        out_path = os.path.join(ROOT, item["slug"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_page(item))
        print("Built:", item["slug"])
    update_store_html()
    print("Updated: store.html with", len(INDIA_GK_PDFS), "uniform ₹49 India GK cards")


if __name__ == "__main__":
    main()
