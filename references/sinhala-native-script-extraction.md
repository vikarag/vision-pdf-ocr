# Native-Script Sinhala OCR Session Notes

Session: 2026-05-19 — Extracting `වියරණ-විවරණ-ප්‍රථම-භාගය.pdf`

## Document Profile

- **Language:** Sinhala (සිංහල) — native script, NOT Latin transliteration
- **Content:** Monolingual Sinhala book, almost entirely in Sinhala script
- **Pages:** 139
- **Model:** `gemini-3-flash-preview:cloud`
- **Backend:** Ollama Cloud
- **Result:** 139/139 pages processed, 0 failures

## System Prompt Used

```
This is a Sinhala language book written almost entirely in Sinhala script (සිංහල).
Extract ALL text exactly as it appears, preserving the original Sinhala script precisely.
Do NOT translate anything into English.
Do NOT use the <tl> tag wrapper.
Preserve all Sinhala characters, diacritics, and punctuation exactly as they appear in the original.
Use markdown formatting (tables, headers, lists) where appropriate to reflect the visual structure of the page.
Ignore page numbers, running headers, and footers.
Mark unclear text with [unclear: best_guess].
If a page is blank or contains only illustrations, note it.
Output ONLY the extracted text and structure — no commentary.
```

## Key Differences from Transliteration Extraction

| Aspect | Transliteration Mode | Native Script Mode |
|--------|---------------------|-------------------|
| Output script | Latin alphabet (e.g., `Mama`, `Oyaage`) | Sinhala script (සිංහල) |
| `<tl>` tags | Used for target language words | Explicitly disabled |
| Translation | English glosses often included | None — pure source text |
| Model challenge | Distinguishing Arabic/Sinhala from English | Rendering complex conjuncts and diacritics |
| Use case | Vocabulary lists, flashcards | Full-text archive, searchable corpus |

## Critical System Prompt Elements

1. **"Do NOT translate anything into English"** — prevents the model from inserting English glosses or summaries
2. **"Do NOT use the `<tl>` tag wrapper"** — overrides default rule #12 in `vision_ocr.py`
3. **"Preserve all Sinhala characters, diacritics, and punctuation"** — ensures fidelity for complex script features like:
   - Conjunct consonants (e.g., ඳ, ඟ, ඬ)
   - Vowel diacritics (e.g., ා, ි, ු, ෙ, ො)
   - Special characters (e.g., ර්‍ය, ය්‍ය ligatures)
4. **"Output ONLY the extracted text and structure — no commentary"** — prevents model from adding explanatory notes

## Pitfalls Observed

- **Missing `pymupdf`:** First run failed with `ModuleNotFoundError: No module named 'fitz'`. Fix: `pip install pymupdf`.
- **Progress polling:** Without `--notify-on-complete`, user had to manually check log file repeatedly. This session led to making `--notify-on-complete` the default.
- **LaTeX arrow syntax:** The model output `\$\\rightarrow\$`, `\$\\leftarrow\$`, `\$\\uparrow\$`, `\$\\downarrow\$` for arrows in sound-change tables (e.g., අ + ඉ → ඒ). User explicitly dislikes LaTeX math syntax in non-mathematical documents. Fix: added rule #15 to default system prompt banning LaTeX arrows; use Unicode `→←↑↓` instead. Post-hoc fix on extracted file: `sed -i 's/\\$\\\\rightarrow\\$/→/g; s/\\$\\\\leftarrow\\$/←/g; s/\\$\\\\uparrow\\$/↑/g; s/\\$\\\\downarrow\\$/↓/g' file.md`.

## Performance

- ~4-5 seconds per page
- 139 pages completed in ~12-15 minutes
- Zero page failures
- Checkpoint file auto-cleaned on success

## Output Location

`/mnt/HDISK1/Languages/1/Sinhala/වියරණ-විවරණ-ප්‍රථම-භාගය_ocr.md`
