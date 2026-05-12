#!/usr/bin/env python3
"""Core vision OCR processor for scanned PDFs.

Supports multiple backends (Ollama Cloud, OpenRouter, Gemini) with
configurable system prompts for context-aware extraction.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests


def _load_env(key: str) -> str:
    """Load from .env file if not in environment."""
    if val := os.environ.get(key):
        return val
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    raise KeyError(f"{key} not found in environment or ~/.hermes/.env")


@dataclass
class PageResult:
    page: int
    text: str
    status: str  # "success" | "failed" | "skipped"
    processing_time: float = 0.0
    model: str = ""
    error: str = ""


@dataclass
class ExtractionResult:
    source: str
    pages_total: int
    pages_processed: int
    pages_failed: int
    backend: str
    model: str
    system_prompt_hash: str
    extracted_at: str
    pages: list[PageResult] = field(default_factory=list)


class VisionBackend:
    """Abstract base for vision backends."""

    def __init__(self, model: str, delay: float = 1.0, max_retries: int = 3):
        self.model = model
        self.delay = delay
        self.max_retries = max_retries

    def extract_text(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OllamaBackend(VisionBackend):
    """Ollama Cloud native API backend."""

    BASE_URL = "https://ollama.com/api/chat"

    def __init__(self, model: str = "gemini-3-flash-preview:cloud", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = _load_env("OLLAMA_API_KEY")

    def extract_text(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> str:
        img_b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": f"{system_prompt}\n\n{user_prompt}",
                "images": [img_b64],
            }],
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Ollama API failed after {self.max_retries} retries: {e}")
                time.sleep(self.delay * (2 ** attempt))

        return ""


class OpenRouterBackend(VisionBackend):
    """OpenRouter backend with vision model routing."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str = "google/gemini-3.1-pro-preview", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = _load_env("OPENROUTER_API_KEY")

    def extract_text(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> str:
        img_b64 = base64.b64encode(image_bytes).decode()
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
            "HTTP-Referer": "https://hermes-agent.nousresearch.com",
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"OpenRouter failed after {self.max_retries} retries: {e}")
                time.sleep(self.delay * (2 ** attempt))

        return ""


class GeminiBackend(VisionBackend):
    """Direct Google Gemini API backend."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model: str = "gemini-3.1-pro-preview", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = _load_env("GEMINI_API_KEY")

    def extract_text(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> str:
        img_b64 = base64.b64encode(image_bytes).decode()
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{system_prompt}\n\n{user_prompt}"},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": img_b64,
                        },
                    },
                ],
            }],
        }

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Gemini failed after {self.max_retries} retries: {e}")
                time.sleep(self.delay * (2 ** attempt))

        return ""


class VisionPDFProcessor:
    """Main processor for extracting text from scanned PDFs via vision models."""

    def __init__(
        self,
        backend: str = "ollama",
        model: str = "",
        system_prompt: str = "",
        dpi: int = 200,
        delay: float = 2.0,
        max_retries: int = 3,
    ):
        self.backend_name = backend
        self.system_prompt = system_prompt
        self.dpi = dpi
        # Enforce minimum 2-second delay to stay under 30 RPM
        self.delay = max(delay, 2.0)
        self.max_retries = max_retries

        # Select backend
        model_defaults = {
            "ollama": "gemini-3-flash-preview:cloud",
            "openrouter": "google/gemini-3.1-pro-preview",
            "gemini": "gemini-3.1-pro-preview",
        }
        self.model = model or model_defaults.get(backend, model_defaults["ollama"])

        backend_classes = {
            "ollama": OllamaBackend,
            "openrouter": OpenRouterBackend,
            "gemini": GeminiBackend,
        }
        if backend not in backend_classes:
            raise ValueError(f"Unknown backend: {backend}. Use: {list(backend_classes.keys())}")

        self.backend = backend_classes[backend](
            model=self.model,
            delay=delay,
            max_retries=max_retries,
        )

    def _render_page(self, pdf_path: str, page_num: int) -> bytes:
        """Render a single PDF page to PNG bytes."""
        try:
            import fitz  # pymupdf
        except ImportError:
            raise ImportError("pymupdf not installed. Run: pip install pymupdf")

        doc = fitz.open(pdf_path)
        try:
            page = doc[page_num]
            # Calculate zoom for target DPI
            zoom = self.dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("png")
        finally:
            doc.close()

    def _get_checkpoint_path(self, pdf_path: str, output_dir: Path) -> Path:
        """Get path to checkpoint file for resume."""
        base = Path(pdf_path).stem
        h = hashlib.sha256((str(pdf_path) + self.system_prompt + self.backend_name + self.model).encode()).hexdigest()[:8]
        return output_dir / f".{base}_ocr_checkpoint_{h}.json"

    def _load_checkpoint(self, checkpoint_path: Path) -> dict:
        """Load checkpoint data."""
        if checkpoint_path.exists():
            return json.loads(checkpoint_path.read_text())
        return {"completed_pages": [], "results": {}}

    def _save_checkpoint(self, checkpoint_path: Path, checkpoint: dict):
        """Save checkpoint data."""
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2))

    def _default_system_prompt(self) -> str:
        """Default OCR system prompt."""
        base = (
            "You are an expert OCR system. Extract ALL text from this scanned document page.\n"
            "Rules:\n"
            "1. Extract ALL visible text exactly as it appears\n"
            "2. Preserve original language, special characters, and diacritics\n"
            "3. Use markdown formatting (tables, headers, lists) where appropriate\n"
            "4. Mark unclear text with [unclear: best_guess]\n"
            "5. If the page is blank or contains only illustrations, say so\n"
            "6. Output ONLY the extracted text and structure, no commentary\n"
        )
        if self.system_prompt:
            base += f"\nDocument context:\n{self.system_prompt}\n"
        return base

    def _default_user_prompt(self, page_num: int, total_pages: int) -> str:
        return f"Extract text from page {page_num + 1} of {total_pages}. Format as markdown."

    def process_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        pages: Optional[str] = None,
        resume: bool = False,
        progress_callback=None,
    ) -> ExtractionResult:
        """Process a PDF and extract text from all pages.

        Args:
            pdf_path: Path to input PDF
            output_path: Path for output markdown file
            pages: Page range like "1-10" or "1,3,5" (1-indexed)
            resume: Resume from checkpoint if exists
            progress_callback: Called with (page, total, status) for each page

        Returns:
            ExtractionResult with all metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Determine output path
        if output_path is None:
            output_path = pdf_path.parent / f"{pdf_path.stem}_ocr.md"
        output_path = Path(output_path)
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load PDF
        import fitz
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        doc.close()

        # Parse page range
        page_indices = list(range(total_pages))
        if pages:
            page_indices = self._parse_page_range(pages, total_pages)

        # Load checkpoint
        checkpoint_path = self._get_checkpoint_path(str(pdf_path), output_dir)
        checkpoint = self._load_checkpoint(checkpoint_path) if resume else {"completed_pages": [], "results": {}}

        completed = set(checkpoint.get("completed_pages", []))
        results: dict[int, PageResult] = {}
        for p in completed:
            if str(p) in checkpoint.get("results", {}):
                r = checkpoint["results"][str(p)]
                results[p] = PageResult(**r)

        system_prompt = self._default_system_prompt()
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:8]

        # Process pages
        start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        failed_count = 0

        for idx, page_num in enumerate(page_indices):
            if page_num in completed:
                if progress_callback:
                    progress_callback(page_num + 1, total_pages, "skipped")
                continue

            if progress_callback:
                progress_callback(page_num + 1, total_pages, "processing")

            page_start = time.time()
            try:
                # Render page
                img_bytes = self._render_page(str(pdf_path), page_num)

                # Extract via vision model
                user_prompt = self._default_user_prompt(page_num, total_pages)
                text = self.backend.extract_text(img_bytes, system_prompt, user_prompt)

                result = PageResult(
                    page=page_num + 1,
                    text=text,
                    status="success",
                    processing_time=round(time.time() - page_start, 2),
                    model=self.backend.model,
                )
            except Exception as e:
                failed_count += 1
                result = PageResult(
                    page=page_num + 1,
                    text="",
                    status="failed",
                    processing_time=round(time.time() - page_start, 2),
                    model=self.backend.model,
                    error=str(e),
                )

            results[page_num] = result
            completed.add(page_num)

            # Save checkpoint after each page
            checkpoint["completed_pages"] = sorted(completed)
            checkpoint["results"] = {
                str(k): {
                    "page": v.page,
                    "text": v.text,
                    "status": v.status,
                    "processing_time": v.processing_time,
                    "model": v.model,
                    "error": v.error,
                }
                for k, v in results.items()
            }
            self._save_checkpoint(checkpoint_path, checkpoint)

            if progress_callback:
                progress_callback(page_num + 1, total_pages, result.status)

            # Delay between requests
            if idx < len(page_indices) - 1:
                time.sleep(self.delay)

        # Assemble final output
        self._write_output(output_path, pdf_path.name, total_pages, results, start_time, prompt_hash)

        return ExtractionResult(
            source=str(pdf_path),
            pages_total=total_pages,
            pages_processed=len([r for r in results.values() if r.status == "success"]),
            pages_failed=failed_count,
            backend=self.backend_name,
            model=self.backend.model,
            system_prompt_hash=prompt_hash,
            extracted_at=start_time,
            pages=list(results.values()),
        )

    def _parse_page_range(self, pages: str, total: int) -> list[int]:
        """Parse page range string to list of 0-indexed page numbers."""
        indices = []
        for part in pages.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                indices.extend(range(int(start) - 1, int(end)))
            else:
                indices.append(int(part) - 1)
        return [i for i in indices if 0 <= i < total]

    def _write_output(
        self,
        output_path: Path,
        source_name: str,
        total_pages: int,
        results: dict[int, PageResult],
        timestamp: str,
        prompt_hash: str,
    ):
        """Write extracted text to markdown file."""
        lines = [
            f"# Extracted: {source_name}",
            "",
            "**Metadata:**",
            f"- Pages (total): {total_pages}",
            f"- Pages processed: {len([r for r in results.values() if r.status == 'success'])}",
            f"- Pages failed: {len([r for r in results.values() if r.status == 'failed'])}",
            f"- Backend: {self.backend_name}",
            f"- Model: {self.backend.model}",
            f"- System prompt hash: {prompt_hash}",
            f"- Extracted: {timestamp}",
            "",
            "---",
            "",
        ]

        for page_num in sorted(results.keys()):
            result = results[page_num]
            lines.append(f"## Page {result.page}")
            lines.append("")
            if result.status == "failed":
                lines.append(f"[ERROR: {result.error}]")
            elif not result.text.strip():
                lines.append("[Blank page or no extractable text]")
            else:
                lines.append(result.text)
            lines.append("")
            lines.append("---")
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
