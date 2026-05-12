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

### Example 2: Multilingual academic paper

```bash
python scripts/batch_ocr.py ./bilingual-paper.pdf \
  --system-prompt "Academic paper with Korean and English. Korean text uses standard Hangul. Mathematical equations use LaTeX-style notation. Tables use tabular layout." \
  --backend openrouter \
  --model google/gemini-3.1-pro-preview
```

### Example 3: Resume after crash

```bash
python scripts/batch_ocr.py ./500-page-archive.pdf \
  --system-prompt "19th century French administrative documents. Use of long s (ſ) and archaic spellings." \
  --resume
```

## Output Format

### Markdown (`<name>_ocr.md`)

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
[Output] 
  ↓  Concatenate all pages into single markdown file
```

## Rate Limiting

To respect API rate limits and stay under **30 requests per minute**, a **minimum 2-second delay** is enforced between page requests. This is hardcoded — you cannot set `--delay` below 2.0.

| Backend | Approximate Speed |
|---------|------------------|
| Ollama Cloud | ~2-4s per page + 2s delay = ~4-6s/page |
| OpenRouter | Varies by model |
| Gemini | Varies by model |

For a 100-page document, expect **~10-15 minutes** total processing time.

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
| Text is garbled/missing | Increase `--dpi` to 300 or higher |
| Model misses special chars | Make them **explicit** in `--system-prompt` |
| Rate limit errors | Already handled — minimum 2s delay enforced |
| Processing too slow | This is expected for vision OCR (~4-6s/page) |
| Pages fail repeatedly | Try `--backend openrouter` with different model |
| Resume not working | Check checkpoint file exists in output dir |

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

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `OLLAMA_API_KEY` | Ollama backend | Your Ollama Cloud API key |
| `OPENROUTER_API_KEY` | OpenRouter backend | Your OpenRouter key |
| `GEMINI_API_KEY` | Gemini backend | Google Gemini API key |

## References

- `references/ollama-cloud-backend.md` — Why native API is used (not Hermes `vision_analyze`), tested models, and backend alternatives
- `references/skills-sh-ocr-research.md` — Skills.sh research findings that led to this skill's creation; comparison with skills.sh OCR skills; DeepSeek API limitations
- `references/test-results-palestinian-arabic.md` — Real-world validation: 29-page Palestinian Arabic textbook extracted with 100% character preservation (68 ī, 64 š, 54 ē, 49 ʿ, etc.)

## Notes

- Ollama Cloud uses the **native `/api/chat` endpoint**, not the `/v1` proxy, due to Hermes bug #23422
- The default `gemini-3-flash-preview:cloud` model is fast, cheap, and excellent at multilingual OCR
- For very blurry scans, increase `--dpi` to 300+ and add explicit character hints in `--system-prompt`
- The checkpoint file is hidden (`.<name>_ocr_checkpoint_<hash>.json`) in the output directory
- This skill was created because existing tools (Tesseract, marker-pdf) failed on muffled fonts, and skills.sh skills lacked the system-prompt customization needed for special-character documents
- For a complete inventory of PDF/OCR tools already installed on this system, see `ocr-and-documents` skill's `references/hermes-pdf-tool-inventory.md`
