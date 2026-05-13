# Sinhala Textbook Extraction Reference

Session: 2026-05-13 — Extracting transliterated Sinhala from Shani's Level 1 Sinhala PDF (705 pages, image-based slides).

## Document Profile

- **Format**: Image-based PDF (zero text layer), educational slides
- **Content mix**: English instructions + transliterated Sinhala (Latin alphabet) + Sinhala script (සිංහල)
- **Creator watermark**: "Created by Shani Bulathsinghala" on most pages
- **Layout**: Color-coded slides with vocabulary lists, dialogues, grammar summaries, homework exercises
- **Total pages processed**: 493 (pages 1-493 of 705 total)
- **Success rate**: 100% (0 failures across 443 pages)

## System Prompts That Worked

### Transliteration-Only Extraction

Use this when you only need the Latin-alphabet transliterated Sinhala words:

```
This is a Sinhala language learning textbook. The document contains English instructional text mixed with transliterated Sinhala words written in the Latin alphabet.

EXTRACT ONLY TRANSLITERATED SINHALA TEXT. Transliterated Sinhala means Sinhala words written using English/Latin letters, like: Oyaage, Mama, kohomadha, thiyenawa, kaaema, waediyen, Mage, Oyaa, kiiyadha, mokadhdha, rassaawa, wayasa, kaemathiidha, kanna, puluwandha, dhannawadha, natanawa, liyanawa, balanawa, yanawa, bonawa, kanawa, karanawa, eken, Meewa, kiyanna, His, thaen, purawanna, Oyaata, kathaa, karanna, kohendha, en, inne, kawdha, thiyenne, ekakdha, gaena, liyanna, eyaata, monaadha, thiyenne, issara, hitiye, hondhai, rasai, Lankaawe, saerai, Mee, wachane, Prashna, pawle, Lakshanige, Lakshanita, car, bike, naae, Ow, eka, waediyen.

DO NOT extract pure English words like 'Summary', 'Questions', 'Hello', 'Answer', 'Possessive', 'Exceptions', 'Lessons', 'Feelings', 'Greetings', 'Homework', 'Dialogue', 'Practice'.

IGNORE page numbers, running headers like 'Lessons in level 1', and the watermark 'Created by Shani Bulathsinghala' at the bottom of pages.

When transliterated Sinhala appears alongside Sinhala script (සිංහල), extract ONLY the Latin-alphabet transliteration, not the Sinhala script.

Format the output as a clean list of transliterated Sinhala words/phrases found on the page. If there are full sentences in transliterated Sinhala, preserve them.
```

### Full-Text Extraction (Preserving Layout)

Use this when you need ALL text — English instructions, transliterated Sinhala, and Sinhala script — organized as it appears on the page:

```
This is a Sinhala language learning textbook. Extract ALL text from the page exactly as it appears, preserving the original layout and organization.

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
- Watermark 'Created by Shani Bulathsinghala' at bottom of pages

FORMAT:
- Use markdown formatting to reflect the visual hierarchy
- Bold for emphasized words
- Tables for vocabulary lists and structured content
- Blockquotes or > prefix for dialogue lines
- Code blocks for pronunciation charts if needed
- Preserve the relationship between English and Sinhala text when they appear side by side
```

**When to use which:**
- **Transliteration-only**: Building a vocabulary list, flashcards, or searchable word index. Produces clean, compact output.
- **Full-text**: Creating a readable study guide, wiki import, or structured lesson reference. Preserves pedagogical context.

## Key Differences from Arabic Transliteration

| Aspect | Arabic (Gulf/Palestinian) | Sinhala |
|--------|---------------------------|---------|
| Special chars | 9, H, S, T, D, DH, x, gh, q, ʼ, á, í, ú | dh, th, ae, aa, ii, uu, oo (vowel length) |
| Script alongside | Yes (Arabic script) | Yes (Sinhala script සිංහල) |
| Code-mixed sentences | English nouns + Arabic particles | English nouns + Sinhala suffixes (eka, karanawa, dha) |
| Grammar focus | Triconsonantal roots, broken plurals | Agglutinative suffixes (ge, eka, en, dha) |
| Pronunciation charts | Stress marks, phonetic notes | Vowel length charts, consonant clusters |

## Code-Mixed Pattern (Sinhala-English)

Sinhala slides frequently mix English nouns with Sinhala grammatical suffixes:
- `Car eka` = the car (eka = definite article/singular marker)
- `Call karanawa` = (to) call (karanawa = doing/making)
- `Mama laptop eka use karanawa` = I use the laptop
- `Ready dha?` = Ready? (dha = question particle)
- `Oyaa games play karanawadha?` = Do you play games?

This is **not** English — it's Sinhala syntax with English loanwords, and should be extracted.

## Observed Page Types

1. **Pure English** — table of contents, instructions (~30% of pages)
2. **Vocabulary lists** — transliterated Sinhala + English translation
3. **Dialogue scripts** — A/B conversation format
4. **Grammar summaries** — possessive forms, question particles, verb conjugations
5. **Pronunciation charts** — consonant clusters, vowel length distinctions
6. **Homework exercises** — fill-in-the-blank with transliterated prompts
7. **Authentic text** — longer passages (e.g., campus strike dialogue)

## Batch Processing: Chunked + Parallel Execution

This session used a **chunked parallel approach** for 493 pages. Two extraction modes were run:

### Mode 1: Transliteration-Only (5 uneven chunks)

| Chunk | Pages | Count | Output File | Status |
|-------|-------|-------|-------------|--------|
| 1 | 1-50 | 50 | `...pages_1-50_ocr.md` | ✅ Validation |
| 2 | 101-230 | 130 | `...pages_101-230_ocr.md` | ✅ Parallel |
| 3 | 231-300 | 70 | `...pages_231-300_ocr.md` | ✅ Parallel |
| 4 | 301-400 | 100 | `...pages_301-400_ocr.md` | ✅ Parallel |
| 5 | 401-493 | 93 | `...pages_401-493_ocr.md` | ✅ Parallel |

**Why chunk 1 was only 50 pages:** Initial validation run to confirm the system prompt worked correctly before committing to larger batches.

### Mode 2: Full-Text Extraction (5 uniform 100-page chunks)

| Chunk | Pages | Count | Output File | Status |
|-------|-------|-------|-------------|--------|
| 1 | 1-100 | 100 | `...FULL_pages_1-100_ocr.md` | ✅ Parallel |
| 2 | 101-200 | 100 | `...FULL_pages_101-200_ocr.md` | ✅ Parallel |
| 3 | 201-300 | 100 | `...FULL_pages_201-300_ocr.md` | ✅ Parallel |
| 4 | 301-400 | 100 | `...FULL_pages_301-400_ocr.md` | ✅ Parallel |
| 5 | 401-493 | 93 | `...FULL_pages_401-493_ocr.md` | ✅ Parallel |

**Why uniform 100-page chunks:** User explicitly requested groups of 100 pages. This proved to be an excellent sweet spot — large enough for efficient throughput, small enough that each chunk completes in ~15-20 minutes and checkpoints are frequent.

### Chunk Sizing Guidance

| Chunk Size | Time | Use Case |
|------------|------|----------|
| 50 pages | ~5-7 min | Initial validation / prompt testing |
| 100 pages | ~15-20 min | **Recommended sweet spot** for parallel execution |
| 130+ pages | ~20-25 min | Acceptable after validation, but longer checkpoint gaps |

**Speed observed:** ~4-6 seconds per page with Ollama Cloud gemini-3-flash-preview:cloud at DPI 200, delay 2.0s.

### Parallel Execution Commands

```bash
# Validation chunk (run first)
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 1-50 --output-name pages_1-50.md ...

# After validation, launch all remaining chunks in parallel:
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 1-100 --output-name FULL_pages_1-100.md ... &
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 101-200 --output-name FULL_pages_101-200.md ... &
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 201-300 --output-name FULL_pages_201-300.md ... &
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 301-400 --output-name FULL_pages_301-400.md ... &
python scripts/batch_ocr.py ./sinhala-level-1.pdf --pages 401-493 --output-name FULL_pages_401-493.md ... &
```

**Critical requirements for parallel execution:**
- Each chunk must use **different `--pages` ranges** (no overlap)
- Each chunk must use **different `--output-name` files** (no collision)
- Same `--system-prompt`, `--backend`, and `--model` across all chunks
- Monitor with `process poll` — each job reports independently

### Checkpoint Behavior When Killed

If a process is killed (SIGTERM, e.g., via `process kill` or system shutdown):
- ✅ **Checkpoint is preserved** — contains all extracted text up to the last completed page
- ❌ **Output file is NOT written** — the markdown file is only generated on successful completion
- 🔄 **To recover**: Either resume with `--resume` (continues from checkpoint) or re-run the remaining page range with `--pages`

This means if you intentionally stop a chunk to switch strategies, the checkpoint holds the data but you must either resume or accept that the partial work needs a new run.

## Quality Observations

**What worked well:**
- Model correctly identified transliterated Sinhala vs. pure English
- Preserved full sentences and code-mixed constructions
- Ignored watermarks and page numbers
- Handled pronunciation chart fragments (dh/d, th/t, ae/aa)
- Zero failures across 443 pages — gemini-3-flash-preview:cloud proved extremely reliable

**Minor cleanup needed in post-processing:**
- HTML `<u>` tags from underlined text in original (e.g., `Po<u>th</u>a`)
- Fragment entries from pronunciation tables (single letters like `a`, `aa`, `dha`)
- Some English loanwords that are genuinely part of Sinhala (car, bike, laptop) — keep these
- Deduplication across chunks: the same words appear on many pages (e.g., `thiyenawadha`, `kaaema`, `Oyaage`)

## Model Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Backend | Ollama Cloud | Native `/api/chat` endpoint |
| Model | gemini-3-flash-preview:cloud | Fast, cheap, excellent multilingual OCR |
| DPI | 200 | Sufficient for clear slide text |
| Delay | 2.0s | Minimum to stay under 30 RPM |
| Max retries | 3 | Never needed in this session |

## Post-Processing Recommendations

1. **Deduplicate**: Sort and uniq the combined output — many words repeat across lessons
2. **Clean HTML**: Strip `<u>` tags from underlined original text
3. **Filter fragments**: Remove single-letter pronunciation chart entries (a, aa, dha, tha)
4. **Preserve code-mixed**: Keep English loanwords with Sinhala suffixes (Car eka, Call karanawa)
5. **Sort by lesson or alphabetically** depending on use case
