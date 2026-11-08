"""
OCR service (Stage 2).

Uses RapidOCR (ONNX runtime) -- a pure-pip OCR engine, so on Windows there
is NO separate program to install (unlike Tesseract). The engine is created
lazily on first use because loading it takes a few seconds.
"""

import io
import logging
from typing import List, Tuple

import numpy as np

logger = logging.getLogger("ocr")

_engine = None
MAX_SIDE_PX = 3000  # downscale huge photos so OCR stays fast on a laptop CPU


class OCRNotAvailable(Exception):
    """Raised when the OCR package is not installed."""


def is_available() -> bool:
    try:
        import rapidocr_onnxruntime  # noqa: F401
        return True
    except Exception:
        return False


def _get_engine():
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception as exc:
            raise OCRNotAvailable(
                "The OCR engine is not installed. Run: pip install rapidocr-onnxruntime"
            ) from exc
        logger.info("Initialising OCR engine...")
        _engine = RapidOCR()
    return _engine


def _lines_from_result(result) -> Tuple[str, float]:
    """Turn RapidOCR boxes into reading-order text and an average confidence."""
    if not result:
        return "", 0.0
    items = []
    for box, text, score in result:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append({"top": min(ys), "height": max(ys) - min(ys) or 1,
                      "left": min(xs), "text": str(text), "score": float(score)})
    items.sort(key=lambda i: i["top"])

    lines: List[List[dict]] = []
    for it in items:
        if lines and abs(it["top"] - lines[-1][0]["top"]) < 0.6 * lines[-1][0]["height"]:
            lines[-1].append(it)
        else:
            lines.append([it])

    out = []
    for line in lines:
        line.sort(key=lambda i: i["left"])
        out.append(" ".join(i["text"] for i in line))
    avg = sum(i["score"] for i in items) / len(items)
    return "\n".join(out), avg


def image_to_text(image_bytes: bytes) -> Tuple[str, float]:
    """Run OCR on PNG/JPEG/etc. bytes. Returns (text, average_confidence)."""
    from PIL import Image

    engine = _get_engine()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if max(img.size) > MAX_SIDE_PX:
        scale = MAX_SIDE_PX / max(img.size)
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    result, _ = engine(np.array(img))
    return _lines_from_result(result)
