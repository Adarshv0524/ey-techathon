import logging
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
from typing import Dict, Any, Optional
from pdfminer.high_level import extract_text as pdf_extract_text
from app.config import settings

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR processing engine using Tesseract"""
    
    def __init__(self):
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        self.confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
    
    async def process_image(self, image_bytes: bytes, doc_type: str) -> Dict[str, Any]:
        """
        Process image and extract text with confidence scores
        
        Args:
            image_bytes: Image file bytes
            doc_type: Type of document (salary_slip, pan_card, aadhaar)
            
        Returns:
            {
                "text": str,
                "confidence": float,
                "extracted_data": dict,
                "status": str
            }
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            return self._ocr_image(image, doc_type)
        
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_data": {},
                "status": "ERROR",
                "error": str(e)
            }
    
    async def process_pdf(self, pdf_bytes: bytes, doc_type: str) -> Dict[str, Any]:
        """Process PDF document — try pdfminer first, then OCR fallback."""
        try:
            # Try pdfminer text extraction first
            text = pdf_extract_text(BytesIO(pdf_bytes))
            extracted_data = self._extract_structured_data(text.strip(), doc_type) if text.strip() else {}

            # If pdfminer gave good text WITH structured data, use it
            if text.strip() and extracted_data:
                confidence = 0.9
                logger.info(f"PDF pdfminer extracted: {extracted_data}")
                return {
                    "text": text,
                    "confidence": confidence,
                    "extracted_data": extracted_data,
                    "status": "SUCCESS"
                }

            # Otherwise, always try OCR on the PDF images
            logger.info("pdfminer gave insufficient data, falling back to image OCR")
            ocr_result = await self._ocr_pdf_images(pdf_bytes, doc_type)

            # If OCR gave better results, use those
            ocr_extracted = ocr_result.get("extracted_data", {})
            if ocr_extracted and len(ocr_extracted) > len(extracted_data):
                return ocr_result

            # If pdfminer had SOME text but no structured data, return it with OCR data merged
            if text.strip():
                merged = {**extracted_data, **ocr_extracted}
                confidence = max(0.9 if text.strip() else 0.0, ocr_result.get("confidence", 0.0))
                status = "SUCCESS" if merged else ("SUCCESS" if confidence >= self.confidence_threshold else "LOW_CONFIDENCE")
                return {
                    "text": text,
                    "confidence": confidence,
                    "extracted_data": merged,
                    "status": status
                }

            return ocr_result

        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_data": {},
                "status": "ERROR",
                "error": str(e)
            }
    
    def _extract_structured_data(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract structured data based on document type"""
        import re
        
        data = {}
        
        if doc_type == "salary_slip":
            # Extract salary information
            salary_patterns = [
                r'(?:gross|net|basic)\s*(?:salary|pay)?\s*:?\s*₹?\s*([\d,]+)',
                r'₹\s*([\d,]+)',
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data["monthly_salary"] = match.group(1).replace(',', '')
                    break
        
        elif doc_type == "pan_card":
            # Extract PAN number
            pan_pattern = r'\b([A-Z]{5}\d{4}[A-Z])\b'
            match = re.search(pan_pattern, text)
            if match:
                data["pan_number"] = match.group(1)
        
        elif doc_type == "aadhaar":
            # Extract Aadhaar number — try multiple patterns (OCR may insert
            # spaces, dashes, or misread separators)
            aadhaar_patterns = [
                r'(\d{4}\s?\d{4}\s?\d{4})',          # 6826 4584 5686
                r'(\d{4}[\s\-\.]{0,2}\d{4}[\s\-\.]{0,2}\d{4})',  # with separators
                r'(\d{12})',                          # continuous 12 digits
            ]
            for pattern in aadhaar_patterns:
                matches = re.findall(pattern, text)
                for m in matches:
                    digits = re.sub(r'\D', '', m)
                    # Valid Aadhaar: 12 digits, first digit != 0 or 1
                    if len(digits) == 12 and digits[0] not in ('0', '1'):
                        data["aadhaar_number"] = m.strip()
                        break
                if "aadhaar_number" in data:
                    break

            # Try to extract name from Aadhaar card
            # Common patterns on Indian Aadhaar cards
            name_patterns = [
                # English name just before DOB/Date of Birth/जन्म
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*\n.*?(?:DOB|Date\s*of\s*Birth|जन्म)',
                # S/O, D/O, W/O, C/O patterns (back of card)
                r'(?:S/?O|D/?O|W/?O|C/?O)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
                # Name: or name label
                r'(?:name|नाम)\s*[:\-]?\s*([A-Za-z ]{3,40})',
                # Standalone line of 2-4 capitalized words (likely a name)
                r'(?:^|\n)\s*([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\s*(?:\n|$)',
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    name = match.group(1).strip()
                    # Filter out garbage: must have at least 2 words, no digits,
                    # no common Aadhaar boilerplate words
                    boilerplate = {"government", "india", "authority", "unique",
                                   "identification", "aadhaar", "male", "female",
                                   "proof", "identity", "address", "date", "birth"}
                    words = name.lower().split()
                    if (len(name) > 4
                        and len(words) >= 2
                        and not re.search(r'\d', name)
                        and not any(w in boilerplate for w in words)):
                        data["name"] = name
                        break

            # Extract DOB
            dob_patterns = [
                r'(?:DOB|Date\s*of\s*Birth|जन्म\s*तिथि)\s*[:/\-]?\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})',
                r'(\d{2}/\d{2}/\d{4})',
            ]
            for pattern in dob_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data["dob"] = match.group(1).strip()
                    break

            # Extract gender
            gender_match = re.search(r'\b(MALE|FEMALE|male|female|पुरुष|महिला)\b', text)
            if gender_match:
                g = gender_match.group(1).upper()
                if g in ('पुरुष',):
                    g = 'MALE'
                elif g in ('महिला',):
                    g = 'FEMALE'
                data["gender"] = g
        
        return data

    def _preprocess_image(self, image: Image.Image, binarize: bool = False) -> Image.Image:
        """Light preprocessing to improve OCR accuracy."""
        image = image.convert("L")
        image = ImageOps.autocontrast(image)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        width, height = image.size
        if max(width, height) < 1400:
            scale = 1400 / max(width, height)
            image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

        if binarize:
            image = image.point(lambda p: 255 if p > 140 else 0)
        return image

    def _lang_for_doc(self, doc_type: str) -> str:
        """Return Tesseract language string based on document type."""
        if doc_type == "aadhaar":
            # Aadhaar cards have Hindi + English
            try:
                # Check if hin is available
                import subprocess
                langs = subprocess.check_output(['tesseract', '--list-langs'],
                                                stderr=subprocess.STDOUT).decode()
                if 'hin' in langs:
                    return 'eng+hin'
            except Exception:
                pass
        return 'eng'

    def _ocr_image(self, image: Image.Image, doc_type: str) -> Dict[str, Any]:
        """Run OCR with multiple passes for best extraction."""
        lang = self._lang_for_doc(doc_type)
        best_result = None

        # Try different preprocessing + PSM combos
        attempts = [
            (False, '--psm 3'),   # Auto layout, no binarization
            (False, '--psm 6'),   # Uniform block, no binarization
            (True,  '--psm 3'),   # Auto layout, binarized
            (True,  '--psm 6'),   # Uniform block, binarized
        ]

        for binarize, psm in attempts:
            processed = self._preprocess_image(image, binarize=binarize)
            tess_config = f'{psm} -l {lang}'

            try:
                ocr_data = pytesseract.image_to_data(
                    processed,
                    output_type=pytesseract.Output.DICT,
                    config=tess_config
                )
            except Exception as e:
                logger.warning(f"OCR data attempt failed ({tess_config}): {e}")
                continue

            confidences = [
                int(conf) for conf in ocr_data.get('conf', [])
                if conf != '-1'
            ]

            if not confidences:
                continue

            avg_confidence = sum(confidences) / len(confidences) / 100.0

            try:
                full_text = pytesseract.image_to_string(processed, config=tess_config)
            except Exception:
                full_text = " ".join(
                    t for t, c in zip(ocr_data.get('text', []), ocr_data.get('conf', []))
                    if c != '-1' and t.strip()
                )

            extracted_data = self._extract_structured_data(full_text, doc_type)

            result = {
                "text": full_text,
                "confidence": avg_confidence,
                "extracted_data": extracted_data,
            }

            # If we found structured data, boost and return immediately
            if extracted_data:
                result["confidence"] = max(avg_confidence, self.confidence_threshold)
                result["status"] = "SUCCESS"
                logger.info(f"OCR extracted (binarize={binarize}, {psm}, lang={lang}): {extracted_data}")
                # If we got both aadhaar_number AND name, this is a great result
                if doc_type == "aadhaar" and "aadhaar_number" in extracted_data and "name" in extracted_data:
                    return result
                # Otherwise keep as best but try other combos for more fields
                if best_result is None or len(extracted_data) > len(best_result.get("extracted_data", {})):
                    best_result = result
                continue

            # Keep the best attempt by confidence
            if best_result is None or avg_confidence > best_result["confidence"]:
                best_result = result

        if best_result is None:
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_data": {},
                "status": "NO_TEXT_DETECTED"
            }

        avg_confidence = best_result["confidence"]
        if avg_confidence >= self.confidence_threshold:
            best_result["status"] = "SUCCESS"
        else:
            best_result["status"] = "LOW_CONFIDENCE"
        return best_result

    async def _ocr_pdf_images(self, pdf_bytes: bytes, doc_type: str) -> Dict[str, Any]:
        """OCR scanned PDFs by converting pages to images."""
        try:
            from pdf2image import convert_from_bytes
        except Exception as e:
            logger.error(f"pdf2image unavailable: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_data": {},
                "status": "NO_TEXT_DETECTED"
            }

        try:
            pages = convert_from_bytes(pdf_bytes, dpi=300, first_page=1, last_page=3)
            if not pages:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "extracted_data": {},
                    "status": "NO_TEXT_DETECTED"
                }

            combined_text = []
            best_conf = 0.0
            merged_extracted = {}
            for page in pages:
                result = self._ocr_image(page, doc_type)
                combined_text.append(result.get("text", ""))
                best_conf = max(best_conf, result.get("confidence", 0.0))
                # Merge per-page extracted data (keep first found for each key)
                for k, v in result.get("extracted_data", {}).items():
                    if k not in merged_extracted:
                        merged_extracted[k] = v

            full_text = "\n".join([t for t in combined_text if t])
            # Also try extraction on the full combined text
            combined_extracted = self._extract_structured_data(full_text, doc_type)
            # Merge: per-page results take precedence, then combined
            extracted_data = {**combined_extracted, **merged_extracted}

            if extracted_data and best_conf < self.confidence_threshold:
                best_conf = max(best_conf, self.confidence_threshold)
                status = "SUCCESS"
            elif full_text.strip():
                status = "SUCCESS" if best_conf >= self.confidence_threshold else "LOW_CONFIDENCE"
            else:
                status = "NO_TEXT_DETECTED"

            return {
                "text": full_text,
                "confidence": best_conf,
                "extracted_data": extracted_data,
                "status": status
            }
        except Exception as e:
            logger.error(f"PDF image OCR error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_data": {},
                "status": "ERROR",
                "error": str(e)
            }


ocr_engine = OCREngine()
