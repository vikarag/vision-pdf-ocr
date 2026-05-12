# Test Results: Palestinian Arabic Textbook OCR

## Document
- **Source**: Speaking Arabic: A Course in Conversational Eastern Arabic (Palestinian) - Book 1
- **Pages tested**: 2–30 (29 pages)
- **PDF type**: Scanned textbook with Latin transliteration + Arabic script
- **Challenge**: Special transliteration characters outside ASCII

## System Prompt Used

```
This is a Palestinian Arabic language textbook. The Arabic text is transliterated
using a modified Latin alphabet with these special characters that must be
preserved exactly: ħ ṯ ḏ š ṣ ḍ ṭ ẓ ' ʿ ġ α ē ī ō ū.
Do NOT convert these to standard ASCII. Preserve all diacritics, macrons,
and special letters exactly as written. Arabic script should also be preserved
where present.
```

## Results

| Metric | Value |
|--------|-------|
| Pages processed | 29/29 |
| Pages failed | 0 |
| Backend | Ollama Cloud (`gemini-3-flash-preview:cloud`) |
| DPI | 200 |
| Delay | 2.0s (30 RPM limit) |
| Total time | ~4 minutes |

## Special Character Preservation

All 15 special characters were preserved:

| Char | Count | Examples |
|------|-------|----------|
| `ī` | 68 | mīn, kbīr, mudīr, Salīm |
| `š` | 64 | šū, šuft, mašbah |
| `ē` | 54 | wēn, wēnak, ħēfa |
| `ʿ` | 49 | maʿi, kaʿke, naʿam |
| `ū` | 35 | šū, hū, byūt |
| `α` | 21 | wαrα, ṭalαb, musīq̈α |
| `ġ` | 19 | ġāli, baġar, šuġol-na |
| `ṣ` | 18 | ṣāliḥ, ṣallēt |
| `ṭ` | 17 | ṭayyeb, ṭalαb, ẓābeṭ |
| `ō` | 17 | hōn, Jōrj, lōn |
| `ħ` | 11 | ħilu, ħalla, ħātem |
| `ẓ` | 6 | ẓābeṭ |
| `ḍ` | 6 | ḍallēt, ḍuhor |
| `ṯ` | 5 | ṯaq̈āfe, ṯiq̈a |
| `ḏ` | 5 | ḏaki, hāḏa |

## Content Captured

- Title page, copyright, table of contents
- Preface (methodology, how to use the course)
- Pronunciation guide (all consonants and vowels explained)
- Lesson 1: vocabulary, conversation, grammar explanations
- Markdown tables for vocabulary
- Footnotes preserved

## Key Lessons

1. **System prompts work**: Explicitly listing special characters dramatically improves preservation vs. generic OCR
2. **DPI 200 is sufficient** for clear textbook scans; use 300 for blurry/aged documents
3. **Rate limiting essential**: 2s delay prevents rate limit errors on 29-page batches
4. **Resume works**: Checkpoint files allow resuming interrupted jobs
5. **Tables extract well**: Vocabulary lists render as clean markdown tables
6. **Footnotes captured**: Explanatory footnotes appear inline

## Output Format

```markdown
# Extracted: Speaking Arabic_ ... Book 1.pdf

**Metadata:**
- Pages (total): 152
- Pages processed: 29
- Pages failed: 0
- Backend: ollama
- Model: gemini-3-flash-preview:cloud
- System prompt hash: 05acf88e
- Extracted: 2026-05-12T07:25:54Z

---

## Page 2
[extracted text]

---

## Page 3
[extracted text]
```
