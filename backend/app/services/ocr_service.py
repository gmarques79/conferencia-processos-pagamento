import io
import os
import shutil
from pathlib import Path
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from app.config.settings import settings

class OcrService:
    def __init__(self):
        self._is_available: bool | None = None
        self._configured_tesseract_path: str | None = None
        self._init_tesseract()

    def _init_tesseract(self):
        """Locates tesseract executable if available."""
        # 1. Custom setting
        if settings.TESSERACT_PATH and Path(settings.TESSERACT_PATH).is_file():
            self._configured_tesseract_path = settings.TESSERACT_PATH
            pytesseract.pytesseract.tesseract_cmd = self._configured_tesseract_path
            self._is_available = True
            return

        # 2. In system PATH
        which_path = shutil.which("tesseract")
        if which_path:
            self._configured_tesseract_path = which_path
            self._is_available = True
            return

        # 3. Common Windows install locations
        win_candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for candidate in win_candidates:
            if Path(candidate).is_file():
                self._configured_tesseract_path = candidate
                pytesseract.pytesseract.tesseract_cmd = candidate
                self._is_available = True
                return

        self._is_available = False

    @property
    def is_available(self) -> bool:
        return bool(self._is_available)

    def extract_text_from_page_image(self, page: fitz.Page) -> str:
        """
        Renders a PyMuPDF page to an in-memory image and executes Tesseract OCR.
        """
        if not self.is_available:
            return ""

        try:
            # Render page to pixmap with 2.0 scale (144 dpi) for better OCR accuracy
            matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            
            # Run OCR
            text = pytesseract.image_to_string(image, lang=settings.TESSERACT_LANG)
            return text
        except Exception:
            # If multi-language fails (e.g. por not installed), fallback to default eng/osd
            try:
                text = pytesseract.image_to_string(image)
                return text
            except Exception:
                return ""

ocr_service = OcrService()
