from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.schemas.certificate import CertificateResult, CertificateStatus
from app.schemas.supplier import SupplierInfo, SupplierRuleResult
from app.schemas.document import AdditionalDocumentResult, DocumentStatus

class ProcessMetadata(BaseModel):
    id: str
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_pages: int
    file_size_bytes: int
    scanned_pages_count: int = 0
    is_ocr_used: bool = False
    ocr_available: bool = False

class FinalInstructions(BaseModel):
    supplier_name: str
    cnpj: str | None = None
    pending_items: list[str] = []
    completed_items: list[str] = []
    completion_message: str
    overall_status: str  # "REGULAR" | "PENDENTE"

class ProcessAnalysisResponse(BaseModel):
    id: str
    metadata: ProcessMetadata
    supplier: SupplierInfo
    certificates: list[CertificateResult]
    additional_documents: list[AdditionalDocumentResult]
    supplier_rules: SupplierRuleResult
    final_instructions: FinalInstructions
    warnings: list[str] = []
    total_pending: int = 0

class RecalculateRequest(BaseModel):
    analysis: ProcessAnalysisResponse
    new_supplier_cnpj: str | None = None
    new_supplier_name: str | None = None
