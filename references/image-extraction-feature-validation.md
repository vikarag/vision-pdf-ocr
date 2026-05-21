# Image Extraction Feature — Validation Notes

## Feature Overview

Added May 2026: Hybrid VLM + PyMuPDF image extraction for complex figures in scanned PDFs.

**Architecture:**
1. VLM flags complex figures with `![FIGURE: desc](extract://PAGENO-NN/bbox:x1,y1,x2,y2)`
2. PyMuPDF parses tags, crops the region from the original PDF at `max(dpi, 300)`
3. Saves as PNG with dynamic zero-padding: `065-01.png` for 100–999 page docs
4. Rewrites markdown reference to relative path `images/065-01.png`

## Real-World Validation

**Document:** 葡萄牙语综合教程1.pdf (186 pages, Portuguese textbook with Chinese explanations)
**Pages tested:** 64–69
**Backend:** ollama-local / gemini-3-flash-preview:cloud
**DPI:** 300

### Results

| Page | Image Extracted | Description | Dimensions | Size |
|------|----------------|-------------|------------|------|
| 65 | `065-01.png` | Cobblestone alleyway in Óbidos, Portugal | 1283×1648 | ~1 MB |
| 69 | `069-01.png` | Living room illustration (sofa, coffee table, desk, computer) | 1390×1075 | ~560 KB |

**Observations:**
- VLM correctly distinguished complex photographs/illustrations from simple decorative elements
- The Óbidos photo (p.65) was flagged because it's a real photograph with visual detail impossible to convey in text
- The living room illustration (p.69) was flagged because it's an exercise diagram where spatial relationships matter
- Pages with simple tables, pronunciation charts, or text-only layouts produced no extraction tags (correct behavior)
- Dynamic zero-padding works: 186-page doc → 3-digit padding (`065-01.png`)

### CLI Used

```bash
python scripts/batch_ocr.py \
  "/path/to/葡萄牙语综合教程1.pdf" \
  --pages 64-69 \
  --backend ollama-local \
  --model gemini-3-flash-preview:cloud \
  --dpi 300 \
  --output-dir /tmp/ocr_test \
  --no-background
```

**Note:** For testing small page ranges, always use `--no-background`. If the terminal times out, use `--resume` to continue.

### Markdown Output Quality

- Portuguese text correctly wrapped in `<tl></tl>` tags
- Pronunciation tables rendered as markdown tables
- Exercise questions preserved with fill-in-the-blank formatting
- Image references use relative paths: `![FIGURE: ...](images/065-01.png)`

## Technical Details

**Bounding box format:** Normalized coordinates (0.0–1.0) where (x1,y1) is top-left and (x2,y2) is bottom-right.

**Crop quality:** Uses `max(dpi, 300)` for extraction regardless of rendering DPI. A 2-pixel padding is added around the bbox and clamped to page bounds.

**Sequential numbering:** Per-page counter, not global. `065-01.png`, `065-02.png` for multiple figures on one page.

**Filename padding logic:**
```python
def _page_num_width(self, total_pages: int) -> int:
    return len(str(total_pages))
# 1-9 pages → 1 digit, 10-99 → 2 digits, 100-999 → 3 digits, etc.
```

## Pitfalls

- **Terminal timeout on long runs:** The default background mode is recommended for production, but for testing use `--no-background` with small `--pages` ranges.
- **VLM must support the syntax:** The system prompt rule #16 instructs the model to output `extract://` tags. Models that ignore system prompt instructions (e.g., some local models) may not produce extraction tags.
- **BBox estimation accuracy:** The VLM estimates normalized coordinates visually. For very precise crops, consider post-processing with PyMuPDF's native image detection (`page.get_images()`) as a fallback.
- **Resume and image extraction:** When resuming, already-processed pages are skipped entirely, including their image extraction. If you need to re-extract images from a previously completed page, delete the checkpoint file and re-run.
