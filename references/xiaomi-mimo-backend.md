# Xiaomi Mimo Token Plan Backend

Session: 2026-05-29 — Added Xiaomi Mimo backend to vision-pdf-ocr skill.

## Endpoint

- **Base URL:** `https://token-plan-sgp.xiaomimimo.com/v1`
- **Protocol:** OpenAI-compatible (`/v1/chat/completions`)
- **Auth:** Bearer token via `XIAOMI_MIMO_API_KEY` in `~/.hermes/.env`

## Model Matrix

| Model | Vision Support | Text | Speed | Notes |
|-------|---------------|------|-------|-------|
| `mimo-v2.5` | **Yes** | Yes | Fast | **Use this for OCR** — base model supports image input |
| `mimo-v2.5-pro` | **No** | Yes | Fast | Returns 404 on image input; text-only |
| `mimo-v2.5-tts` | No | TTS only | — | Voice synthesis, not for OCR |
| `mimo-v2.5-tts-voiceclone` | No | TTS only | — | Voice cloning |
| `mimo-v2.5-tts-voicedesign` | No | TTS only | — | Voice design |
| `mimo-v2-omni` | Yes | Yes | Medium | Legacy V2 series |
| `mimo-v2-pro` | Yes | Yes | Medium | Legacy V2 series |

**Critical pitfall:** The `-pro` suffix does NOT mean "better vision." `mimo-v2.5-pro` is text-only and returns HTTP 404 when sent image content. Always use `mimo-v2.5` (base) for vision OCR.

## Verification Commands

```bash
# List available models
curl -s "https://token-plan-sgp.xiaomimimo.com/v1/models" \
  -H "Authorization: Bearer $XIAOMI_MIMO_API_KEY"

# Test text-only
curl -s "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions" \
  -H "Authorization: Bearer $XIAOMI_MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "mimo-v2.5-pro", "messages": [{"role": "user", "content": "Hello"}]}'

# Test vision (will FAIL with 404 for -pro, succeed for base)
curl -s "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions" \
  -H "Authorization: Bearer $XIAOMI_MIMO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mimo-v2.5",
    "messages": [{"role": "user", "content": [
      {"type": "text", "text": "What color?"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]}]
  }'
```

## CLI Usage

```bash
python scripts/batch_ocr.py scan.pdf \
  --backend xiaomi-mimo \
  --model mimo-v2.5 \
  --system-prompt "Your context here..."
```

## Performance vs Gemini (Ollama Cloud)

From page-27 Hindi textbook test (same page, same prompt, same DPI 250):

| Metric | Xiaomi Mimo (`mimo-v2.5`) | Gemini (`gemini-3-flash-preview:cloud`) |
|--------|---------------------------|----------------------------------------|
| Speed | ~15s | ~60s+ (timed out once) |
| Devanagari accuracy | Good | Good |
| Diacritic precision | Good (`hũ` short) | Better (`hũ̃` nasalized) |
| Speaker name tagging | No `<tl>` on names | `<tl>` on names |
| Artifacts | None | Added `[Icon: cassette...]` |

**Verdict:** Xiaomi is ~4x faster with comparable accuracy. Gemini is slightly more precise on diacritics but slower and occasionally adds unwanted artifact descriptions. For bulk processing, Xiaomi's speed advantage is significant.

## Response Format

Standard OpenAI chat completion format:

```json
{
  "id": "...",
  "choices": [{
    "finish_reason": "length",
    "message": {
      "content": "extracted text...",
      "role": "assistant",
      "reasoning_content": "internal reasoning..."
    }
  }],
  "model": "mimo-v2.5",
  "usage": {
    "completion_tokens": 100,
    "prompt_tokens": 47,
    "total_tokens": 147,
    "completion_tokens_details": {"reasoning_tokens": 96},
    "prompt_tokens_details": {"image_tokens": 16}
  }
}
```

Note: `reasoning_content` is present in the response — this is the model's chain-of-thought, not the final output. The actual extracted text is in `choices[0].message.content`.
