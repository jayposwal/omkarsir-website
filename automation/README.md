# Current Affairs PDF Generator

Generates a branded, printable PDF from a dated Current Affairs page
(`current-affairs/YYYY-MM-DD.html`) for automated distribution (e.g. Telegram).

The website's own "Download PDF" button (client-side, html2pdf.js) is
unrelated to this — this script is a separate, server-side generator for use
by scheduled/automated tasks that don't have a browser available.

## Why WeasyPrint (not fpdf2 or a headless browser)

- A headless browser (Playwright/Puppeteer) could reuse the site's own
  html2pdf.js script, but needs system libraries (libnss3, libatk, etc.)
  that require `sudo apt install`, which is not available in the automation
  sandbox.
- A pure-Python library like `fpdf2` has no complex-text-shaping engine, so
  Devanagari words with pre-base vowel signs (e.g. "वि", "कि") render with
  the matra in the wrong position (e.g. "विज्ञान" becomes "वज्ञिान").
- WeasyPrint renders through Pango + HarfBuzz + Cairo, which are already
  present on the system as shared libraries, and gives fully correct Indic
  script shaping plus native CSS Paged Media support (running headers/
  footers, page numbers via `counter(page)`/`counter(pages)`).

## Fonts

`fonts/NotoMerged-Regular.ttf` and `fonts/NotoMerged-Bold.ttf` are Noto Sans
Devanagari (SIL OFL 1.1 licensed — see `fonts/OFL-LICENSE.txt`), with the
Devanagari and Latin subsets merged into a single file per weight (via
`fonttools pyftmerge`) since the upstream distribution ships them as
separate per-script files. Emoji are intentionally NOT supported — color
emoji font merging drops the color bitmap tables, so the generator strips
emoji from extracted content and uses plain coloured CSS bullets instead.

## Usage

```
pip install weasyprint beautifulsoup4 --break-system-packages

python3 automation/generate_ca_pdf.py \
  current-affairs/2026-07-18.html \
  /path/to/output.pdf \
  --hindi-date "18 जुलाई 2026" \
  --eng-date "18 July 2026" \
  --font-regular automation/fonts/NotoMerged-Regular.ttf \
  --font-bold automation/fonts/NotoMerged-Bold.ttf \
  --site-url omkarsir.com
```

Output: a cover+index page followed by the 7 sections (National,
International, Rajasthan, Sujas, Economic, Science-Defence-Tech,
Sports-Awards), each item as extracted from the HTML's `.ca-item` blocks,
with a running header (site + date), footer (site, page X of Y, brand name)
and a subtle diagonal watermark on every content page.

## Still to do (blocked on user input)

Sending the generated PDF to Telegram (`sendDocument` via Bot API) is not
yet wired in — needs a bot token (from @BotFather) and the target channel's
username/ID, with the bot added as an admin with post permission.
