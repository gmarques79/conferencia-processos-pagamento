import io
import os
import shutil
import logging
import platform
from pathlib import Path
import pytesseract
from PIL import Image
import pymupdf as fitz
from app.config.settings import settings

logger = logging.getLogger("ocr_service")

class OcrService:
    def __init__(self):
        self._is_available: bool | None = None
        self._configured_tesseract_path: str | None = None
        self._available_languages: list[str] = []
        self._init_tesseract()

    def _init_tesseract(self):
        """Locates tesseract executable if available."""
        # 1. Custom configured path
        if settings.TESSERACT_PATH and Path(settings.TESSERACT_PATH).is_file():
            self._configured_tesseract_path = settings.TESSERACT_PATH
            pytesseract.pytesseract.tesseract_cmd = self._configured_tesseract_path
            self._is_available = True
            self._detect_languages()
            return

        # 2. In system PATH (Standard in Linux Docker containers & PATH-configured environments)
        which_path = shutil.which("tesseract")
        if which_path:
            self._configured_tesseract_path = which_path
            pytesseract.pytesseract.tesseract_cmd = which_path
            self._is_available = True
            self._detect_languages()
            return

        # 3. Common Windows install locations (only on Windows)
        if platform.system() == "Windows":
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
                    self._detect_languages()
                    return

        self._is_available = False

    def _detect_languages(self):
        """Checks available languages in Tesseract installation."""
        try:
            langs = pytesseract.get_languages()
            self._available_languages = langs
        except Exception:
            self._available_languages = []

    @property
    def is_available(self) -> bool:
        return bool(self._is_available)

    @property
    def available_languages(self) -> list[str]:
        return self._available_languages

    def extract_text_from_page_image(self, page: fitz.Page) -> str:
        """
        Renders a single PyMuPDF page to an in-memory image and executes Tesseract OCR.
        Image and memory buffers are immediately closed and released.
        """
        if not self.is_available:
            return ""

        image = None
        try:
            # Render page to pixmap with 2.0 scale (144 dpi) for accurate OCR
            matrix = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            pix = None  # Free pixmap memory immediately
            
            image = Image.open(io.BytesIO(img_bytes))
            
            # Select language: prefer 'por' if available
            lang_to_use = "por" if "por" in self._available_languages else settings.TESSERACT_LANG
            
            try:
                text = pytesseract.image_to_string(image, lang=lang_to_use)
            except Exception as e:
                logger.warning(f"OCR with lang '{lang_to_use}' failed: {e}. Retrying default.")
                text = pytesseract.image_to_string(image)
                
            return text or ""
        except Exception as e:
            logger.warning(f"Failed OCR on page: {e}")
            return ""
        finally:
            if image is not None:
                try:
                    image.close()
                except Exception:
                    pass

ocr_service = OcrService()
