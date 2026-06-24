# Hindi Language Textbook OCR — System Prompt Pattern

Session: 2026-05-29 — Tested on Teach Yourself Hindi (2003), page 27.

## Document Type

Hindi language textbook published in English. Pages contain Devanagari script, Romanized transliteration, English translations, vocabulary tables with gender markers, and dialogue sections.

## Key Diacritics for Hindi Romanization

| Category | Characters | Example |
|----------|-----------|---------|
| Nasalized short vowels | a tilde, i tilde, etc. | h with tilde (yes, nasalized) |
| Long vowels | a macron, i macron, u macron | good |
| Nasalized long vowels | a macron+tilde, etc. | yes respectfully |
| Retroflex consonants | t dot below, d dot below, etc. | boy, all right |
| Palatal sibilant | s acute | thank you |

## Model Comparison

Tested page 27 at DPI 250:

| Aspect | Xiaomi Mimo (mimo-v2.5) | Gemini (gemini-3-flash-preview:cloud) |
|--------|---------------------------|----------------------------------------|
| Speed | ~15s | ~60s+ |
| Devanagari tags | Correct | Correct |
| Romanized tags | Correct | Correct |
| Speaker names tagged | No | Yes |
| Nasalization precision | Short (less precise) | Nasalized (more accurate) |
| Gender markers | HTML sup | Unicode superscript |
| Artifacts | None | Icon description added |

## Underlined Character Handling

The textbook uses underlined kh and g in some romanized forms. The prompt explicitly instructs the model to ignore these underlines and treat them as plain kh and g. This prevents combining underline characters which are hard to search.

## CLI Usage Example

```bash
python scripts/batch_ocr.py ./hindi-textbook.pdf \
  --pages 27 \
  --backend xiaomi-mimo \
  --model mimo-v2.5 \
  --system-prompt "This is a Hindi language textbook published in English. Mark ALL Hindi language text (both Devanagari script and Romanized transliteration) with tl tags.

DIACRITIC ALPHABETS used for romanized Hindi:
- Nasalized vowels: a-tilde i-tilde u-tilde e-tilde o-tilde
- Long vowels: a-macron i-macron u-macron
- Nasalized long vowels: a-macron-tilde i-macron-tilde u-macron-tilde (beware)
- Retroflex consonants: t-dotbelow d-dotbelow n-dotbelow r-dotbelow s-dotbelow
- Palatal sibilant: s-acute
- Velar nasal: n-tilde

IMPORTANT: IGNORE underlined kh and g - treat them as plain kh and g.

English text should NOT be wrapped in tl tags. Only wrap Hindi words with tl tags.
Preserve all diacritics exactly as they appear." \
  --output-dir ./extracted/ \
  --dpi 250
```
