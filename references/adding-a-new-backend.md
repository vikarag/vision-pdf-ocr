# Adding a New Vision Backend to the OCR Pipeline

Step-by-step recipe for adding a new vision API provider (e.g., OpenAI, Anthropic, local endpoint) to the vision-pdf-ocr skill.

## Files to Edit

1. `scripts/vision_ocr.py` — add backend class + register it
2. `scripts/batch_ocr.py` — add to CLI `--backend` choices
3. `SKILL.md` — document in backends table, environment variables, troubleshooting
4. `references/<provider>-backend.md` (optional) — provider-specific quirks

## Step 1: Add Backend Class

In `vision_ocr.py`, add a new class after the existing backends, before `VisionPDFProcessor`:

```python
class MyProviderBackend(VisionBackend):
    """MyProvider backend (OpenAI-compatible or custom).

    Endpoint: https://api.myprovider.com/v1
    """

    BASE_URL = "https://api.myprovider.com/v1"

    def __init__(self, model: str = "default-model", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = _load_env("MYPROVIDER_API_KEY")

    def extract_text(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> str:
        img_b64 = base64.b64encode(image_bytes).decode()

        # --- OpenAI-compatible format (most common) ---
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                        },
                    ],
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}/chat/completions"

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"MyProvider API failed after {self.max_retries} retries: {e}")
                time.sleep(self.delay * (2 ** attempt))

        return ""
```

## Step 2: Register in VisionPDFProcessor

In `VisionPDFProcessor.__init__()`, add entries to both dicts:

```python
model_defaults = {
    "ollama": "gemini-3-flash-preview:cloud",
    "ollama-local": "llava",
    "openrouter": "google/gemini-3.1-pro-preview",
    "gemini": "gemini-3.1-pro-preview",
    "myprovider": "default-model",  # <-- add
}

backend_classes = {
    "ollama": OllamaBackend,
    "ollama-local": OllamaLocalBackend,
    "openrouter": OpenRouterBackend,
    "gemini": GeminiBackend,
    "myprovider": MyProviderBackend,  # <-- add
}
```

## Step 3: Add CLI Choice

In `batch_ocr.py`, update the `--backend` argument:

```python
parser.add_argument(
    "--backend",
    choices=["ollama", "ollama-local", "openrouter", "gemini", "myprovider"],
    default="ollama-local",
    help="Vision backend (default: ollama-local)",
)
```

## Step 4: Update SKILL.md

Add to the backends table and environment variables table.

## Provider Format Cheat Sheet

| Provider | Format | Image Field | Response Path | Auth |
|----------|--------|-------------|---------------|------|
| OpenAI / OpenRouter | OpenAI | `messages[].content[].image_url` | `choices[0].message.content` | Bearer |
| Ollama Cloud | Ollama native | `messages[].images[]` | `message.content` | Bearer |
| Ollama Local | Ollama native | `messages[].images[]` | `message.content` | None |
| Gemini direct | Gemini native | `contents[].parts[].inline_data` | `candidates[0].content.parts[0].text` | URL param |

## Common Pitfalls

1. **Vision vs text-only models:** Some providers have separate model IDs for vision and text. The `-pro` or `-vision` suffix is not always consistent. Always test with a real image before assuming vision works.

2. **Base URL trailing slash:** Store `BASE_URL` without trailing slash and append paths explicitly.

3. **Image encoding:** Always base64-encode PNG bytes. PNG is safest.

4. **Timeout:** Set `timeout=120` on the `requests.post()` call.

5. **System prompt concatenation:** Some providers concatenate system + user prompt into a single message. Check existing implementations for the pattern.

6. **Rate limiting:** Add the `delay` parameter (minimum 2.0s enforced in `VisionPDFProcessor`).
