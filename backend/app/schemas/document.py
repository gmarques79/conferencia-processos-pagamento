from enum import StrEnum
from pydantic import BaseModel

class AdditionalDocType(StrEnum):
    PAYMENT_DATA_SHEET = "PAYMENT_DATA_SHEET"
    ATESTO = "ATESTO"
    SUPPLIER_REPORT = "SUPPLIER_REPORT"

class DocumentStatus(StrEnum):
    OK = "OK"
    AUSENTE = "AUSENTE"
    REVISAR_MANUALMENTE = "REVISAR_MANUALMENTE"
    NAO_APLICAVEL = "NAO_APLICAVEL"

class AdditionalDocumentResult(BaseModel):
    type: AdditionalDocType
    name: str
    found: bool
    status: DocumentStatus
    pages: list[int] = []
    snippet: str | None = None
    message: str
    is_required: bool = True
    instructions: str | None = None
    warnings: list[str] = []
    is_manually_overridden: bool = False
