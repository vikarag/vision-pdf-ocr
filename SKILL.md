---
name: vision-pdf-ocr
description: Batch OCR for scanned PDFs using vision-language models. Supports customizable system prompts for context-aware extraction of blurry, multilingual, and special-character documents.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
category: mlops
metadata:
  hermes:
    tags: [PDF, OCR, Vision, Multilingual, Scanned-Documents, Batch-Processing]
    related_skills: [ocr-and-documents, pdf-to-wiki-pipeline, opendataloader-pdf]
---

# Vision PDF OCR

Extract text from scanned, textless PDFs using vision-language models (VLMs) with **customizable system prompts** for context-aware accuracy.

**Note on Remote Hosts**: If dependencies like `pymupdf` are missing on a NAS/SSH host, see `references/remote-nas-fallback-workflow.md` for a local-processing fallback pattern.

Perfect for:
- Old/blurry scanned textbooks
- Documents with special characters or unusual romanization
- Multilingual scanned materials
- Any image-based PDF where traditional OCR fails

## Why Vision OCR?

Traditional OCR (Tesseract, PaddleOCR) struggles with:
- Muffled or distorted fonts
- Unusual characters not in training data
- Complex layouts with mixed languages
- Low-quality scans

Vision-language models (Gemini, Claude) "read like humans" — they understand context, layout, and can be guided with **system prompts** (e.g., "the romanization uses ğ, ħ, ž").

## Backends Supported

| Backend | Requirements | Best For |
|---------|-------------|----------|
| **Ollama Cloud** (default) | `OLLAMA_API_KEY` in `.env`, Pro subscription | Fast, cheap, multilingual |
| **OpenRouter** | `OPENROUTER_API_KEY` in `.env` | Fallback, model choice |
| **Direct Gemini** | `GEMINI_API_KEY` | Google's native API |

## Quick Start

### Prerequisites

```bash
pip install pymupdf
```

### 1. Basic extraction

```bash
python scripts/batch_ocr.py scan.pdf
```

### 2. With custom system prompt (context-aware)

```bash
python scripts/batch_ocr.py old-textbook.pdf \
  --system-prompt "This is an Ottoman Turkish textbook. The romanization uses ğ, ħ, ı, ş, ç, ö, ü. Preserve all diacritics exactly."
```

### 3. Save to specific directory

```bash
python scripts/batch_ocr.py scan.pdf --output-dir ./extracted/
```

### 4. Resume interrupted job

```bash
python scripts/batch_ocr.py scan.pdf --resume
```

### 5. Run in background with completion notification (opt-in)

Jobs run in **foreground mode** by default (attached to the terminal). Use `--background` to detach the process so it survives SSH disconnects, and `--notify-on-complete` to get alerted when it finishes.

```bash
# Run in background with notification
python scripts/batch_ocr.py ./500-page-archive.pdf \
  --system-prompt "19th century French administrative documents..." \
  --background \
  --notify-on-complete
```

Monitor progress:
```bash
tail -f ./500-page-archive_ocr.log
```

Check if still running:
```bash
ps aux | grep batch_ocr
# or
cat ./500-page-archive_ocr.pid | xargs ps
```

Stop the job:
```bash
kill $(cat ./500-page-archive_ocr.pid)
```

**Opt-in flags:**
- `--background` — run detached from the current terminal
- `--notify-on-complete` — send a completion alert

**Background mode features:**
- Process detaches from terminal (survives SSH disconnect, new messages, etc.)
- Automatic log file with timestamps and command history
- PID file for easy process management
- Prevents duplicate jobs (checks PID file before starting)
- `--resume` flag is preserved if specified
- Completion notification sent via Hermes gateway IPC socket (or JSON fallback)
- **Note:** Hermes `terminal()` has a hard 600s (10 minute) foreground timeout. For long jobs, use `terminal(background=true, notify_on_complete=True)` or chunk into smaller batches.
- Default log file: `<output_dir>/<pdf>_ocr.log`
- Default PID file: `<output_dir>/<pdf>_ocr.pid`

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

## Default System Prompt Rules

The built-in default system prompt (in `scripts/vision_ocr.py`) automatically applies these rules to every extraction. You can override or extend them via `--system-prompt`:

1. **Extract ALL visible text** exactly as it appears
2. **Preserve original language**, special characters, and diacritics
3. **Use markdown formatting** (tables, headers, lists) where appropriate
4. **Mark unclear text** with `[unclear: best_guess]`
5. **Note blank pages** — if the page is blank or contains only illustrations, say so
6. **No commentary** — output ONLY the extracted text and structure
7. **TOC JSON heading hierarchy** — if a TOC JSON is provided, use it to assign correct `<h>` tag levels (`#`, `##`, `###`, ...). The JSON has nested `title`/`pdf-page-no`/`children` structure. Depth 0 = `#`, depth 1 = `##`, etc. Match titles against the `title` field; use `pdf-page-no` only for page location (it's the actual PDF page number, not the printed one)
8. **Use `<table>` elements** as much as possible for structured data
9. **One column per category** — when listing words, do NOT create multi-column side-by-side tables
10. **Semantic line breaks** — do NOT mechanically mirror visual line breaks from the printed page. Lines that wrap due to page width belong to the same paragraph and must be joined into a single markdown line. Use reasoning to decide where genuine structural breaks occur (new paragraph, list item, table row, heading, etc.). When a hard line break IS appropriate within a block (e.g., between list items, dialogue lines, or distinct entries that are not separate paragraphs), add two trailing spaces at the end of the line to force a proper `<br>` break.
11. **Preserve formatting** — apply bold, italic, underline exactly as displayed
12. **`<tl>` wrapper** — target language text should be wrapped with `<tl>text</tl>`
13. **Ignore headers and footers** — running page numbers, document titles, chapter banners
14. **Image descriptions** — add simple minimal descriptions for images/diagrams/illustrations. For complex figures (diagrams, charts, maps, anatomical illustrations, mathematical figures, flowcharts, architectural drawings) that cannot be accurately described in text, the model flags them with `![FIGURE: description](extract://PAGENO-NN/bbox:x1,y1,x2,y2)` and they are automatically cropped and saved as PNG files.
15. **No LaTeX arrows** — NEVER use LaTeX math syntax (`$\rightarrow$`, `$\leftarrow$`, `$\uparrow$`, `$\downarrow$`) for arrows or symbols. Use plain Unicode: `→`, `←`, `↑`, `↓`, `⇒`, `⇐`, `↔`. Only use LaTeX if the original document is a LaTeX/math paper and the user explicitly requests it.

These rules are **appended to** (not replaced by) any custom `--system-prompt` you provide.

## System Prompts: The Secret Weapon

The `--system-prompt` parameter lets you teach the model about your document before extraction. This dramatically improves accuracy for:

- **Special characters**: "This document uses medieval Latin abbreviations: ͙, ̅, ̾"
- **Romanization**: "The romanization system uses ğ, ħ, ž, ş, ç"
- **Language context**: "This is a 19th-century German physics text with Fraktur script"
- **Layout hints**: "Tables have no borders; columns are separated by whitespace"
- **Content type**: "This is a bilingual Korean-English legal contract"

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
  --background            Run in background (default: false, use --background to enable)
  --no-background         Run in foreground (attached to terminal)
  --no-extract-images     Disable automatic extraction of complex images/diagrams
  --images-dir DIR        Directory to save extracted images (default: <output_dir>/images/)
  --log-file PATH         Log file for background mode (default: <output_dir>/<pdf>_ocr.log)
  --pid-file PATH         PID file for background mode (default: <output_dir>/<pdf>_ocr.pid)
  --notify-on-complete    Send completion notification (default: false, use --notify-on-complete to enable)
  --no-notify-on-complete Do not send a completion notification
  --quiet                 Minimal output
  --help                  Show this help
```

## Examples

### Example 1: Blurry old textbook with special characters

```bash
python scripts/batch_ocr.py ./turkish-grammar-1920.pdf \
  --system-prompt "Ottoman Turkish grammar book. Special letters: ğ (g-breve), ı (dotless i), ş (s-cedilla), ç (c-cedilla), ö, ü. Preserve ALL diacritics. Footnotes appear in smaller font at bottom of page." \
  --dpi 300 \
  --output-dir ./extracted/
```

### Example 2: Language textbook with custom Latin transliteration

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

**Why this works:** The model receives the page as an image and can use spatial/layout cues (indentation, column position, boldface in the original) to distinguish Arabic from English. Text-based extraction (`pdftotext`) loses these cues and fails on words like `chinn-` or `farg` that have no special characters.

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

**Why this works:** The model receives the page as an image and can use spatial/layout cues (indentation, column position, boldface in the original) to distinguish Arabic from English. Text-based extraction (`pdftotext`) loses these cues and fails on words like `chinn-` or `farg` that have no special characters.

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

**Sinhala-specific patterns to know:**
- Code-mixed sentences: English noun + Sinhala suffix (e.g., `Car eka`, `Call karanawa`, `Ready dha?`)
- Pronunciation charts: consonant clusters (dh/d, th/t) and vowel length (ae/aa, ii/uu)
- See `references/sinhala-textbook-extraction.md` for full session notes including observed page types and quality observations.

### Example 4: Language textbook — full-text extraction preserving layout (Sinhala)

When you need ALL text organized as it appears on the page — not just transliteration — use a full-text system prompt with explicit layout preservation instructions. This produces a readable study guide rather than a word list.

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

**When to use full-text vs. transliteration-only:**
- **Transliteration-only**: Building vocabulary lists, flashcards, or searchable word indexes. Produces clean, compact output.
- **Full-text**: Creating a readable study guide, wiki import, or structured lesson reference. Preserves pedagogical context and relationships between English explanations and Sinhala examples.

**Chunk sizing for full-text:** 100-page chunks work well as a sweet spot — ~15-20 minutes per chunk, frequent checkpoints, easy to parallelize. See `references/sinhala-textbook-extraction.md` for parallel execution patterns.

### Example 4b: Native-script Sinhala book — no translation, no `<tl>` tags

When the source material is written **entirely in Sinhala script** (සිංහල) and the user wants the raw text preserved without any translation wrappers or `<tl>` tags:

```bash
python scripts/batch_ocr.py ./sinhala-native-script-book.pdf \
  --system-prompt "This is a Sinhala language book written almost entirely in Sinhala script (සිංහල). Extract ALL text exactly as it appears, preserving the original Sinhala script precisely. Do NOT translate anything into English. Do NOT use the <tl> tag wrapper. Preserve all Sinhala characters, diacritics, and punctuation exactly as they appear in the original. Use markdown formatting (tables, headers, lists) where appropriate to reflect the visual structure of the page. Ignore page numbers, running headers, and footers. Mark unclear text with [unclear: best_guess]. If a page is blank or contains only illustrations, note it. Output ONLY the extracted text and structure — no commentary." \
  --output-dir ./extracted/ \
  --model gemini-3-flash-preview:cloud
```

**Key differences from transliteration extraction:**
- Output is pure Sinhala script (සිංහල), not Latin transliteration
- No `<tl>` tags — the default rule #12 (wrap target language in `<tl>`) is explicitly disabled
- No English translation mixed in — the book itself is monolingual Sinhala
- Model must correctly render complex Sinhala conjuncts and diacritic combinations

### Example 5: Multilingual academic paper

```bash
python scripts/batch_ocr.py ./bilingual-paper.pdf \
  --system-prompt "Academic paper with Korean and English. Korean text uses standard Hangul. Mathematical equations use LaTeX-style notation. Tables use tabular layout." \
  --backend openrouter \
  --model google/gemini-3.1-pro-preview
```

### Example 6: Grammar book with TOC JSON for heading hierarchy

When you have a structured grammar book (or any document with a known table of contents), embed the TOC directly into the system prompt. This ensures the model assigns correct markdown heading levels (`#` through `#####`) based on the document's actual hierarchy.

**Preparing the TOC:**
1. Obtain or create a TOC JSON with nested `title`, `pdf-page-no`, and `children` fields
2. Clean any Unicode escapes (`\uXXXX` → actual characters) so the model can match titles
3. Flatten to a compact "Page N: ## Title" format
4. Append the compact TOC to the system prompt under a "TABLE OF CONTENTS REFERENCE" section

```bash
python scripts/batch_ocr.py ./spoken-sinhala-grammar.pdf \
  --pages 16-117 \
  --system-prompt "This is a grammar book of spoken Sinhala. Sinhala language texts are mostly romanized (Latinized).

IMPORTANT: All (Latinized) Sinhala text must be written in ITALICS (*text*).

The special letters for romanization used here are: æ, ā, à, ǣ, ī, ū, ē, ō, ń, ḿ, ṅ, ñ, ṇ, ḍ, ṭ, ḷ, ś, ṣ, ŋ. The symbol combination V̄ (V + macron) is used to denote a long vowel.

Superscript letters are often used throughout the book for reference — preserve them as regular text (e.g., x², H²) or using HTML sup tags if needed.

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

**Key points for TOC-integrated extraction:**
- The model matches section titles against the TOC `title` field and uses the indicated heading level
- `pdf-page-no` is the **actual PDF page number** (not the printed page number)
- Depth 0 = `#`, depth 1 = `##`, depth 2 = `###`, depth 3 = `####`, depth 4 = `#####`
- If the TOC JSON contains Unicode escapes (e.g., `\u014dn\u00e0`), clean them to actual characters (e.g., `ōnà`) before embedding — otherwise the model cannot match titles

### Example 7: Language textbook with diacritic stripping — Fijian (Bauan)

When the source material uses macrons (long vowel marks: ā, ē, ī, ō, ū) but you want the output written as plain Latin letters (a, e, i, o, u), explicitly instruct the model to **ignore macrons entirely**. This is common for language learners who want searchable plain-ASCII vocabulary.

```bash
python scripts/batch_ocr.py ./spoken-fijian-textbook.pdf \
  --pages 53-270 \
  --system-prompt "This is a Fijian language textbook (Bauan Fijian). The text contains Fijian words and phrases mixed with English instructional text, grammar notes, and translations.

IMPORTANT DIACRITIC RULE: The Fijian text uses macrons (long vowel marks) over vowels: ā, ē, ī, ū, ō. You must COMPLETELY IGNORE these macrons and write the letters WITHOUT the macron mark. For example, 'bāravi' must be written as 'baravi', 'lēsoni' as 'lesoni', 'mākete' as 'makete', 'tū' as 'tu', 'vō' as 'vo'. Treat macron-vowels exactly like their plain counterparts: a, e, i, o, u. NEVER output ā, ē, ī, ō, ū in the extracted text.

FIJIAN TEXT MARKING:
All Fijian language text must be wrapped with <tl> tags. This includes:
- Fijian words and phrases in dialogues
- Fijian words in vocabulary lists
- Fijian words in repetition and variable slot exercises
- Fijian words in grammatical examples
- Any Fijian text that is NOT English instructional text

English instructional text, grammar explanations, section headers, and translations should NOT be wrapped in <tl> tags.

DIALOGUE FORMATTING:
Format dialogue lines as:
> **A** <tl>Fijian text here</tl>
> English translation here

VOCABULARY LIST FORMATTING:
- Vocabulary lists show Fijian words with English definitions
- Format as markdown tables with | Fijian | English |
- Keep multi-line entries together as a single row
- Wrap Fijian words in <tl> tags

STRUCTURE TO PRESERVE:
- Lesson headers as # Lesson X
- Section numbers as ## X.Y Title
- Dialogue headers as ### Dialogue
- Repetition headers as ### Repetition
- Vocabulary headers as ### Vocabulary
- Exercise headers as ### Exercise

IGNORE page numbers, running headers like 'FIJIAN' at the top of pages, and footnote reference numbers (superscript numbers like ¹, ², ³, ⁴).

Use markdown formatting to reflect the visual hierarchy of the page. Bold for emphasized words. Tables for vocabulary lists and structured content." \
  --output-dir ./extracted_fijian_lessons/ \
  --output-name "fijian_lessons_1-15_ocr.md" \
  --model gemini-3-flash-preview:cloud \
  --dpi 250
```

**Key points for diacritic stripping:**
- The instruction must be **explicit and repeated** — "NEVER output ā, ē, ī, ō, ū" — because VLMs sometimes preserve visual diacritics by default
- Always verify the first few pages for stray macrons before committing to a large batch
- The `<tl>` tag wrapper (default rule #12) works well for marking target-language text separately from English instructional text

### Example 8: Resume after crash

```bash
python scripts/batch_ocr.py ./500-page-archive.pdf \
  --system-prompt "19th century French administrative documents. Use of long s (ſ) and archaic spellings." \
  --resume
```

## Output Format

### Markdown (`<name>_ocr.md`)

The output is a **single merged markdown file** containing all extracted pages. This file includes `## Page N` markers between pages and preserves the structure detected by the vision model.

**Important:** If you need per-chapter files (e.g., one file per unit), you must post-process the merged output. See the `pdf-textbook-parser` skill's "Post-Processing: Splitting Merged Vision OCR Output" section for the splitting technique and a production-ready script.

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

---

## Page 25

### Figure 2.3: Vowel Harmony Diagram

![Vowel harmony flowchart](images/025-01.png)

The diagram above illustrates the two-way and four-way vowel harmony rules...
```

### Extracted Images (`images/` subdirectory)

When the vision model flags a complex figure (diagram, chart, map, etc.), the system:

1. **Detects** the `extract://` tag in the VLM output: `![FIGURE: description](extract://PAGENO-NN/bbox:x1,y1,x2,y2)`
2. **Crops** the region from the original PDF page using PyMuPDF at 300 DPI (or higher if `--dpi` is set above 300)
3. **Saves** the cropped image as PNG in the `images/` directory (or `--images-dir` if specified)
4. **Rewrites** the markdown reference to point to the saved file

**Filename format:** `[PAGENO]-[SEQ].png` with dynamic zero-padding based on total page count:
- 1–9 pages: `1-01.png`, `2-01.png`
- 10–99 pages: `01-01.png`, `25-03.png`
- 100–999 pages: `001-01.png`, `025-04.png`
- 1000+ pages: `0001-01.png`, etc.

**Example directory structure:**
```
extracted/
├── textbook_ocr.md
└── images/
    ├── 025-01.png
    ├── 025-02.png
    ├── 047-01.png
    └── 128-01.png
```

To disable image extraction, use `--no-extract-images`. To specify a custom directory, use `--images-dir ./my_figures/`.

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
    },
    ...
  ]
}
```

## How It Works

```
[PDF] 
  ↓  PyMuPDF renders each page to PNG (200 DPI)
[Page Image]
  ↓  Send to VLM with system prompt + image
[Vision Model]
  ↓  Returns extracted markdown text
  ↓  (If complex figures detected) Flags them with extract://PAGENO-NN/bbox:x1,y1,x2,y2
[Image Extractor]
  ↓  PyMuPDF crops the flagged region at 300+ DPI
[Output] 
  ↓  Concatenate all pages into single markdown file + saved PNG crops in images/
```

## Rate Limiting

To respect API rate limits and stay under **30 requests per minute**, a **minimum 2-second delay** is enforced between page requests. This is hardcoded — you cannot set `--delay` below 2.0.

| Backend | Approximate Speed |
|---------|------------------|
| Ollama Cloud | ~2-4s per page + 2s delay = ~4-6s/page |
| OpenRouter | Varies by model |
| Gemini | Varies by model |

For a 100-page document, expect **~10-15 minutes** total processing time.

## Large-Batch Processing Strategy

For documents with 200+ pages, consider these approaches to manage time and API load:

### Option A: Background mode with notification (opt-in)

Use `--background` and `--notify-on-complete` to detach the process so it survives SSH disconnects, and receive an alert when it completes.

```bash
# Run in background with notification
python scripts/batch_ocr.py ./textbook.pdf --pages 1-500 \
  --background \
  --notify-on-complete
```

Monitor with `tail -f ./textbook_ocr.log`. The job continues even if you disconnect.

**Opt-in:**
- `--background` — run in background
- `--notify-on-complete` — send completion alert

**Background mode features:**
- Detaches from terminal completely (new session)
- Log file captures all output with timestamps
- PID file for easy process management
- Duplicate job prevention (won't start if already running)
- Resume supported: include `--resume` to continue from checkpoint
- **Completion notification** sent via Hermes gateway IPC socket or JSON fallback
- Default log file: `<output_dir>/<pdf>_ocr.log`
- Default PID file: `<output_dir>/<pdf>_ocr.pid`

### Option B: Chunked batches with explicit pause points (recommended for 400+ pages)

Process in chunks of 50–100 pages, review quality, then continue. This prevents API overload and lets you validate output before committing the full document:

```bash
# Batch 1: validate approach on small sample
python scripts/batch_ocr.py ./textbook.pdf --pages 1-50 --output-name textbook_p1-50.md

# Review output, then continue in chunks
python scripts/batch_ocr.py ./textbook.pdf --pages 51-150 --output-name textbook_p51-150.md
python scripts/batch_ocr.py ./textbook.pdf --pages 151-250 --output-name textbook_p151-250.md
# ... etc
```

**Why chunk:** Vision OCR runs at ~4-6 seconds per page. A 500-page document takes ~45-60 minutes. Chunking lets you:
- Validate quality early (catch prompt issues before page 400)
- Prevent API rate-limit or connection timeout issues
- Pause/resume without losing progress
- Run multiple chunks in parallel (see Option C)

**Chunk size guidance:**
- 50 pages: ~5-7 minutes, good for initial validation
- 100 pages: ~15-20 minutes, **recommended sweet spot** for parallel execution (good throughput + frequent checkpoints)
- 150+ pages: ~20-30 minutes, only after approach is validated

### Option C: Parallel chunk execution (fastest for large documents)

Launch multiple non-overlapping chunks simultaneously as background processes. Each chunk writes to its own output file:

```bash
# Chunk A
python scripts/batch_ocr.py ./textbook.pdf --pages 1-100 --output-name textbook_p1-100.md --background

# Chunk B (different page range, different output file)
python scripts/batch_ocr.py ./textbook.pdf --pages 101-200 --output-name textbook_p101-200.md --background

# Chunk C
python scripts/batch_ocr.py ./textbook.pdf --pages 201-300 --output-name textbook_p201-300.md --background
```

**Critical requirements for parallel execution:**
- Each chunk must use **different `--pages` ranges** (no overlap)
- Each chunk must use **different `--output-name` files** (no collision)
- Same `--system-prompt`, `--backend`, and `--model` across all chunks
- Monitor with `tail -f` on each log file
- Combine outputs after all chunks finish: `cat textbook_p*.md > textbook_full.md`

**Note on page range gaps:** If you process chunk 1 as pages 1-50 for validation, then chunk 2 as 101-230, you are intentionally skipping pages 51-100. This is fine if those pages are known to be English-only (table of contents, instructions). Always verify the document structure before deciding which pages to skip.

**When to use parallel:** When you need a 400+ page document processed quickly and the system prompt is already validated. A 493-page document splits into 5 chunks of ~100 pages each and finishes in ~15-20 minutes total (vs. ~50 minutes serial).

### Option D: Background with checkpoint monitoring
Launch as a background process and monitor the checkpoint file:

```bash
# Start the job
python scripts/batch_ocr.py ./textbook.pdf --pages 1-500 --background --log-file ./ocr.log

# Monitor progress
watch -n 10 'python3 -c "import json; cp=json.load(open(\".textbook_ocr_checkpoint_*.json\")); print(f\"Completed: {len(cp[\\\"completed_pages\\\"])}\")"'
```

The checkpoint file (`.<pdf>_ocr_checkpoint_<hash>.json`) updates after every page. You can kill the process anytime and resume with `--resume`.

### Option F: Hermes terminal with background=true (most reliable for very long jobs)

When you need to process hundreds of pages without the 600s Hermes foreground timeout, use Hermes' `terminal(background=true, notify_on_complete=True)`:

```python
# From Hermes agent or execute_code
terminal(
    command="python scripts/batch_ocr.py ./textbook.pdf --pages 53-270 --resume",
    background=True,
    notify_on_complete=True,
    timeout=600  # 10 min max for foreground, but background has no limit
)
```

**Advantages over native `--background`:**
- No timeout limit (background processes run until completion)
- Automatic notification when done
- Hermes tracks the process lifecycle
- No silent fork failures

**Chunking with this approach:**
Since even background mode can be interrupted by system events, process in ~50-page chunks and use `--resume` to continue:

```bash
# Chunk 1: pages 53-100
python scripts/batch_ocr.py ./textbook.pdf --pages 53-270
# (wait for notification, then...)

# Chunk 2: pages 101-150
python scripts/batch_ocr.py ./textbook.pdf --pages 53-270 --resume
# (wait for notification, then...)

# Chunk 3: pages 151-200
python scripts/batch_ocr.py ./textbook.pdf --pages 53-270 --resume
# ... etc
```

Each chunk uses the SAME `--pages` range (`53-270`) so the checkpoint hash stays constant and `--resume` works correctly.

See `references/fijian-textbook-extraction.md` for a complete session reproduction using this pattern.

### Option E: Pause at a specific page
If you need to stop at a specific page (e.g., to prevent overload or review intermediate results), simply kill the process. The checkpoint preserves all progress up to the last completed page. Resume later with `--resume` or process the remaining range explicitly:

```bash
# Processed 1-230, now continue from 231
python scripts/batch_ocr.py ./textbook.pdf --pages 231-493 --resume
```

**Important:** When resuming, use the SAME `--pages` range as the original run to ensure the checkpoint hash matches. If you originally ran with `--pages 1-500`, resume with `--pages 1-500 --resume`, not `--pages 231-500 --resume`. The latter creates a new checkpoint file and starts from scratch.

## Post-Processing: Splitting into Per-Chapter Files

After OCR produces a single merged markdown file, you may want to split it into per-chapter or per-lesson files. This requires:

1. **Knowing the page-to-chapter mapping** — either from the PDF's table of contents or by inspecting page content
2. **Splitting the merged output** — extracting page ranges into separate files

### Manual splitting with checkpoint data

If you have the checkpoint JSON (`.<pdf>_ocr_checkpoint_<hash>.json`), you can extract specific page ranges programmatically:

```python
import json

# Load checkpoint
with open('.textbook_ocr_checkpoint_abc123.json', 'r') as f:
    cp = json.load(f)

# Extract pages for a specific lesson/chapter
lesson_pages = range(53, 60)  # Lesson 1: pages 53-59
lesson_content = []
for p in lesson_pages:
    p_str = str(p)
    if p_str in cp['results']:
        lesson_content.append(f"## Page {p}\n\n{cp['results'][p_str]}")

# Write lesson file
with open('lesson_01.md', 'w') as f:
    f.write('# Lesson 1\n\n')
    f.write('\n\n'.join(lesson_content))
```

### Automated splitting by TOC

For textbooks with a known table of contents, map book page numbers to PDF page numbers (usually PDF page = book page + offset), then split:

```python
import json, os

# Load combined checkpoint (merged from multiple runs if needed)
with open('combined_results.json', 'r') as f:
    results = json.load(f)

# Lesson ranges (PDF page numbers)
lesson_ranges = {
    1: (53, 59), 2: (60, 68), 3: (69, 80), 4: (81, 91),
    5: (92, 102), 6: (103, 115), 7: (116, 127), 8: (128, 139),
    9: (140, 150), 10: (151, 163), 11: (164, 178), 12: (179, 190),
    13: (191, 204), 14: (205, 219), 15: (220, 234),
}

output_dir = './lessons'
os.makedirs(output_dir, exist_ok=True)

for lesson_num, (start, end) in lesson_ranges.items():
    lesson_content = []
    for p in range(start, end + 1):
        p_str = str(p)
        if p_str in results:
            lesson_content.append(f"## Page {p}\n\n{results[p_str]}")
    
    with open(f'{output_dir}/lesson_{lesson_num:02d}.md', 'w') as f:
        f.write(f'# Lesson {lesson_num}\n\n')
        f.write('\n\n'.join(lesson_content))
```

**Note:** The `pdf-textbook-parser` skill also provides a splitting script for vision OCR output. See that skill for a production-ready implementation.

## Integration with Wiki Pipeline

After extraction, ingest into your knowledge base:

```bash
# Option 1: Direct to wiki
synthadoc ingest -w my-knowledge ./extracted/turkish-grammar-1920_ocr.md

# Option 2: Via OpenDataLoader (for structure preservation)
bash ~/.hermes/skills/data-science/opendataloader-pdf/scripts/ingest_to_synthadoc.sh \
  ./extracted/turkish-grammar-1920_ocr.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No API key found" | Add `OLLAMA_API_KEY=...` to `~/.hermes/.env` |
| `ModuleNotFoundError: No module named 'fitz'` | Install PyMuPDF: `pip install pymupdf` |
| Text is garbled/missing | Increase `--dpi` to 300 or higher |
| Model misses special chars | Make them **explicit** in `--system-prompt` |
| Model hallucinates characters / drops diacritics | Switch to `gemini-3-flash-preview:cloud` — see Model Selection section above |
| Page headers leak into output | Add "IGNORE page numbers and running headers" to system prompt |
| Vocabulary tables split incorrectly | Add explicit "Keep ALL vocabulary entries in ONE continuous table" instruction |
| TOC JSON has `\uXXXX` escapes | Clean with `python -c "import json; print(json.dumps(json.load(open('toc.json')), ensure_ascii=False))"` before embedding |
| Model assigns wrong heading levels | Embed the TOC directly in the system prompt with explicit "Page N: ## Title" format — see Example 6 |
| Rate limit errors | Already handled — minimum 2s delay enforced |
| Processing too slow | This is expected for vision OCR (~4-6s/page). For 200+ pages, see Large-Batch Processing Strategy |
| Pages fail repeatedly | Try `--backend openrouter` with different model |
| Resume not working / creates new checkpoint | **Critical:** The checkpoint hash includes the `--pages` range string. Changing `--pages` (e.g., from `53-270` to `110-270`) generates a **different checkpoint file** and resumes from scratch. **Always use the same `--pages` range when resuming.** To fill gaps, process the missing range with the SAME `--pages` value, or manually merge checkpoint JSONs by combining `completed_pages` and `results` dicts. See `references/fijian-textbook-extraction.md` for a detailed reproduction of this pitfall. |
| Need to merge multiple checkpoints | When different `--pages` ranges create separate checkpoints, merge them programmatically: `python3 -c "import json; d1=json.load(open('checkpoint_a.json')); d2=json.load(open('checkpoint_b.json')); merged={'completed_pages': list(set(d1['completed_pages']) | set(d2['completed_pages'])), 'results': {**d1['results'], **d2['results']}}; json.dump(merged, open('combined.json','w'))"`. Then resume with the original `--pages` range. |
| Background job dies immediately after launch | **Pitfall:** The native `--background` mode can fail silently. Use `terminal(background=true)` from Hermes, or run in a `screen`/`tmux` session. The subprocess fork sometimes exits before processing begins. See `references/fijian-textbook-extraction.md` for session reproduction. |
| Background job won't start ("already running") | Check PID file and kill stale process, or delete the PID file manually |
| Terminal timeout kills long OCR jobs | Hermes `terminal()` has a hard 600s (10 minute) foreground timeout. For vision OCR at ~4-6s/page, this limits each run to ~25-30 pages. **Workaround:** Use `terminal(background=true, notify_on_complete=True)` — no timeout limit. Or chunk into 25-page batches. See `references/fijian-textbook-extraction.md` for chunking strategy. |
| No completion notification received | Check that gateway is running (`hermes gateway status`); fallback JSON is written next to output |
| Lost SSH connection during long job | Use `--background` to detach, or run in `screen`/`tmux` |
| LaTeX arrows in output (`$\rightarrow$`, etc.) | This should not happen with current default prompt (rule #15). If it does, post-process: `sed -i 's/\$\\rightarrow\$/→/g; s/\$\\leftarrow\$/←/g; s/\$\\uparrow\$/↑/g; s/\$\\downarrow\$/↓/g' file.md` |
| Images not being extracted | Ensure `--no-extract-images` is not set. Check that the VLM is outputting `extract://` tags in the markdown. Complex figures must be flagged by the model — simple decorative images are intentionally skipped. |
| Extracted images are blurry or low quality | Increase `--dpi` (default 200, crops use `max(dpi, 300)`). Use `--dpi 400` or higher for detailed diagrams. |
| Image files have wrong names | Filenames use dynamic zero-padding based on total page count (e.g., `025-04.png` for 100–999 pages). This is expected behavior. |

## Advanced: Programmatic Usage

```python
from scripts.vision_ocr import VisionPDFProcessor

processor = VisionPDFProcessor(
    backend="ollama",
    model="gemini-3-flash-preview:cloud",
    system_prompt="This is a medieval Latin manuscript...",
    dpi=300,
    delay=2.0,  # minimum 2.0s enforced to stay under 30 RPM
    extract_images=True,        # Enable automatic image extraction (default: True)
    images_dir="./my_figures",  # Custom directory for extracted images
)

result = processor.process_pdf(
    "manuscript.pdf",
    output_path="manuscript_ocr.md",
    pages="1-50",
)

print(f"Processed {result.pages_processed} pages")
```

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `OLLAMA_API_KEY` | Ollama backend | Your Ollama Cloud API key |
| `OPENROUTER_API_KEY` | OpenRouter backend | Your OpenRouter key |
| `GEMINI_API_KEY` | Gemini backend | Google Gemini API key |
| `VISION_OCR_NOTIFY` | Notification system | Set to `1` by background launcher to enable completion alerts in child process |
| `HERMES_PLATFORM` | Notification routing | Platform name for gateway delivery (e.g., `telegram`) |
| `HERMES_CHAT_ID` | Notification routing | Chat ID for routing completion alerts |
| `HERMES_THREAD_ID` | Notification routing | Thread ID for routing completion alerts |

## References
- `references/fijian-textbook-extraction.md` — Fijian (Bauan) language textbook OCR: macron stripping (ā→a, ē→e, ī→i, ō→o, ū→u), `<tl>` tag wrapping for Fijian text, dialogue/vocabulary/repetition drill formatting, checkpoint hash pitfall with `--pages`, background mode failure workaround, terminal timeout chunking strategy, checkpoint merging technique, and per-lesson file splitting
- `references/gulf-arabic-textbook-extraction.md` — Complete extraction pattern for Latin-transliterated Arabic textbooks: system prompt template, model comparison (gemini-flash vs gemma4), vocabulary table formatting rules, and 2-page test protocol
- `references/test-results-palestinian-arabic.md` — Real-world validation: 29-page Palestinian Arabic textbook extracted with 100% character preservation (68 ī, 64 š, 54 ē, 49 ʿ, etc.)
- `references/sinhala-textbook-extraction.md` — Sinhala language learning materials: extracting Latin-alphabet transliteration from mixed English-Sinhala slide-based PDFs, handling Sinhala script alongside, code-mixed sentences, and pronunciation chart fragments
- `references/sinhala-native-script-extraction.md` — Native-script Sinhala OCR session notes: system prompt for pure Sinhala script extraction without `<tl>` tags or translation, LaTeX arrow pitfall (`$\rightarrow$` → Unicode `→`), observed page types, and quality observations
- `references/ollama-cloud-backend.md` — Why native API is used (not Hermes `vision_analyze`), tested models, and backend alternatives
- `references/vlm-guided-image-extraction.md` — VLM-guided image extraction architecture: two-stage pipeline (VLM detection + PyMuPDF cropping), bounding box tag format, dynamic zero-padding filename convention, and implementation details
- `references/image-extraction-feature-validation.md` — Real-world validation of the image extraction feature on a 186-page Portuguese textbook (pages 64–69), including observed extraction behavior, filename format verification, and CLI testing notes
- `references/skills-sh-ocr-research.md` — Skills.sh research findings that led to this skill's creation; comparison with skills.sh OCR skills; DeepSeek API limitations
- `references/adding-a-new-backend.md` — Step-by-step recipe for adding a new vision API backend (e.g., OpenAI, Anthropic) to the OCR pipeline: class template, registration, CLI wiring, provider format cheat sheet, and common pitfalls
- `references/cli-background-mode-pattern.md` — Background mode implementation pattern: detached process, PID file, log file, completion notification via gateway IPC socket

## Notes

- Ollama Cloud uses the **native `/api/chat` endpoint**, not the `/v1` proxy, due to Hermes bug #23422
- The default `gemini-3-flash-preview:cloud` model is fast, cheap, and excellent at multilingual OCR
- For very blurry scans, increase `--dpi` to 300+ and add explicit character hints in `--system-prompt`
- The checkpoint file is hidden (`.<name>_ocr_checkpoint_<hash>.json`) in the output directory
- This skill was created because existing tools (Tesseract, marker-pdf) failed on muffled fonts, and skills.sh skills lacked the system-prompt customization needed for special-character documents
- For a complete inventory of PDF/OCR tools already installed on this system, see `ocr-and-documents` skill's `references/hermes-pdf-tool-inventory.md`
- **Vision OCR beats text extraction for custom romanization:** When a PDF contains Latin-transliterated Arabic (or similar custom romanization systems), vision OCR with explicit character instructions in the system prompt produces dramatically better results than text-based extraction (pdftotext + regex heuristics). Text-based approaches fail because they cannot distinguish Arabic words without special characters (e.g., "chinn-", "farg", "tist") from English words.
