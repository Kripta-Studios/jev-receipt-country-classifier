"""Adapter to the inspected trace-it reader, with explicit local-only operation."""

import hashlib
import io
from pathlib import Path
import sys
import time


class TraceReader:
    def __init__(self, repository, model_dir, cache_dir, threads=2, force_recompute=False):
        repository = Path(repository).resolve()
        if not (repository / "backend/app/features/ingestion/ocr/local.py").exists():
            raise ValueError("TRACE_REPO must contain the trace-it backend")
        sys.path.insert(0, str(repository / "backend"))
        from app.features.ingestion.config import Settings
        from app.features.ingestion.ocr.local import LocalOCR

        self.engine = LocalOCR(
            Settings(
                model_dir=Path(model_dir).resolve(),
                data_dir=Path(cache_dir).resolve(),
                ocr_mode="local",
                ocr_profile="experimental",
                ocr_threads=threads,
                ocr_force_recompute=force_recompute,
                vision_providers=(),
                text_providers=(),
            )
        )

    def image(self, image, page=1):
        from PIL import ImageOps

        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.width * image.height > 18_000_000:
            raise ValueError("Image exceeds the 18 megapixel limit")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        lines = self.engine.recognize(buffer.getvalue(), page, image.size)
        return [
            {"text": line.raw, "confidence": line.confidence, "bbox": line.bbox, "page": page}
            for line in lines
        ]

    def read(self, path):
        from PIL import Image

        path = Path(path)
        started = time.perf_counter()
        if path.stat().st_size > 25 * 1024 * 1024:
            raise ValueError("File exceeds the 25 MiB limit")
        content = path.read_bytes()
        lines = []
        native_pages = 0
        if path.suffix.lower() == ".txt":
            text = content.decode("utf-8-sig")
            lines = [
                {"text": line, "page": 1, "confidence": None, "bbox": None}
                for line in text.splitlines()
            ]
        elif content.startswith(b"%PDF"):
            import pymupdf

            with pymupdf.open(stream=content, filetype="pdf") as document:
                if len(document) > 20:
                    raise ValueError("PDF exceeds the 20 page limit")
                for i, page in enumerate(document):
                    text = page.get_text(sort=True).strip()
                    if sum(c.isalnum() for c in text) >= 40:
                        native_pages += 1
                        lines.extend(
                            {"text": line, "page": i + 1, "confidence": None, "bbox": None}
                            for line in text.splitlines()
                        )
                    else:
                        pix = page.get_pixmap(dpi=180)
                        with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
                            lines.extend(self.image(image, i + 1))
        else:
            with Image.open(io.BytesIO(content)) as image:
                lines = self.image(image)
        return {
            "text": "\n".join(line["text"] for line in lines),
            "lines": lines,
            "native_pages": native_pages,
            "elapsed_s": time.perf_counter() - started,
            "sha256": hashlib.sha256(content).hexdigest(),
        }
