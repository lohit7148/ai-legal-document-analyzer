"""
Document loader (Stage 2): turns an uploaded PDF or image into plain text.

PDF  -> read the embedded text layer with PyMuPDF. Pages that have almost no
        text (scanned pages) are rendered to an image and sent to OCR.
Image -> OCR directly.

The result is ordinary text that the user can review/edit in the editor
before pressing "Analyze Document", so OCR mistakes never go unnoticed.
The rest of the pipeline (Stage 1) is unchanged.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import List

from services import ocr

try:  # PyMuPDF >= 1.24.3 exposes the `pymupdf` name; older versions use `fitz`
    import pymupdf as fitz
except Exception:  # pragma: no cover
    import fitz

logger = logging.getLogger("document_loader")

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_PAGES = 30
MIN_CHARS_PER_PAGE = 40      # below this a PDF page is treated as "scanned"
LOW_OCR_CONFIDENCE = 0.6

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


class ExtractionError(Exception):
    """User-facing problem with the uploaded file."""


@dataclass
class ExtractionResult:
    text: str
    source_type: str
    pages: int
    method: str
    ocr_used: bool
    warnings: List[str] = field(default_factory=list)


def extract_from_bytes(filename: str, data: bytes) -> ExtractionResult:
    ext = os.path.splitext(filename or "")[1].lower()
    if not data:
        raise ExtractionError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ExtractionError(f"The file is too large (maximum {MAX_FILE_BYTES // (1024 * 1024)} MB).")
    if ext in PDF_EXTENSIONS:
        return _extract_pdf(data)
    if ext in IMAGE_EXTENSIONS:
        return _extract_image(data)
    raise ExtractionError("Unsupported file type. Please upload a PDF, PNG, JPG, BMP, TIFF or WEBP file.")


def _extract_pdf(data: bytes) -> ExtractionResult:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ExtractionError("This PDF could not be opened. It may be damaged.")

    if doc.needs_pass:
        doc.close()
        raise ExtractionError("This PDF is password-protected. Please remove the password and try again.")

    warnings: List[str] = []
    total_pages = doc.page_count
    pages_to_read = min(total_pages, MAX_PAGES)
    if total_pages > MAX_PAGES:
        warnings.append(f"Only the first {MAX_PAGES} of {total_pages} pages were read.")

    page_texts: List[str] = []
    ocr_pages = 0
    confidences: List[float] = []

    for i in range(pages_to_read):
        page = doc.load_page(i)
        text = page.get_text("text").strip()
        if len(text) < MIN_CHARS_PER_PAGE:
            # Probably a scanned page -> render to an image and OCR it.
            try:
                png = page.get_pixmap(dpi=200).tobytes("png")
                ocr_text, conf = ocr.image_to_text(png)
            except ocr.OCRNotAvailable as exc:
                doc.close()
                raise ExtractionError(
                    f"Page {i + 1} looks scanned and needs OCR, but the OCR engine is not installed. "
                    "Run: pip install rapidocr-onnxruntime"
                ) from exc
            if ocr_text.strip():
                text = ocr_text.strip()
                ocr_pages += 1
                confidences.append(conf)
        page_texts.append(text)
    doc.close()

    full_text = "\n\n".join(t for t in page_texts if t)
    if not full_text.strip():
        raise ExtractionError("No readable text was found in this PDF.")

    if ocr_pages == 0:
        method = "text-layer"
    elif ocr_pages == pages_to_read:
        method = "ocr"
    else:
        method = "text-layer+ocr"
    warnings += _ocr_warnings(confidences)
    return ExtractionResult(full_text, "pdf", pages_to_read, method, ocr_pages > 0, warnings)


def _extract_image(data: bytes) -> ExtractionResult:
    try:
        text, conf = ocr.image_to_text(data)
    except ocr.OCRNotAvailable as exc:
        raise ExtractionError(str(exc)) from exc
    except Exception:
        raise ExtractionError("This image could not be read. Please upload a clear PNG or JPG.")

    if not text.strip():
        raise ExtractionError("No text could be recognised in this image. Try a sharper, well-lit photo.")
    return ExtractionResult(text.strip(), "image", 1, "ocr", True, _ocr_warnings([conf]))


def _ocr_warnings(confidences: List[float]) -> List[str]:
    warnings = ["Text was recognised with OCR and may contain mistakes. Please review it before analysing."] if confidences else []
    if confidences and sum(confidences) / len(confidences) < LOW_OCR_CONFIDENCE:
        warnings.append("OCR confidence was low. Try a higher-resolution scan or a clearer photo.")
    return warnings
