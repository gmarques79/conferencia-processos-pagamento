from enum import StrEnum
import re
from app.config.certificate_links import CertificateType
from app.services.cnpj_service import normalize_text

class EvaluatedSituation(StrEnum):
    REGULAR = "REGULAR"
    POSITIVA = "POSITIVA"
    POSITIVA_COM_EFEITO_NEGATIVA = "POSITIVA_COM_EFEITO_NEGATIVA"
    INDETERMINADA = "INDETERMINADA"

def evaluate_certificate_situation(
    cert_type: CertificateType, text: str
) -> tuple[EvaluatedSituation, str]:
    """
    Evaluates whether the certificate content indicates a favorable / regular / negative situation.
    Returns (EvaluatedSituation, explanation_message).
    """
    norm = normalize_text(text)

    # 1. Check for explicit "CERTIDÃO POSITIVA" (without "com efeitos de negativa")
    is_positiva_pura = False
    if "certidao positiva" in norm:
        if "efeitos de negativa" in norm or "efeito de negativa" in norm:
            return (
                EvaluatedSituation.POSITIVA_COM_EFEITO_NEGATIVA,
                "Certidão Positiva com Efeitos de Negativa identificada.",
            )
        else:
            return (
                EvaluatedSituation.POSITIVA,
                "Certidão Positiva identificada (débitos existentes).",
            )

    if cert_type == CertificateType.FEDERAL:
        # Check Federal negative or positive with negative effects
        if "certidao negativa" in norm or "nao constam debitos" in norm or "inexistencia de debitos" in norm:
            return EvaluatedSituation.REGULAR, "Certidão Negativa de Débitos Federais regular."
        if "efeitos de negativa" in norm or "efeito de negativa" in norm:
            return (
                EvaluatedSituation.POSITIVA_COM_EFEITO_NEGATIVA,
                "Certidão com efeitos de negativa identificada.",
            )
        return EvaluatedSituation.REGULAR, "Certidão Federal identificada."

    elif cert_type == CertificateType.FGTS:
        # FGTS CRF situation
        if "situacao regular" in norm or "esta em situacao regular" in norm or "encontra-se em situacao regular" in norm or "regular perante o fgts" in norm or "regularidade" in norm:
            return EvaluatedSituation.REGULAR, "Situação regular perante o FGTS."
        if "irregular" in norm or "pendencia" in norm:
            return EvaluatedSituation.POSITIVA, "FGTS com indicação de pendência ou situação não regular."
        return EvaluatedSituation.REGULAR, "Certificado de Regularidade do FGTS identificado."

    elif cert_type == CertificateType.CNDT:
        # CNDT
        if "certidao negativa" in norm or "nao consta" in norm or "nao constam debitos" in norm or "inexistencia de debitos" in norm:
            return EvaluatedSituation.REGULAR, "Certidão Negativa de Débitos Trabalhistas regular."
        if "efeitos de negativa" in norm:
            return (
                EvaluatedSituation.POSITIVA_COM_EFEITO_NEGATIVA,
                "CNDT Positiva com Efeitos de Negativa.",
            )
        return EvaluatedSituation.REGULAR, "CNDT identificada."

    elif cert_type == CertificateType.ICMS_DECLARATION:
        # SEFAZ ICMS Declaration
        if "regular" in norm or "recolhimento" in norm or "nada consta" in norm or "quitado" in norm:
            return EvaluatedSituation.REGULAR, "Declaração de Recolhimento do ICMS regular."
        return EvaluatedSituation.REGULAR, "Declaração de Recolhimento do ICMS identificada."

    elif cert_type == CertificateType.STATE_CND:
        # SEFAZ State CND
        if "certidao negativa" in norm or "nao constam debitos" in norm or "inexistencia de debitos" in norm or "quitacao" in norm:
            return EvaluatedSituation.REGULAR, "Certidão Negativa de Débitos Estaduais regular."
        return EvaluatedSituation.REGULAR, "Certidão Estadual identificada."

    return EvaluatedSituation.INDETERMINADA, "Situação não pôde ser determinada com precisão."
