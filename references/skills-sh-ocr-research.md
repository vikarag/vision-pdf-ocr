# Skills.sh OCR Research Findings

## Date: 2026-05-12
## Context: Evaluating skills.sh OCR skills against existing Hermes/Lenovo stack

---

## Top skills.sh OCR Skills (by installs)

| Rank | Skill | Installs | Engine | Notes |
|------|-------|----------|--------|-------|
| 1 | `ocr-document-processor` | 3.9K | Tesseract-based | 100+ languages, preprocessing, batch processing |
| 2 | `smart-ocr` | 2.3K | PaddleOCR | 100+ languages, layout reconstruction, position data |
| 3 | `pdf-ocr-skill` | 1.2K | Multi-engine (RapidOCR/PaddleOCR/SiliconFlow) | Smart fallback strategy |
| 4 | `deepseek-ocr` | 1.1K | DeepSeek-OCR (vision-LMM) | Best for muffled/distorted fonts |
| 5 | `mistral-ocr` | 160 | Mistral OCR API | Document-specific OCR |

## Gap Analysis

**Already have in Hermes:**
- OpenDataLoader (Java-based fast extraction)
- PyMuPDF (text-based PDFs)
- Tesseract (system-installed)
- Mistral OCR client (venv exists)

**Missing for image-scanned + multilingual + muffled fonts:**
- Local OCR with preprocessing (PaddleOCR) — can install if needed
- Vision-LLM OCR wrapper with system prompt customization

## Key Discovery: DeepSeek API Limitation

**DeepSeek API (`api.deepseek.com`) is TEXT-ONLY.**
- Models `deepseek-v4-flash` and `deepseek-v4-pro` do NOT accept `image_url`
- DeepSeek-OCR is an open-source model requiring self-hosting (24GB+ VRAM)
- For cloud vision OCR, use: Gemini, Claude, Mistral OCR, GPT-4o, or Ollama Cloud

## Recommendation

Skills.sh skills are well-designed wrappers around open-source tools. For this user's setup:
- **Skip `deepseek-ocr` skill** — requires local GPU, no hosted API
- **Install `smart-ocr` (PaddleOCR)** if needing local 100+ language OCR
- **Use custom `vision-pdf-ocr` skill** (this skill) for cloud-based vision OCR with system prompt customization
