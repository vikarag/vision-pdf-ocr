# Ollama Cloud Backend: Native API Requirement

## Why Native API?

This skill uses Ollama Cloud's **native `/api/chat` endpoint**, not the OpenAI-compatible `/v1/chat/completions` proxy.

**Reason:** Hermes bug #23422 — the `/v1` proxy does not support the OpenAI vision format (`image_url` objects). Vision requests via the proxy fail with timeout or 401 errors.

The native endpoint works perfectly:
```json
POST https://ollama.com/api/chat
{
  "model": "gemini-3-flash-preview:cloud",
  "messages": [{
    "role": "user",
    "content": "prompt",
    "images": ["base64..."]
  }]
}
```

## Implications

- The skill makes direct HTTP calls, not using Hermes `vision_analyze`
- You need `OLLAMA_API_KEY` in `~/.hermes/.env`
- The Ollama Pro subscription covers usage
- ~6 seconds per page at 200 DPI

## Tested Models

| Model | OCR Quality | Speed | Cost |
|-------|-------------|-------|------|
| `gemini-3-flash-preview:cloud` | Excellent | ~6s/page | Included in Pro |

## Alternatives

If Ollama Cloud is unavailable, switch backends:
```bash
--backend openrouter --model google/gemini-3.1-pro-preview
```
