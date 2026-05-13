# TOC JSON Integration for Vision PDF OCR

Session: 2026-05-13 — Sinhala grammar book extraction with embedded TOC

## When to Use This

Use TOC JSON integration when:
- The document has a known hierarchical structure (grammar books, textbooks, reference manuals)
- You want the model to assign correct markdown heading levels (`#` through `#####`)
- The document's printed page numbers differ from actual PDF page numbers

## TOC JSON Format

The expected structure is a nested array of objects:

```json
[
  {
    "title": "REFERENCE",
    "pdf-page-no": 15,
    "children": [
      {
        "title": "Nouns",
        "pdf-page-no": 16,
        "children": [
          {
            "title": "Animate and inanimate",
            "pdf-page-no": 16
          }
        ]
      }
    ]
  }
]
```

Fields:
- `title` — Section title as it appears in the document
- `pdf-page-no` — **Actual PDF page number** (not the printed page number)
- `children` — Optional nested array of the same structure

## Depth-to-Heading Mapping

| Depth | Heading Level |
|-------|--------------|
| 0 (top-level) | `#` |
| 1 | `##` |
| 2 | `###` |
| 3 | `####` |
| 4 | `#####` |

## Workflow

### Step 1: Obtain or Create the TOC JSON

If the PDF has a digital TOC, extract it. Otherwise, create it manually or via another tool.

### Step 2: Clean Unicode Escapes

**Critical:** JSON files often contain Unicode escapes like `\u014d\u00e0` instead of actual characters like `ōnà`. The vision model cannot match escaped sequences against text in the page image.

Clean with Python:

```python
import json

with open('toc.json', 'r') as f:
    data = json.load(f)

with open('toc-clean.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### Step 3: Flatten to Compact Format

Convert the nested structure to a flat "Page N: ## Title" format:

```python
import json

def flatten_toc(nodes, depth=0):
    lines = []
    for node in nodes:
        heading = '#' * (depth + 1)
        lines.append(f"Page {node['pdf-page-no']}: {heading} {node['title']}")
        if 'children' in node:
            lines.extend(flatten_toc(node['children'], depth + 1))
    return lines

with open('toc-clean.json', 'r') as f:
    toc = json.load(f)

compact = '\n'.join(flatten_toc(toc))
print(compact)
```

### Step 4: Embed in System Prompt

Append the compact TOC to the system prompt under a clear header:

```
TABLE OF CONTENTS REFERENCE — Use this to assign correct heading levels.
Match section titles against the titles below and use the indicated heading level.
The page numbers refer to actual PDF page numbers (not printed page numbers).

Page 16: ## Nouns
Page 16: ### Animate and inanimate
Page 17: ### Definite and indefinite
Page 18: ### Case
Page 18: #### Case functions
...
```

### Step 5: Run OCR

```bash
python scripts/batch_ocr.py ./grammar-book.pdf \
  --pages 16-117 \
  --system-prompt "...your document context...

TABLE OF CONTENTS REFERENCE — ...

Page 16: ## Nouns
..." \
  --output-dir ./extracted/
```

## Pitfalls

1. **Unicode escapes in JSON** — Always clean `\uXXXX` escapes before embedding. The model matches against visible text, not escape sequences.
2. **Page number mismatch** — Ensure `pdf-page-no` uses actual PDF page numbers. If the document has front matter (copyright, TOC, preface), PDF page 1 may not be the first content page.
3. **Title variations** — The model does fuzzy matching, but titles in the TOC should closely match what's actually printed in the document.
4. **Depth overflow** — Most markdown renderers only handle up to `######` (6 levels). If your TOC goes deeper, consider flattening the deepest levels.

## Reference: Sinhala Grammar Book TOC

The Sinhala grammar book TOC had 155 entries across 5 depth levels:
- 3 top-level chapters (`#`)
- 21 second-level sections (`##`)
- 68 third-level sections (`###`)
- 60 fourth-level sections (`####`)
- 3 fifth-level sections (`#####`)

The compact format was ~4,500 characters — well within context limits for modern VLMs.
