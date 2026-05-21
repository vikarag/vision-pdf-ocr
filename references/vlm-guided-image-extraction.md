# VLM-Guided Image Extraction Architecture

## Overview

Two-stage pipeline for extracting complex figures from PDFs during vision OCR:

1. **Detection stage (VLM):** The vision model identifies complex images/diagrams and outputs special markdown tags with normalized bounding boxes.
2. **Cropping stage (PyMuPDF):** A post-processor parses the tags, opens the original PDF, crops the specified region, and saves as PNG.

This hybrid approach is more accurate than either pure VLM extraction (which can't reliably crop) or pure PDF parsing (which can't distinguish important figures from decorative elements).

## VLM Tag Format

```markdown
![FIGURE: brief description](extract://PAGENO-NN/bbox:x1,y1,x2,y2)
```

- `PAGENO`: 1-indexed page number
- `NN`: Sequential figure number on that page (01, 02, ...)
- `x1,y1`: Top-left normalized coordinates (0.0–1.0)
- `x2,y2`: Bottom-right normalized coordinates (0.0–1.0)

## System Prompt Rule

Rule #16 in the default system prompt instructs the VLM:

> COMPLEX IMAGE EXTRACTION: When you encounter images, diagrams, charts, or illustrations that contain important visual information that is difficult or impossible to convey accurately with text alone (e.g., complex diagrams, detailed charts, maps, anatomical illustrations, mathematical figures, flowcharts, architectural drawings), you MUST flag them for extraction using the following special syntax...

The VLM decides **which** images are worth extracting. Simple decorative images, logos, or icons remain as text descriptions (rule #14).

## Cropping Implementation

```python
def _extract_images_from_page(self, pdf_path, page_num, text, images_dir, total_pages):
    import fitz, re

    pattern = re.compile(
        r"!\[([^\]]*)\]\(extract://(\d+)-(\d+)/bbox:([0-9.]+),([0-9.]+),([0-9.]+),([0-9.]+)\)"
    )

    doc = fitz.open(pdf_path)
    page = doc[page_num]
    page_rect = page.rect

    matches = list(pattern.finditer(text))
    seq_counter = 0
    pad_width = len(str(total_pages))  # Dynamic zero-padding

    new_text = text
    for m in matches:
        seq_counter += 1
        desc = m.group(1)
        pageno = int(m.group(2))
        x1, y1, x2, y2 = [float(m.group(i)) for i in range(4, 8)]

        # Clamp and convert to page coordinates
        rect = fitz.Rect(
            max(0, x1) * page_rect.width,
            max(0, y1) * page_rect.height,
            min(1, x2) * page_rect.width,
            min(1, y2) * page_rect.height,
        )

        # Expand slightly and intersect with page bounds
        rect = (rect + (-2, -2, 2, 2)) & page_rect

        # Render at high DPI for quality
        zoom = max(self.dpi, 300) / 72
        pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(zoom, zoom))

        fname = f"{pageno:0{pad_width}d}-{seq_counter:02d}.png"
        pix.save(str(images_dir / fname))

        rel_path = f"images/{fname}"
        new_text = new_text.replace(m.group(0), f"![{desc}]({rel_path})", 1)

    return new_text
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **VLM decides what to extract** | Only the VLM viewing the rendered page can judge whether a figure is "complex enough" to warrant extraction vs. a simple text description |
| **VLM provides bbox hints** | The VLM sees the image and can estimate where the figure is. Pure PDF parsing (`page.get_images()`) misses vector drawings and can't judge importance |
| **PyMuPDF does actual cropping** | Precise, deterministic, no hallucination. Uses the original PDF vectors for maximum quality |
| **Dynamic zero-padding** | `len(str(total_pages))` gives intuitive filenames: `5-01.png` for short docs, `025-04.png` for 100–999 page docs |
| **Per-page sequence counter** | `065-01.png`, `065-02.png` for multiple figures on one page. Easier to locate than global numbering |
| **`max(dpi, 300)` for crops** | Even if the user uses `--dpi 200` for speed, figure crops always render at 300+ DPI for readability |
| **2-pixel padding** | Small expansion prevents cutting off figure edges. Clamped to page bounds to avoid errors |

## Filename Convention

```
images/
├── 065-01.png   # Page 65, figure 1 (186-page doc → 3-digit padding)
├── 065-02.png   # Page 65, figure 2
├── 069-01.png   # Page 69, figure 1
└── 128-01.png   # Page 128, figure 1
```

Padding by total page count:
- 1–9 pages → `1-01.png`
- 10–99 pages → `01-01.png`
- 100–999 pages → `001-01.png`
- 1000+ pages → `0001-01.png`

## When This Pattern Applies

Use this two-stage approach when:
- Processing scanned/image-based PDFs with mixed text and figures
- Figures contain information that cannot be accurately conveyed textually (maps, charts, photographs, diagrams)
- You need both extracted text AND preserved visual figures in the output
- Simple "describe the image" text replacement would lose critical information

## Limitations

- VLM must be capable of following system prompt instructions (some local models ignore complex rules)
- Bounding boxes are estimates — very precise crops may need manual adjustment
- Only works with PyMuPDF-compatible PDFs (most standard PDFs)
- Each extraction requires opening the PDF again (minor overhead, ~100ms per page with figures)
