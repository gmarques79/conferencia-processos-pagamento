from pydantic import BaseModel

class SupplierCandidate(BaseModel):
    cnpj: str  # 14 digits
    cnpj_formatted: str
    corporate_name: str | None = None
    confidence: float  # 0 to 100
    occurrences: int = 1
    page_numbers: list[int] = []
    context_snippet: str | None = None

class SupplierInfo(BaseModel):
    cnpj: str | None = None
    cnpj_formatted: str | None = None
    corporate_name: str | None = None
    confidence: float = 0.0
    is_confirmed: bool = False
    needs_confirmation: bool = False
    candidates: list[SupplierCandidate] = []

class SupplierRuleResult(BaseModel):
    cnpj: str
    display_name: str
    report_required: bool
    report_name: str | None = None
    instructions: str
    warnings: list[str] = []
