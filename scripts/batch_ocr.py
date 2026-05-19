#!/usr/bin/env python3
"""CLI for batch OCR of scanned PDFs using vision-language models.

Usage:
    python batch_ocr.py scan.pdf
    python batch_ocr.py scan.pdf --system-prompt "Romanization uses ğ, ħ, ž"
    python batch_ocr.py scan.pdf --pages 1-50 --dpi 300
    python batch_ocr.py scan.pdf --backend openrouter --model google/gemini-3.1-pro-preview
    python batch_ocr.py scan.pdf --resume
    python batch_ocr.py scan.pdf --background --log-file ./ocr.log
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
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
  %(prog)s scan.pdf --background --log-file ./ocr.log
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
        choices=["ollama", "ollama-local", "openrouter", "gemini"],
        default="ollama-local",
        help="Vision backend (default: ollama-local)",
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
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background (detached from terminal). Use --log-file to capture output.",
    )
    parser.add_argument(
        "--log-file",
        default="",
        help="Log file path for background mode (default: <output_dir>/<pdf>_ocr.log)",
    )
    parser.add_argument(
        "--pid-file",
        default="",
        help="PID file path for background mode (default: <output_dir>/<pdf>_ocr.pid)",
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


def _daemonize(log_file: Path, pid_file: Path):
    """Double-fork to detach from terminal completely."""
    # First fork
    pid = os.fork()
    if pid > 0:
        # Parent exits
        sys.exit(0)

    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # Second fork
    pid = os.fork()
    if pid > 0:
        # Parent exits
        sys.exit(0)

    # Redirect standard file descriptors to log file
    sys.stdout.flush()
    sys.stderr.flush()

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a+") as f:
        # Write PID
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))

        # Redirect stdout/stderr to log file
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

    # Ignore SIGHUP in case controlling terminal is closed
    signal.signal(signal.SIGHUP, signal.SIG_IGN)


def _build_command(args: argparse.Namespace) -> list[str]:
    """Rebuild the command line without --background and related flags."""
    cmd = [sys.executable, __file__]

    # Add all args except background-related ones
    cmd.append(args.pdf)
    if args.system_prompt:
        cmd.extend(["--system-prompt", args.system_prompt])
    if args.backend != "ollama-local":
        cmd.extend(["--backend", args.backend])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.dpi != 200:
        cmd.extend(["--dpi", str(args.dpi)])
    if args.pages:
        cmd.extend(["--pages", args.pages])
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    if args.output_name:
        cmd.extend(["--output-name", args.output_name])
    if args.resume:
        cmd.append("--resume")
    if args.delay != 2.0:
        cmd.extend(["--delay", str(args.delay)])
    if args.max_retries != 3:
        cmd.extend(["--max-retries", str(args.max_retries)])
    if args.json:
        cmd.append("--json")
    if args.quiet:
        cmd.append("--quiet")

    return cmd


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

    # Determine log and pid file paths
    log_file = Path(args.log_file) if args.log_file else output_dir / f"{pdf_path.stem}_ocr.log"
    pid_file = Path(args.pid_file) if args.pid_file else output_dir / f"{pdf_path.stem}_ocr.pid"

    # Handle background mode
    if args.background:
        # Check if already running
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                os.kill(old_pid, 0)  # Check if process exists
                print(f"⚠️  Background job already running (PID {old_pid}).", file=sys.stderr)
                print(f"   Log: {log_file}", file=sys.stderr)
                print(f"   To monitor: tail -f {log_file}", file=sys.stderr)
                print(f"   To stop: kill {old_pid}", file=sys.stderr)
                sys.exit(1)
            except (OSError, ValueError):
                # Stale PID file
                pid_file.unlink(missing_ok=True)

        # Use subprocess.Popen for a simpler detached process on Linux
        cmd = _build_command(args)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "a") as log_fh:
            # Write header
            log_fh.write(f"\n{'='*60}\n")
            log_fh.write(f"Background OCR started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_fh.write(f"Command: {' '.join(cmd)}\n")
            log_fh.write(f"{'='*60}\n\n")
            log_fh.flush()

            # Start detached process
            process = subprocess.Popen(
                cmd,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )

        # Write PID file
        pid_file.write_text(str(process.pid))

        print(f"🚀 Background OCR job started (PID {process.pid})")
        print(f"   Log file: {log_file}")
        print(f"   Output: {output_path}")
        print(f"   Monitor: tail -f {log_file}")
        print(f"   Stop: kill {process.pid}")
        print(f"   Resume supported: --resume flag is preserved")
        sys.exit(0)

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

    # Clean up PID file if it exists (background mode cleanup)
    pid_file.unlink(missing_ok=True)

    sys.exit(0 if result.pages_failed < result.pages_total else 1)


if __name__ == "__main__":
    main()
