#!/usr/bin/env python3
"""CLI for batch OCR of scanned PDFs using vision-language models.

Usage:
    python batch_ocr.py scan.pdf
    python batch_ocr.py scan.pdf --system-prompt "Romanization uses ğ, ħ, ž"
    python batch_ocr.py scan.pdf --pages 1-50 --dpi 300
    python batch_ocr.py scan.pdf --backend openrouter --model google/gemini-3.1-pro-preview
    python batch_ocr.py scan.pdf --resume
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from vision_ocr import VisionPDFProcessor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from scanned PDFs using vision-language models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan.pdf
  %(prog)s scan.pdf --system-prompt "Ottoman Turkish: ğ, ı, ş, ç, ö, ü"
  %(prog)s scan.pdf --pages 1-10 --dpi 300
  %(prog)s scan.pdf --backend openrouter --model google/gemini-3.1-pro-preview
  %(prog)s scan.pdf --resume --output-dir ./extracted/
        """,
    )

    parser.add_argument("pdf", help="Path to scanned PDF file")
    parser.add_argument(
        "--system-prompt",
        default="",
        help="Context prompt for the vision model (e.g., special characters, language hints)",
    )
    parser.add_argument(
        "--backend",
        choices=["ollama", "openrouter", "gemini"],
        default="ollama",
        help="Vision backend (default: ollama)",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Specific model tag (backend defaults if omitted)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Render resolution in DPI (default: 200, use 300 for blurry scans)",
    )
    parser.add_argument(
        "--pages",
        default="",
        help='Page range: "1-10" or "1,3,5" (1-indexed, default: all)',
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory (default: same as PDF)",
    )
    parser.add_argument(
        "--output-name",
        default="",
        help="Output filename (default: <pdf>_ocr.md)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint if exists",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0, min: 2.0 to stay under 30 RPM)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per page (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also save JSON metadata sidecar",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output",
    )

    return parser.parse_args()


def progress_callback(page: int, total: int, status: str):
    """Print progress to console."""
    icons = {
        "processing": "⏳",
        "success": "✅",
        "failed": "❌",
        "skipped": "⏭️ ",
    }
    icon = icons.get(status, "○")
    print(f"\r{icon} Page {page}/{total} ({status})", end="", flush=True)
    if status in ("success", "failed", "skipped"):
        print()  # newline after completion


def main():
    args = parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    output_dir = Path(args.output_dir) if args.output_dir else pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output_name:
        output_path = output_dir / args.output_name
    else:
        output_path = output_dir / f"{pdf_path.stem}_ocr.md"

    # Validate delay (minimum 2.0s to stay under 30 RPM)
    effective_delay = max(args.delay, 2.0)
    if args.delay < 2.0:
        print(f"⚠️  Delay increased from {args.delay}s to 2.0s (30 RPM limit)", file=sys.stderr)

    # Initialize processor
    processor = VisionPDFProcessor(
        backend=args.backend,
        model=args.model,
        system_prompt=args.system_prompt,
        dpi=args.dpi,
        delay=effective_delay,
        max_retries=args.max_retries,
    )

    if not args.quiet:
        print(f"📚 PDF: {pdf_path}")
        print(f"🔧 Backend: {args.backend} ({processor.model})")
        print(f"📊 DPI: {args.dpi}")
        print(f"📝 System prompt: {args.system_prompt[:60]}{'...' if len(args.system_prompt) > 60 else ''}")
        print(f"📁 Output: {output_path}")
        if args.resume:
            print("🔄 Resume mode enabled")
        print()

    # Process
    callback = None if args.quiet else progress_callback
    result = processor.process_pdf(
        pdf_path=str(pdf_path),
        output_path=str(output_path),
        pages=args.pages or None,
        resume=args.resume,
        progress_callback=callback,
    )

    if not args.quiet:
        print()
        print("✅ Extraction complete!")
        print(f"   Pages total: {result.pages_total}")
        print(f"   Processed: {result.pages_processed}")
        print(f"   Failed: {result.pages_failed}")
        print(f"   Output: {output_path}")

    # Save JSON sidecar if requested
    if args.json:
        import json
        sidecar_path = output_path.with_suffix(".json")
        sidecar_data = {
            "source": result.source,
            "pages_total": result.pages_total,
            "pages_processed": result.pages_processed,
            "pages_failed": result.pages_failed,
            "backend": result.backend,
            "model": result.model,
            "system_prompt_hash": result.system_prompt_hash,
            "extracted_at": result.extracted_at,
            "pages": [
                {
                    "page": p.page,
                    "status": p.status,
                    "processing_time": p.processing_time,
                    "model": p.model,
                    "error": p.error,
                    "text_length": len(p.text),
                }
                for p in result.pages
            ],
        }
        sidecar_path.write_text(json.dumps(sidecar_data, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"   JSON: {sidecar_path}")

    # Clean up checkpoint on success
    if result.pages_failed == 0 and not args.quiet:
        print("🧹 Checkpoint cleaned up (all pages succeeded)")

    sys.exit(0 if result.pages_failed < result.pages_total else 1)


if __name__ == "__main__":
    main()
