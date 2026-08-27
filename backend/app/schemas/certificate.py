from enum import StrEnum
from pydantic import BaseModel
from app.config.certificate_links import CertificateType

class CertificateStatus(StrEnum):
    OK = "OK"
    AUSENTE = "AUSENTE"
    VENCIDA = "VENCIDA"
    CNPJ_DIVERGENTE = "CNPJ_DIVERGENTE"
    VALIDADE_NAO_IDENTIFICADA = "VALIDADE_NAO_IDENTIFICADA"
    REVISAR_MANUALMENTE = "REVISAR_MANUALMENTE"

class CertificateResult(BaseModel):
    type: CertificateType
    name: str
    short_name: str
    issuer: str
    status: CertificateStatus
    found: bool
    cnpj: str | None = None
    cnpj_formatted: str | None = None
    corporate_name: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None
    calculated_validity: bool = False
    validity_rule_text: str | None = None
    pages: list[int] = []
    snippet: str | None = None
    message: str
    issuance_url: str
    confidence_score: float = 0.0
    is_manually_overridden: bool = False
    manual_notes: str | None = None
