from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.certificate import CertificateResult, CertificateStatus
from app.schemas.supplier import SupplierInfo, SupplierRuleResult
from app.schemas.document import AdditionalDocumentResult, DocumentStatus

class ProcessMetadata(BaseModel):
    id: str
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
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

class ProcessSummary(BaseModel):
    id: str
    filename: str
    created_at: datetime
    cnpj: str | None = None
    supplier_name: str | None = None
    total_pending: int
    overall_status: str
    total_pages: int

class UpdateSupplierRequest(BaseModel):
    cnpj: str
    corporate_name: str | None = None

class UpdateCertificateOverrideRequest(BaseModel):
    cert_type: str
    status: CertificateStatus
    found: bool
    manual_notes: str | None = None

class UpdateDocOverrideRequest(BaseModel):
    doc_type: str
    status: DocumentStatus
    found: bool
