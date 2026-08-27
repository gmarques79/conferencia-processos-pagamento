from dataclasses import dataclass, field
from pathlib import Path
import fitz
from app.config.settings import settings
from app.services.ocr_service import ocr_service

@dataclass
class ExtractedPdfData:
    pages_text: list[str]
    total_pages: int
    scanned_pages: list[int] = field(default_factory=list)
    is_ocr_used: bool = False
    ocr_available: bool = False
    warnings: list[str] = field(default_factory=list)

class PdfTextExtractor:
    def __init__(self):
        self.char_threshold = settings.SCANNED_PAGE_CHAR_THRESHOLD

    def extract(self, pdf_path: str | Path) -> ExtractedPdfData:
        """
        Extracts text from each page of a PDF file using PyMuPDF.
        If pages have minimal text, attempts OCR if available, or records warning.
        """
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path_obj))
        except Exception as e:
            raise ValueError(f"Não foi possível abrir o PDF: {e}")

        total_pages = len(doc)
        pages_text: list[str] = []
        scanned_pages: list[int] = []
        ocr_used = False
        warnings: list[str] = []

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]
            
            # Native PyMuPDF text extraction
            native_text = page.get_text("text") or ""
            clean_text = native_text.strip()

            if len(clean_text) < self.char_threshold:
                # Potential scanned page
                scanned_pages.append(page_num)
                if ocr_service.is_available:
                    ocr_text = ocr_service.extract_text_from_page_image(page)
                    if len(ocr_text.strip()) > len(clean_text):
                        pages_text.append(ocr_text)
                        ocr_used = True
                        continue
                pages_text.append(clean_text)
            else:
                pages_text.append(clean_text)

        doc.close()

        if scanned_pages and not ocr_service.is_available:
            warnings.append(
                "Este PDF parece conter páginas digitalizadas e algumas informações não puderam ser analisadas automaticamente. "
                "Faça a conferência manual ou configure o OCR."
            )

        return ExtractedPdfData(
            pages_text=pages_text,
            total_pages=total_pages,
            scanned_pages=scanned_pages,
            is_ocr_used=ocr_used,
            ocr_available=ocr_service.is_available,
            warnings=warnings,
        )

pdf_extractor = PdfTextExtractor()
