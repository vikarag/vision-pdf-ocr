# Fijian (Bauan) Textbook OCR Session Notes

Session: 2026-05-23
Document: *Spoken Fijian: An intensive course in Bauan Fijian* (Schütz & Komaitai)
Pages processed: 218 (53–270, Lessons 1–15)
Backend: ollama-local (gemini-3-flash-preview:cloud)
DPI: 250

## Macron Stripping Pattern

The PDF visually shows macrons (ā, ē, ī, ō, ū) but the text layer does NOT contain them — they are only in the rendered image. The VLM sees the image and must be explicitly instructed to strip them.

**Effective system prompt fragment:**
```
IMPORTANT DIACRITIC RULE: The Fijian text uses macrons (long vowel marks) over vowels: ā, ē, ī, ū, ō. You must COMPLETELY IGNORE these macrons and write the letters WITHOUT the macron mark. For example, 'bāravi' must be written as 'baravi', 'lēsoni' as 'lesoni', 'mākete' as 'makete', 'tū' as 'tu', 'vō' as 'vo'. Treat macron-vowels exactly like their plain counterparts: a, e, i, o, u. NEVER output ā, ē, ī, ō, ū in the extracted text.
```

**Verification:** After processing 193 pages, zero macron characters (āēīūō) were found in 5,034 `<tl>` tags.

## Checkpoint Hash Pitfall

The checkpoint filename includes a hash of: `pdf_path + system_prompt + backend + model + pages_range`.

**Critical consequence:** Changing `--pages` (e.g., from `53-270` to `110-270`) generates a **different checkpoint file** and resumes from scratch. The old checkpoint is not automatically merged.

**Workaround:**
1. Always use the same `--pages` range when resuming
2. To fill gaps, process the missing range with the SAME `--pages` value as the original run
3. Or manually merge checkpoint JSONs by combining `completed_pages` lists and `results` dicts

**Session example:**
- First run: `--pages 53-270` → checkpoint `ca46a7ab` (pages 53–109 completed)
- Second run: `--pages 110-270` → checkpoint `f334c977` (pages 110–133 completed, but 53–109 lost)
- Fix: Re-process `--pages 53-270` with `--resume` to continue from the original checkpoint

## Background Mode Failure

The default `--background` mode in batch_ocr.py can fail silently — the subprocess forks, writes a PID file, then exits immediately without processing any pages. The PID file becomes stale.

**Symptoms:**
- `ps aux | grep batch_ocr` shows no running process seconds after launch
- Checkpoint file never updates
- Log file only shows the header, no page progress

**Workaround:** Use `--no-background` and run in a `screen`/`tmux` session, or use Hermes `terminal(background=true)` with `notify_on_complete`. The subprocess fork with `start_new_session=True` sometimes exits before processing begins.

## Terminal Timeout Limitation

Hermes `terminal()` has a hard maximum foreground timeout of 600 seconds (10 minutes). For vision OCR at ~4–6 seconds per page, this limits each run to approximately 25–30 pages.

**Chunking strategy used in this session:**
```bash
# Process in ~25-page chunks to stay under 600s timeout
python scripts/batch_ocr.py ... --pages 78-109 --no-background   # 32 pages, ~5-6 min
python scripts/batch_ocr.py ... --pages 110-133 --no-background  # 24 pages, ~4-5 min
python scripts/batch_ocr.py ... --pages 134-158 --no-background  # 25 pages, ~4-5 min
# ... etc
```

Each chunk uses `--resume` to continue from the same checkpoint (same `--pages` range).

## `<tl>` Tag Wrapping for Language Textbooks

For mixed-language textbooks (Fijian + English), the `<tl>` wrapper effectively separates target language from instructional text:

- Fijian words/phrases in dialogues → `<tl>...</tl>`
- Fijian words in vocabulary lists → `<tl>...</tl>`
- Fijian words in repetition drills → `<tl>...</tl>`
- English instructional text, grammar notes, translations → no tags

This produces clean output suitable for vocabulary extraction or flashcard generation.

## Output Quality

- **Dialogue formatting:** Blockquote with speaker labels (`> **A** <tl>...</tl>`) works well
- **Vocabulary tables:** Two-column markdown tables (`| Fijian | English |`) preserve structure
- **Repetition drills:** Table format with Cue/Sentence columns is readable
- **Page numbers and headers:** Successfully ignored per system prompt
- **Footnote references:** Superscript numbers (¹, ², ³, ⁴) still appear in output — may need post-processing cleanup
