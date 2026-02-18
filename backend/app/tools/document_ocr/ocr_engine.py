import os
from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text as pdf_extract_text

# OPTIONAL: explicitly set tesseract path (Windows)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
SUPPORTED_PDF_EXTS = {".pdf"}

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    # ---- IMAGE OCR ----
    if ext in SUPPORTED_IMAGE_EXTS:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip()

    # ---- PDF TEXT EXTRACTION (NO OCR) ----
    if ext in SUPPORTED_PDF_EXTS:
        text = pdf_extract_text(file_path)
        if not text or len(text.strip()) < 20:
            raise RuntimeError(
                "This PDF appears to be scanned. Please upload a photo (JPG/PNG)."
            )
        return text.strip()

    raise RuntimeError("Unsupported file type")
