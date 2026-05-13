# Vision PDF OCR

Extract text from scanned, textless PDFs using **vision-language models** (VLMs) with **customizable system prompts** for context-aware accuracy.

Perfect for:
- Old/blurry scanned textbooks
- Documents with special characters or unusual romanization
- Multilingual scanned materials
- Any image-based PDF where traditional OCR fails

---

## Why Vision OCR?

Traditional OCR (Tesseract, PaddleOCR) struggles with:
- Muffled or distorted fonts
- Unusual characters not in training data
- Complex layouts with mixed languages
- Low-quality scans

Vision-language models (Gemini, Claude) "read like humans" — they understand context, layout, and can be guided with **system prompts** (e.g., "the romanization uses ğ, ħ, ž").

---

## Backends Supported

| Backend | Requirements | Best For |
|---------|-------------|----------|
| **Ollama Cloud** (default) | `OLLAMA_API_KEY` in `.env`, Pro subscription | Fast, cheap, multilingual |
| **OpenRouter** | `OPENROUTER_API_KEY` in `.env` | Fallback, model choice |
| **Direct Gemini** | `GEMINI_API_KEY` | Google's native API |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Basic extraction

```bash
python scripts/batch_ocr.py scan.pdf
```

### 3. With custom system prompt (context-aware)

```bash
python scripts/batch_ocr.py old-textbook.pdf \
  --system-prompt "This is an Ottoman Turkish textbook. The romanization uses ğ, ħ, ı, ş, ç, ö, ü. Preserve all diacritics exactly."
```

### 4. Save to specific directory

```bash
python scripts/batch_ocr.py scan.pdf --output-dir ./extracted/
```

### 5. Resume interrupted job

```bash
python scripts/batch_ocr.py scan.pdf --resume
```

---

## Model Selection for Character-Level Accuracy

When extracting documents with **custom romanization or special character systems** (e.g., Arabic transliteration with 9, H, ḥ, ʿ, ī, ā), model choice matters significantly for character-level fidelity:

| Model | Character Accuracy | Speed | Recommendation |
|-------|-------------------|-------|----------------|
| `gemini-3-flash-preview:cloud` | **Excellent** — preserves diacritics, special chars, stress marks | Fast | **Default choice** for romanized language textbooks |
| `gemma4:31b-cloud` | Poor — hallucinates characters, drops diacritics, invents forms | Medium | **Avoid** for precise transliteration work |
| `claude-sonnet-4-20250514` | Very good | Slower | Use via OpenRouter when flash fails |

**Test before bulk processing:** Always run a 2-page sample with your target document before committing to a 400+ page batch. Character errors in language learning materials are costly to fix retroactively.

### The 2-Page Test Protocol

Before bulk-processing any language textbook, test with these two page types:

1. **Dialogue page** — tests inline Arabic bolding, speaker labels, mixed English-Arabic lines
2. **Vocabulary page** — tests table formatting, slash-separated forms (`máraD/yímraD/máraD`), parenthetical additions (`kaláafa*`, `muqáabla*(aat)`), multi-line entries

Check specifically for:
- Character hallucinations (e.g., `d` → `C`, `j` → `i`, `9` → `g`)
- Dropped diacritics/stress marks (e.g., `á` → `a`, `í` → `i`)
- Split vocabulary tables (should be ONE continuous table per page)
- Missing Arabic words without special chars (e.g., `chinn-`, `farg`, `tist`)
- Page headers leaking through (e.g., "Unit 19", "310")

---

## Default System Prompt Rules

The built-in default system prompt automatically applies these rules to every extraction. You can override or extend them via `--system-prompt`:

1. **Extract ALL visible text** exactly as it appears
2. **Preserve original language**, special characters, and diacritics
3. **Use markdown formatting** (tables, headers, lists) where appropriate
4. **Mark unclear text** with `[unclear: best_guess]`
5. **Note blank pages** — if the page is blank or contains only illustrations, say so
6. **No commentary** — output ONLY the extracted text and structure
7. **TOC JSON heading hierarchy** — if a TOC JSON is provided, use it to assign correct `<h>` tag levels (`#`, `##`, `###`, ...). The JSON has nested `title`/`pdf-page-no`/`children` structure. Depth 0 = `#`, depth 1 = `##`, etc.
8. **Use `<table>` elements** as much as possible for structured data
9. **One column per category** — when listing words, do NOT create multi-column side-by-side tables
10. **Double trailing spaces for line breaks** — single line breaks collapse in HTML; add two spaces at end of line to force `<br>`
11. **Preserve formatting** — apply bold, italic, underline exactly as displayed
12. **`<span class="tl">` wrapper** — target language text should be wrapped with `<span class="tl">text</span>`
13. **Ignore headers and footers** — running page numbers, document titles, chapter banners
14. **Image descriptions** — add simple minimal descriptions for images/diagrams/illustrations

These rules are **appended to** (not replaced by) any custom `--system-prompt` you provide.

---

## System Prompts: The Secret Weapon

The `--system-prompt` parameter lets you teach the model about your document before extraction. This dramatically improves accuracy for:

- **Special characters**: "This document uses medieval Latin abbreviations: ͙, ̅, ̾"
- **Romanization**: "The romanization system uses ğ, ħ, ž, ş, ç"
- **Language context**: "This is a 19th-century German physics text with Fraktur script"
- **Layout hints**: "Tables have no borders; columns are separated by whitespace"
- **Content type**: "This is a bilingual Korean-English legal contract"

---

## Full CLI Reference

```
python scripts/batch_ocr.py <pdf_path> [options]

Options:
  --system-prompt TEXT    Context prompt for the vision model
  --backend {ollama,openrouter,gemini}
                          Vision backend (default: ollama)
  --model MODEL           Specific model tag
  --dpi DPI               Render resolution (default: 200)
  --pages PAGES           Page range: "1-10" or "1,3,5"
  --output-dir DIR        Output directory (default: same as PDF)
  --output-name NAME      Output filename (default: <pdf>_ocr.md)
  --resume                Resume from checkpoint
  --delay SECONDS         Delay between requests (default: 2.0, minimum 2.0 to stay under 30 RPM)
  --max-retries N         Retries per page (default: 3)
  --json                  Also save JSON metadata sidecar
  --quiet                 Minimal output
  --help                  Show this help
```

---

## Examples

### Example 1: Blurry old textbook with special characters

```bash
python scripts/batch_ocr.py ./turkish-grammar-1920.pdf \
  --system-prompt "Ottoman Turkish grammar book. Special letters: ğ (g-breve), ı (dotless i), ş (s-cedilla), ç (c-cedilla), ö, ü. Preserve ALL diacritics. Footnotes appear in smaller font at bottom of page." \
  --dpi 300 \
  --output-dir ./extracted/
```

### Example 2: Language textbook with custom Latin transliteration — Arabic

This example demonstrates the complete system prompt for a Gulf Arabic textbook using a custom Latin transliteration system. The key insight: **vision OCR with explicit character instructions dramatically outperforms text-based extraction** (`pdftotext` + regex) because the model understands layout context and can distinguish Arabic words without special characters (e.g., `chinn-`, `farg`, `tist`) from English words.

```bash
python scripts/batch_ocr.py ./gulf-arabic-textbook.pdf \
  --system-prompt "This is a Gulf Arabic language textbook. IGNORE any page numbers and running headers like 'Unit X' or '310' at the top of pages - do not include them in the output.

The text uses Latin transliteration for Arabic words with these special characters: 9 (ayn), H (ha), S (sad), T (ta), D (dad), DH (dha), x (kha), gh (ghayn), q (qaf), ʼ (hamza). Vowels with acute accents indicate stress: á, í, ú. Long vowels are doubled: aa, ii, oo, uu.

ARABIC TEXT BOLDING:
Render ALL transliterated Arabic text in bold markdown (**text**). This includes:
- Words with Arabic special characters (9, H, S, T, D, DH, x, gh, q, ʼ, á, í, ú)
- Common Arabic function words even without special chars: min, il-, yaa, maa, laysh, wayn, shloon, kull, ba9ad, fii, fi, 9ala, 9ind, ma9a, li, la, ay, laa, muu, mub, 9aad, 9óob, 9ógub, Haalan, dáa9iman, ábadan, zayn, nzayn, máashi, támaam, yállah
- English explanatory text should remain unbolded

VOCABULARY LIST FORMATTING (very important):
- Vocabulary lists are arranged in TWO COLUMNS per page. Each column has Arabic on the left, English on the right.
- FLATTEN the two columns into ONE single markdown table with two columns: | Arabic | English |
- Many entries span TWO OR MORE LINES. Keep multi-line entries together as a single row.
- Arabic words often show singular/plural/conjugated forms separated by SLASHES: e.g. 'máraD/yímraD/máraD', 'istáahal/yistáahil', 'wádda9/yiwáddi9', 'Harb (f.)/Hurúub', 'karíim/kiráam'. Keep the ENTIRE slash-separated form as ONE Arabic cell.
- Some Arabic words have parenthetical additions: e.g. 'istánfa9/yistanfi9(min)', 'rizg (or rizj)', 'kaláafa*', 'máSlaHa*/maSáaliH', 'risáala*', 'shúghla*', 'TáyHa*(aat)', 'muwáDHDHaf (iin)', 'muqáabla*(aat)', 'naDHDHáara* (aat)'. Include these parentheses and asterisks as part of the Arabic term.
- Some English definitions also have parenthetical notes: e.g. 'to profit; benefit (from)', 'sustenance; food (fig.)'. Include these in the English cell.
- Keep ALL vocabulary entries from a single page in ONE continuous markdown table. Do NOT split into multiple tables.

DIALOGUE FORMATTING:
- Format dialogue lines as: > **A** Arabic text here
- Keep speaker labels (A, B, C, etc.) outside the bold

STRUCTURE TO PRESERVE:
- Unit headers as # Unit X
- Section numbers as ## X.Y Title
- Exercise headers as ### Exercise X.Y
- Dialogue headers as ### Dialogue X.Y
- Cultural point sections as ### Cultural Point
- Reading Arabic sections as ### Reading Arabic" \
  --output-dir ./extracted/ \
  --model gemini-3-flash-preview:cloud
```

### Example 3: Language textbook with custom Latin transliteration — Sinhala (transliteration-only)

Sinhala language materials use Latin transliteration alongside Sinhala script (සිංහල). The key challenge is extracting only the Latin-alphabet transliteration while ignoring pure English instructional text and the Sinhala script itself.

```bash
python scripts/batch_ocr.py ./sinhala-level-1.pdf \
  --system-prompt "This is a Sinhala language learning textbook. The document contains English instructional text mixed with transliterated Sinhala words written in the Latin alphabet.

EXTRACT ONLY TRANSLITERATED SINHALA TEXT. Transliterated Sinhala means Sinhala words written using English/Latin letters, like: Oyaage, Mama, kohomadha, thiyenawa, kaaema, waediyen, Mage, Oyaa, kiiyadha, mokadhdha, rassaawa, wayasa, kaemathiidha, kanna, puluwandha, dhannawadha, natanawa, liyanawa, balanawa, yanawa, bonawa, kanawa, karanawa, eken, Meewa, kiyanna, His, thaen, purawanna, Oyaata, kathaa, karanna, kohendha, en, inne, kawdha, thiyenne, ekakdha, gaena, liyanna, eyaata, monaadha, thiyenne, issara, hitiye, hondhai, rasai, Lankaawe, saerai, Mee, wachane, Prashna, pawle, Lakshanige, Lakshanita, car, bike, naae, Ow, eka, waediyen.

DO NOT extract pure English words like 'Summary', 'Questions', 'Hello', 'Answer', 'Possessive', 'Exceptions', 'Lessons', 'Feelings', 'Greetings', 'Homework', 'Dialogue', 'Practice'.

IGNORE page numbers, running headers like 'Lessons in level 1', and the watermark 'Created by Shani Bulathsinghala' at the bottom of pages.

When transliterated Sinhala appears alongside Sinhala script (සිංහල), extract ONLY the Latin-alphabet transliteration, not the Sinhala script.

Format the output as a clean list of transliterated Sinhala words/phrases found on the page. If there are full sentences in transliterated Sinhala, preserve them." \
  --output-dir ./extracted/ \
  --model gemini-3-flash-preview:cloud
```

### Example 4: Full-text extraction preserving layout (Sinhala)

When you need ALL text organized as it appears on the page — not just transliteration — use a full-text system prompt with explicit layout preservation instructions.

```bash
python scripts/batch_ocr.py ./sinhala-level-1.pdf \
  --system-prompt "This is a Sinhala language learning textbook. Extract ALL text from the page exactly as it appears, preserving the original layout and organization.

PRESERVE STRUCTURE:
- Keep tables as markdown tables (vocabulary lists, pronunciation charts)
- Preserve dialogue format with speaker labels (A:, B:, etc.)
- Maintain bullet points and numbered lists
- Keep section headers and titles
- Preserve two-column layouts as tables where appropriate
- Keep question/answer formatting

EXTRACT EVERYTHING:
- English instructional text
- Transliterated Sinhala (Latin alphabet words like Oyaage, Mama, kohomadha)
- Sinhala script (සිංහල)
- Headers, subheaders, and page titles
- Exercise instructions and questions
- Grammar explanations and examples
- Cultural notes and tips

IGNORE ONLY:
- Page numbers
- Running headers like 'Lessons in level 1'
- Watermark 'Created by Shani Bulathsinghala' at the bottom of pages

FORMAT:
- Use markdown formatting to reflect the visual hierarchy
- Bold for emphasized words
- Tables for vocabulary lists and structured content
- Blockquotes or > prefix for dialogue lines
- Code blocks for pronunciation charts if needed
- Preserve the relationship between English and Sinhala text when they appear side by side" \
  --output-dir ./extracted/ \
  --output-name "sinhala_fulltext_pages_1-100.md" \
  --model gemini-3-flash-preview:cloud
```

### Example 5: Grammar book with TOC JSON for heading hierarchy

When you have a structured grammar book, embed the TOC directly into the system prompt. This ensures the model assigns correct markdown heading levels (`#` through `#####`) based on the document's actual hierarchy.

```bash
python scripts/batch_ocr.py ./spoken-sinhala-grammar.pdf \
  --pages 16-117 \
  --system-prompt "This is a grammar book of spoken Sinhala. Sinhala language texts are mostly romanized (Latinized).

IMPORTANT: All (Latinized) Sinhala text must be written in ITALICS (*text*).

The special letters for romanization used here are: æ, ā, à, ǣ, ī, ū, ē, ō, ń, ḿ, ṅ, ñ, ṇ, ḍ, ṭ, ḷ, ś, ṣ, ŋ. The symbol combination V̄ (V + macron) is used to denote a long vowel.

TABLE OF CONTENTS REFERENCE — Use this to assign correct heading levels. Match section titles against the titles below and use the indicated heading level. The page numbers refer to actual PDF page numbers.

Page 16: ## Nouns
Page 16: ### Animate and inanimate
Page 18: ### Case
Page 18: #### Case functions
Page 20: #### Noun classes
Page 20: ##### Singular nouns
... (etc) ...
Page 53: # PREDICATION
Page 54: ## Verbs
..." \
  --output-dir ./extracted/ \
  --model gemini-3-flash-preview:cloud
```

### Example 6: Resume after crash

```bash
python scripts/batch_ocr.py ./500-page-archive.pdf \
  --system-prompt "19th century French administrative documents. Use of long s (ſ) and archaic spellings." \
  --resume
```

---

## Output Format

### Markdown (`<name>_ocr.md`)

The output is a **single merged markdown file** containing all extracted pages. This file includes `## Page N` markers between pages and preserves the structure detected by the vision model.

```markdown
# Extracted: turkish-grammar-1920.pdf

**Metadata:**
- Pages: 245
- Backend: ollama
- Model: gemini-3-flash-preview:cloud
- Extracted: 2026-05-12 14:30:00
- System prompt: [hash: a3f7c2]

---

## Page 1

# TÜRKÇE GRAMERİ

## Birinci Kısım: Sesler

Türkçede üç ünlü vardır: a, ı, u...

---

## Page 2

[Note: Page appears to be blank or contains only an illustration]

---

## Page 3

| Harf | Adı | Sesi |
|------|-----|------|
| A a | a | [a] |
| B b | be | [b] |
```

### JSON Sidecar (`<name>_ocr.json`) — optional with `--json`

```json
{
  "source": "turkish-grammar-1920.pdf",
  "pages_total": 245,
  "pages_processed": 245,
  "pages_failed": 0,
  "backend": "ollama",
  "model": "gemini-3-flash-preview:cloud",
  "system_prompt_hash": "a3f7c2",
  "extracted_at": "2026-05-12T14:30:00Z",
  "pages": [
    {
      "page": 1,
      "status": "success",
      "text_length": 1245,
      "processing_time": 4.2,
      "model": "gemini-3-flash-preview:cloud"
    }
  ]
}
```

---

## How It Works

```
[PDF]
  ↓  PyMuPDF renders each page to PNG (200 DPI)
[Page Image]
  ↓  Send to VLM with system prompt + image
[Vision Model]
  ↓  Returns extracted markdown text
[Output]
  ↓  Concatenate all pages into single markdown file
```

---

## Rate Limiting

To respect API rate limits and stay under **30 requests per minute**, a **minimum 2-second delay** is enforced between page requests. This is hardcoded — you cannot set `--delay` below 2.0.

| Backend | Approximate Speed |
|---------|------------------|
| Ollama Cloud | ~2-4s per page + 2s delay = ~4-6s/page |
| OpenRouter | Varies by model |
| Gemini | Varies by model |

For a 100-page document, expect **~10-15 minutes** total processing time.

---

## Large-Batch Processing Strategy

For documents with 200+ pages, consider these approaches:

### Option A: Chunked batches (recommended for 400+ pages)

Process in chunks of 50–100 pages, review quality, then continue:

```bash
# Batch 1: validate approach on small sample
python scripts/batch_ocr.py ./textbook.pdf --pages 1-50 --output-name textbook_p1-50.md

# Review output, then continue in chunks
python scripts/batch_ocr.py ./textbook.pdf --pages 51-150 --output-name textbook_p51-150.md
python scripts/batch_ocr.py ./textbook.pdf --pages 151-250 --output-name textbook_p151-250.md
# ... etc
```

### Option B: Parallel chunk execution (fastest for large documents)

Launch multiple non-overlapping chunks simultaneously:

```bash
# Terminal 1: chunk A
python scripts/batch_ocr.py ./textbook.pdf --pages 1-100 --output-name textbook_p1-100.md &

# Terminal 2: chunk B
python scripts/batch_ocr.py ./textbook.pdf --pages 101-200 --output-name textbook_p101-200.md &

# Terminal 3: chunk C
python scripts/batch_ocr.py ./textbook.pdf --pages 201-300 --output-name textbook_p201-300.md &
```

**Critical requirements for parallel execution:**
- Each chunk must use **different `--pages` ranges** (no overlap)
- Each chunk must use **different `--output-name` files** (no collision)
- Same `--system-prompt`, `--backend`, and `--model` across all chunks
- Combine outputs after all chunks finish: `cat textbook_p*.md > textbook_full.md`

### Option C: Background with checkpoint monitoring

```bash
# Start the job
python scripts/batch_ocr.py ./textbook.pdf --pages 1-500 &

# Monitor progress via checkpoint file
watch -n 10 'python3 -c "import json; cp=json.load(open(\".textbook_ocr_checkpoint_*.json\")); print(f\"Completed: {len(cp[\\\"completed_pages\\\"])}\")"'
```

The checkpoint file updates after every page. Kill the process anytime and resume with `--resume`.

---

## Integration with Wiki Pipeline

After extraction, ingest into your knowledge base:

```bash
# Option 1: Direct to wiki
synthadoc ingest -w my-knowledge ./extracted/turkish-grammar-1920_ocr.md

# Option 2: Via OpenDataLoader (for structure preservation)
bash ~/.hermes/skills/data-science/opendataloader-pdf/scripts/ingest_to_synthadoc.sh \
  ./extracted/turkish-grammar-1920_ocr.md
```

---

## Post-Processing: Splitting into Chapters

The `batch_ocr.py` output is a single merged file. To split it into per-chapter markdown files, use the `pdf-textbook-parser` skill:

```bash
# After OCR completes:
python ~/.hermes/skills/productivity/pdf-textbook-parser/scripts/split_vision_ocr.py \
  ./extracted/textbook_ocr.md \
  --output-dir ./chapters/
```

---

## Advanced: Programmatic Usage

```python
from scripts.vision_ocr import VisionPDFProcessor

processor = VisionPDFProcessor(
    backend="ollama",
    model="gemini-3-flash-preview:cloud",
    system_prompt="This is a medieval Latin manuscript...",
    dpi=300,
    delay=2.0,  # minimum 2.0s enforced to stay under 30 RPM
)

result = processor.process_pdf(
    "manuscript.pdf",
    output_path="manuscript_ocr.md",
    pages="1-50",
)

print(f"Processed {result.pages_processed} pages")
```

---

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `OLLAMA_API_KEY` | Ollama backend | Your Ollama Cloud API key |
| `OPENROUTER_API_KEY` | OpenRouter backend | Your OpenRouter key |
| `GEMINI_API_KEY` | Gemini backend | Google Gemini API key |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No API key found" | Add `OLLAMA_API_KEY=...` to `~/.hermes/.env` |
| Text is garbled/missing | Increase `--dpi` to 300 or higher |
| Model misses special chars | Make them **explicit** in `--system-prompt` |
| Model hallucinates characters / drops diacritics | Switch to `gemini-3-flash-preview:cloud` — see Model Selection section |
| Page headers leak into output | Add "IGNORE page numbers and running headers" to system prompt |
| Vocabulary tables split incorrectly | Add explicit "Keep ALL vocabulary entries in ONE continuous table" instruction |
| TOC JSON has `\uXXXX` escapes | Clean with `python -c "import json; print(json.dumps(json.load(open('toc.json')), ensure_ascii=False))"` before embedding |
| Model assigns wrong heading levels | Embed the TOC directly in the system prompt with explicit "Page N: ## Title" format |
| Rate limit errors | Already handled — minimum 2s delay enforced |
| Processing too slow | This is expected for vision OCR (~4-6s/page). For 200+ pages, see Large-Batch Processing Strategy |
| Pages fail repeatedly | Try `--backend openrouter` with different model |
| Resume not working | Check checkpoint file exists in output dir |
| Job was killed before completion | Checkpoint preserves progress. Resume with `--resume` or process remaining range with `--pages`. Note: output file is only written on successful completion. |

---

## References

- `references/gulf-arabic-textbook-extraction.md` — Complete extraction pattern for Latin-transliterated Arabic textbooks
- `references/test-results-palestinian-arabic.md` — Real-world validation: 29-page Palestinian Arabic textbook extracted with 100% character preservation
- `references/sinhala-textbook-extraction.md` — Sinhala language learning materials: extracting Latin-alphabet transliteration from mixed English-Sinhala slide-based PDFs
- `references/sinhala-grammar-toc-integration.md` — TOC JSON integration workflow for correct heading hierarchy in grammar books
- `references/ollama-cloud-backend.md` — Why native API is used (not Hermes `vision_analyze`), tested models, and backend alternatives
- `references/skills-sh-ocr-research.md` — Skills.sh research findings that led to this skill's creation

---

## License

MIT

