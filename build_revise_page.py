# -*- coding: utf-8 -*-
import json, re, os

base_dir = '/Users/omkarsingh/Desktop/omkarsir-website/quizzes'

def extract_array(text, prefix):
    idx = text.find(prefix)
    if idx == -1: return []
    start = idx + len(prefix)
    open_b = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '[': open_b += 1
        elif text[i] == ']':
            open_b -= 1
            if open_b == 0:
                end = i + 1
                break
    if end == -1: return []
    try:
        return json.loads(text[start:end])
    except Exception as e:
        print("Parse error:", e)
        return []

def clean(s):
    if not s: return ''
    return ' '.join(str(s).strip().split())

# 1. Art & Culture
with open(os.path.join(base_dir, 'top-150-mcqs-raj-art-culture-2026-08-29-thtl.html'), 'r', encoding='utf-8') as f:
    art_raw = extract_array(f.read(), 'var DATA={hi:')[:35]

# 2. Rajasthan History
with open(os.path.join(base_dir, 'rajasthan-history-150-top-mcqs-2026-08-29-0rbg.html'), 'r', encoding='utf-8') as f:
    hist_raw = extract_array(f.read(), 'var DATA={hi:')[:35]

# 3. Rajasthan Geography
with open(os.path.join(base_dir, 'pyqs-mcqs-2026-08-06-8ozj.html'), 'r', encoding='utf-8') as f:
    geo_raw = extract_array(f.read(), 'var D=')[:35]

# 4. Rajasthan Polity
with open(os.path.join(base_dir, 'raj-polity-sub-inspector-pyqs-2026-07-31-4bfu.html'), 'r', encoding='utf-8') as f:
    pol_raw = extract_array(f.read(), 'var D=')[:35]

# 5. Economy & Economic Survey
with open(os.path.join(base_dir, 'si-economy-pyqs-2026-08-04-irv4.html'), 'r', encoding='utf-8') as f:
    eco_raw = extract_array(f.read(), 'var D=')[:35]

# 6. Indian Constitution & Polity
with open(os.path.join(base_dir, 'top-300-mcqs-india-polity-2026-09-21-wss5.html'), 'r', encoding='utf-8') as f:
    ind_pol_raw = extract_array(f.read(), 'var DATA={hi:')[:35]

# 7. General Science
with open(os.path.join(base_dir, 'basics-of-everyday-science-2026-08-08-r9js.html'), 'r', encoding='utf-8') as f:
    sci_raw = extract_array(f.read(), 'var DATA={hi:')[:35]

questions = []

def process_batch(items, subject, exam_tag):
    for q in items:
        text = clean(q.get('text', ''))
        opts = []
        for o in q.get('opts', []):
            opts.append({
                'k': clean(o.get('k', '')).upper(),
                'v': clean(o.get('v', ''))
            })
        ans = clean(q.get('ans', '')).upper()
        exp = clean(q.get('exp', ''))
        questions.append({
            'id': len(questions) + 1,
            'subj': subject,
            'exam': exam_tag,
            'text': text,
            'opts': opts,
            'ans': ans,
            'exp': exp
        })

process_batch(hist_raw, 'राजस्थान इतिहास', 'RPSC RAS Pre')
process_batch(art_raw, 'कला व संस्कृति', 'RPSC RAS Pre / SI')
process_batch(geo_raw, 'राजस्थान भूगोल', 'RPSC RAS Pre')
process_batch(pol_raw, 'राजस्थान राजव्यवस्था', 'RPSC SI / RAS')
process_batch(eco_raw, 'अर्थव्यवस्था', 'RPSC RAS / SI')
process_batch(ind_pol_raw, 'भारतीय संविधान', 'RPSC RAS / UPSC')
process_batch(sci_raw, 'सामान्य विज्ञान', 'RPSC RAS Pre')

print(f"Total curated questions ready: {len(questions)}")

# Write to a JSON file first for safety
with open('/Users/omkarsingh/Desktop/omkarsir-website/revise_questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print("Saved revise_questions.json successfully")
