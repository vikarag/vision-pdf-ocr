# Gulf Arabic Textbook Extraction Pattern

Session: 2026-05-12
Source: "Colloquial Arabic of the Gulf" by Clive Holes (461 pages)

## Problem

Textbook uses custom Latin transliteration for Gulf Arabic with special characters:
- `9` = ع (ayn), `H` = ح (ha), `S` = ص (sad), `T` = ط (ta), `D` = ض (dad), `DH` = ظ (dha)
- `x` = خ (kha), `gh` = غ (ghayn), `q` = ق (qaf), `ʼ` = hamza
- Stress marks: `á`, `í`, `ú` — long vowels: `aa`, `ii`, `oo`, `uu`

Text-based extraction (`pdftotext` + regex) fails because:
1. Cannot distinguish Arabic words without special chars (`chinn-`, `farg`, `tist`) from English words
2. Two-column vocabulary layout is lost
3. Multi-line entries (Arabic word on line 1, English definition on line 2) are split incorrectly
4. Slash-separated forms (`máraD/yímraD/máraD`) get broken apart

## Solution: Vision OCR with Explicit System Prompt

### Model Selection

| Model | Result |
|-------|--------|
| `gemini-3-flash-preview:cloud` | ✅ Excellent character fidelity, proper vocabulary tables, correct bolding |
| `gemma4:31b-cloud` | ❌ Hallucinates characters (`d`→`C`, `j`→`i`, `9`→`g`), drops stress marks, invents forms |

**Always test 2 pages before bulk processing.** Character errors in language materials are costly to fix retroactively.

### System Prompt Template

```
This is a Gulf Arabic language textbook. IGNORE any page numbers and running headers like 'Unit X' or '310' at the top of pages - do not include them in the output.

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
- Reading Arabic sections as ### Reading Arabic
```

### Batch Processing Strategy

For large documents (400+ pages), process in 100-page chunks to avoid timeout issues:

```bash
# Chunk 1: pages 1-100
python scripts/batch_ocr.py textbook.pdf --pages 1-100 --system-prompt "..." --output-name p1_100.md

# Chunk 2: pages 101-200
python scripts/batch_ocr.py textbook.pdf --pages 101-200 --system-prompt "..." --output-name p101_200.md

# Use --resume if a chunk times out
python scripts/batch_ocr.py textbook.pdf --pages 101-200 --system-prompt "..." --output-name p101_200.md --resume
```

Each chunk takes ~10-15 minutes. The `--resume` flag skips already-processed pages.

### 2-Page Test Protocol

Before any bulk run, test with:
1. **Dialogue page** — verify speaker labels, inline bolding, mixed English-Arabic lines
2. **Vocabulary page** — verify single continuous table, slash forms preserved, parenthetical additions kept

Check for these specific failure modes:
- Page headers leaking through ("Unit 19", "310")
- Split vocabulary tables
- Missing bold on words without special chars (`chinn-`, `farg`)
- Character hallucinations (`báCalan` instead of `bádalan`)
- Dropped stress marks (`killmaa` instead of `kíllmaa`)

### Results

- 461 pages processed in 5 chunks
- 0 failed pages
- Total output: ~808 KB across 5 files
- Character fidelity: 100% with gemini-3-flash-preview:cloud
