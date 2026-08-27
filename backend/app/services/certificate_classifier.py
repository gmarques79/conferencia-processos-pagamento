import re
from datetime import date
from app.config.certificate_links import CertificateType, get_certificate_link_info
from app.schemas.certificate import CertificateResult, CertificateStatus
from app.services.cnpj_service import normalize_text, normalize_cnpj, format_cnpj, extract_cnpj_candidates
from app.services.date_service import (
    extract_issue_and_expiration_dates,
    is_certificate_expired,
    format_date_br,
)
from app.services.situation_evaluator import (
    evaluate_certificate_situation,
    EvaluatedSituation,
)

# Authentication / Control codes pattern
AUTH_CODE_REGEX = re.compile(
    r"(?:c[oó]digo\s+(?:de\s+)?(?:controle|autentica[cç][aã]o|valida[cç][aã]o|seguran[cç]a)|chave\s+de\s+acesso|autentica[cç][aã]o\s*:\s*|autenticidade\s+em|hash\s*:?)\s*[:\-]?\s*([A-Za-z0-9\.\-\/]{4,40})",
    re.IGNORECASE,
)

# Index / Checklist indicators (penalize if present to avoid false positives)
INDEX_CHECKLIST_KEYWORDS = [
    "indice",
    "sumario",
    "relacao de documentos",
    "checklist",
    "check-list",
    "despacho",
    "termo de referencia",
    "edital de licitacao",
    "minuta do contrato",
]

class PageClassification:
    def __init__(
        self,
        cert_type: CertificateType,
        page_num: int,
        score: float,
        text: str,
        matched_terms: list[str],
    ):
        self.cert_type = cert_type
        self.page_num = page_num
        self.score = score
        self.text = text
        self.matched_terms = matched_terms

def is_checklist_or_index_page(text_norm: str) -> bool:
    """Checks whether the page looks like a table of contents or checklist."""
    matches = sum(1 for kw in INDEX_CHECKLIST_KEYWORDS if kw in text_norm)
    has_index_structure = bool(re.search(r"\b(?:fls?\.?|folhas?|item\s*\d+)\b", text_norm, re.IGNORECASE))
    return (matches >= 1 and has_index_structure) or matches >= 2

def score_federal_certificate(text_norm: str, raw_text: str) -> tuple[float, list[str]]:
    score = 0.0
    terms = []

    # Title check
    if (
        "certidao negativa de debitos relativos aos tributos federais" in text_norm
        or "certidao de debitos relativos a creditos tributarios federais" in text_norm
        or "tributos federais e a divida ativa da uniao" in text_norm
    ):
        score += 45.0
        terms.append("Título da Certidão Federal")
    elif "tributos federais" in text_norm and "divida ativa" in text_norm:
        score += 30.0
        terms.append("Termos Federais e Dívida Ativa")

    # Issuer check
    if (
        "receita federal do brasil" in text_norm
        or "secretaria da receita federal" in text_norm
        or "procuradoria-geral da fazenda nacional" in text_norm
        or "pgfn" in text_norm
        or "ministerio da fazenda" in text_norm
    ):
        score += 25.0
        terms.append("Emissor Receita Federal/PGFN")

    # Auth code / control code
    if AUTH_CODE_REGEX.search(raw_text) or "codigo de controle" in text_norm:
        score += 15.0
        terms.append("Código de controle/autenticação")

    # Validity / dates
    if "valida ate" in text_norm or "validade" in text_norm or "emitida as" in text_norm:
        score += 15.0
        terms.append("Cláusula de validade/emissão")

    return score, terms

def score_fgts_certificate(text_norm: str, raw_text: str) -> tuple[float, list[str]]:
    score = 0.0
    terms = []

    # Title & main terms
    if "certificado de regularidade do fgts" in text_norm or "certificado de regularidade do empregador" in text_norm:
        score += 45.0
        terms.append("Título Certificado de Regularidade do FGTS")
    elif "crf" in text_norm and "fundo de garantia do tempo de servico" in text_norm:
        score += 40.0
        terms.append("CRF e Fundo de Garantia por extenso")
    elif "fundo de garantia do tempo de servico" in text_norm:
        score += 25.0
        terms.append("Fundo de Garantia do Tempo de Serviço")

    # Issuer check
    if "caixa economica federal" in text_norm or "caixa" in text_norm:
        score += 20.0
        terms.append("Emissor CAIXA")

    # Regularity statement
    if "situacao regular" in text_norm or "regular perante o fgts" in text_norm or "inscricao" in text_norm:
        score += 20.0
        terms.append("Declaração de situação regular")

    # Validity / Auth
    if "validade" in text_norm or "valida de" in text_norm or "certificacao numero" in text_norm:
        score += 15.0
        terms.append("Validade / Certificação CRF")

    return score, terms

def score_cndt_certificate(text_norm: str, raw_text: str) -> tuple[float, list[str]]:
    score = 0.0
    terms = []

    # Title
    if "certidao negativa de debitos trabalhistas" in text_norm or "certidao positiva de debitos trabalhistas" in text_norm:
        score += 45.0
        terms.append("Título CNDT")
    elif "cndt" in text_norm and "justica do trabalho" in text_norm:
        score += 35.0
        terms.append("CNDT e Justiça do Trabalho")
    elif "debitos trabalhistas" in text_norm:
        score += 20.0
        terms.append("Débitos Trabalhistas")

    # Issuer / System
    if (
        "banco nacional de devedores trabalhistas" in text_norm
        or "bndt" in text_norm
        or "tribunal superior do trabalho" in text_norm
        or "tst" in text_norm
        or "consolidacao das leis do trabalho" in text_norm
    ):
        score += 25.0
        terms.append("Emissor TST / BNDT")

    # Validity / Auth
    if "validade" in text_norm or "expedicao" in text_norm or AUTH_CODE_REGEX.search(raw_text):
        score += 15.0
        terms.append("Validade / Autenticação")

    return score, terms

def score_icms_declaration(text_norm: str, raw_text: str) -> tuple[float, list[str]]:
    score = 0.0
    terms = []

    # Title: Declaração de Recolhimento do ICMS
    if "declaracao de recolhimento do icms" in text_norm or "declaracao de recolhimento de icms" in text_norm or "declaracao de recolhimento" in text_norm:
        score += 45.0
        terms.append("Título Declaração de Recolhimento do ICMS")

    # SEFAZ Sergipe
    if "secretaria de estado da fazenda" in text_norm and ("sergipe" in text_norm or "sefaz" in text_norm):
        score += 30.0
        terms.append("SEFAZ Sergipe")
    elif "sefaz" in text_norm or "secretaria de estado da fazenda" in text_norm:
        score += 15.0
        terms.append("Secretaria da Fazenda")

    # Must distinctively separate from CND Estadual
    if "certidao negativa" in text_norm and not ("declaracao de recolhimento" in text_norm):
        score -= 40.0  # Penalize if it's the State CND

    if "numero da declaracao" in text_norm or "autenticacao" in text_norm or "icms" in text_norm:
        score += 15.0
        terms.append("Dados de autenticação da declaração ICMS")

    return score, terms

def score_state_cnd(text_norm: str, raw_text: str) -> tuple[float, list[str]]:
    score = 0.0
    terms = []

    # Title: Certidão Negativa Estadual
    if (
        "certidao negativa de debitos estaduais" in text_norm
        or "certidao negativa de tributos estaduais" in text_norm
        or "certidao negativa de debitos" in text_norm
        or "certidao de regularidade fiscal" in text_norm
    ):
        score += 40.0
        terms.append("Título Certidão Negativa de Débitos Estaduais")

    # SEFAZ Sergipe
    if "secretaria de estado da fazenda" in text_norm and ("sergipe" in text_norm or "sefaz" in text_norm):
        score += 30.0
        terms.append("SEFAZ Sergipe")
    elif "sefaz" in text_norm or "secretaria da fazenda" in text_norm:
        score += 15.0
        terms.append("Secretaria da Fazenda")

    # Must distinctively separate from Declaração de Recolhimento do ICMS
    if "declaracao de recolhimento do icms" in text_norm or "declaracao de recolhimento de icms" in text_norm:
        score -= 40.0  # Penalize if it's the ICMS Declaration

    if "tributos estaduais" in text_norm or "fazenda publica estadual" in text_norm or "divida ativa do estado" in text_norm:
        score += 15.0
        terms.append("Tributos Estaduais / Dívida Ativa Estadual")

    return score, terms

def classify_page(page_text: str, page_num: int) -> list[PageClassification]:
    """Classifies a single page against all 5 certificate types with scoring."""
    raw_text = page_text
    norm_text = normalize_text(page_text)
    
    if not norm_text or len(norm_text) < 30:
        return []

    is_index = is_checklist_or_index_page(norm_text)
    classifications: list[PageClassification] = []

    # 1. Federal
    score_fed, terms_fed = score_federal_certificate(norm_text, raw_text)
    if is_index:
        score_fed -= 50.0
    if score_fed >= 50.0 and len(terms_fed) >= 2:
        classifications.append(
            PageClassification(CertificateType.FEDERAL, page_num, score_fed, raw_text, terms_fed)
        )

    # 2. FGTS
    score_fgts, terms_fgts = score_fgts_certificate(norm_text, raw_text)
    if is_index:
        score_fgts -= 50.0
    if score_fgts >= 50.0 and len(terms_fgts) >= 2:
        classifications.append(
            PageClassification(CertificateType.FGTS, page_num, score_fgts, raw_text, terms_fgts)
        )

    # 3. CNDT
    score_cndt, terms_cndt = score_cndt_certificate(norm_text, raw_text)
    if is_index:
        score_cndt -= 50.0
    if score_cndt >= 50.0 and len(terms_cndt) >= 2:
        classifications.append(
            PageClassification(CertificateType.CNDT, page_num, score_cndt, raw_text, terms_cndt)
        )

    # 4. ICMS Declaration
    score_icms, terms_icms = score_icms_declaration(norm_text, raw_text)
    if is_index:
        score_icms -= 50.0
    if score_icms >= 50.0 and len(terms_icms) >= 2:
        classifications.append(
            PageClassification(CertificateType.ICMS_DECLARATION, page_num, score_icms, raw_text, terms_icms)
        )

    # 5. State CND
    score_state, terms_state = score_state_cnd(norm_text, raw_text)
    if is_index:
        score_state -= 50.0
    if score_state >= 50.0 and len(terms_state) >= 2:
        classifications.append(
            PageClassification(CertificateType.STATE_CND, page_num, score_state, raw_text, terms_state)
        )

    return classifications

def extract_snippet(text: str, target_terms: list[str], max_len: int = 250) -> str:
    """Extracts a relevant snippet justifying the classification."""
    if not text:
        return ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    # Try finding line containing primary match
    for line in lines:
        line_norm = normalize_text(line)
        if any(normalize_text(t) in line_norm for t in target_terms):
            return line[:max_len]
            
    # Fallback to first non-empty lines
    return " ".join(lines[:3])[:max_len]

def merge_contiguous_pages(page_classifications: list[PageClassification]) -> dict[CertificateType, list[PageClassification]]:
    """Groups classifications by certificate type and retains highest score or contiguous range."""
    grouped: dict[CertificateType, list[PageClassification]] = {}
    for item in page_classifications:
        grouped.setdefault(item.cert_type, []).append(item)

    # Sort each group by page_num
    for cert_type in grouped:
        grouped[cert_type].sort(key=lambda x: x.page_num)

    return grouped

def evaluate_all_certificates(
    pages_text: list[str],
    confirmed_supplier_cnpj: str | None = None,
    reference_date: date | None = None,
) -> list[CertificateResult]:
    """
    Evaluates all 5 mandatory certificates across all PDF pages.
    Returns a list of 5 CertificateResult items.
    """
    ref_date = reference_date or date.today()
    all_page_classifications: list[PageClassification] = []

    for page_idx, p_text in enumerate(pages_text):
        page_num = page_idx + 1
        page_classes = classify_page(p_text, page_num)
        all_page_classifications.extend(page_classes)

    grouped_classes = merge_contiguous_pages(all_page_classifications)
    results: list[CertificateResult] = []

    # Mandatory 5 certificate types in fixed order
    required_types = [
        CertificateType.FEDERAL,
        CertificateType.FGTS,
        CertificateType.CNDT,
        CertificateType.ICMS_DECLARATION,
        CertificateType.STATE_CND,
    ]

    for cert_type in required_types:
        link_info = get_certificate_link_info(cert_type)
        classifications = grouped_classes.get(cert_type, [])

        if not classifications:
            # AUSENTE
            results.append(
                CertificateResult(
                    type=cert_type,
                    name=link_info.name,
                    short_name=link_info.short_name,
                    issuer=link_info.issuer,
                    status=CertificateStatus.AUSENTE,
                    found=False,
                    cnpj=None,
                    cnpj_formatted=None,
                    corporate_name=None,
                    issue_date=None,
                    expiration_date=None,
                    pages=[],
                    snippet=None,
                    message="Não encontrada no processo.",
                    issuance_url=link_info.issuance_url,
                    confidence_score=0.0,
                )
            )
            continue

        # Found one or more pages
        # If contiguous, combine text; otherwise pick highest scoring page/cluster
        sorted_pages = sorted(list({c.page_num for c in classifications}))
        combined_text = "\n".join([c.text for c in classifications])
        combined_terms = list({term for c in classifications for term in c.matched_terms})
        avg_confidence = min(100.0, sum(c.score for c in classifications) / len(classifications))
        
        # Extract dates
        issue_date, exp_date, calculated_val, rule_text = extract_issue_and_expiration_dates(combined_text)
        
        # Extract CNPJs from certificate text
        cert_cnpjs = extract_cnpj_candidates([combined_text])
        cert_cnpj = cert_cnpjs[0].cnpj if cert_cnpjs else None
        cert_corporate_name = cert_cnpjs[0].corporate_name if cert_cnpjs else None
        
        # Evaluate situation (negativa vs positiva vs indeterminada)
        situation, situation_msg = evaluate_certificate_situation(cert_type, combined_text)
        
        snippet = extract_snippet(combined_text, combined_terms)

        # Status Decision Logic
        status: CertificateStatus
        msg: str

        # 1. Situation check: Positiva or indeterminate
        if situation == EvaluatedSituation.POSITIVA:
            status = CertificateStatus.REVISAR_MANUALMENTE
            msg = f"Atenção: {situation_msg} Verifique administrativamente se pode ser aceita."
        elif situation == EvaluatedSituation.POSITIVA_COM_EFEITO_NEGATIVA:
            # Check expiration and CNPJ
            if confirmed_supplier_cnpj and cert_cnpj and cert_cnpj != confirmed_supplier_cnpj:
                status = CertificateStatus.CNPJ_DIVERGENTE
                msg = f"CNPJ da certidão ({format_cnpj(cert_cnpj)}) diverge do fornecedor ({format_cnpj(confirmed_supplier_cnpj)})."
            elif exp_date and is_certificate_expired(exp_date, ref_date):
                status = CertificateStatus.VENCIDA
                msg = f"Certidão vencida em {format_date_br(exp_date)}. Emitir nova certidão."
            else:
                status = CertificateStatus.REVISAR_MANUALMENTE
                msg = "Certidão Positiva com Efeitos de Negativa. Revisar manualmente para confirmação."
        # 2. CNPJ Divergence Check
        elif confirmed_supplier_cnpj and cert_cnpj and cert_cnpj != confirmed_supplier_cnpj:
            status = CertificateStatus.CNPJ_DIVERGENTE
            msg = f"CNPJ da certidão ({format_cnpj(cert_cnpj)}) não corresponde ao fornecedor ({format_cnpj(confirmed_supplier_cnpj)})."
        # 3. Expiration Check
        elif exp_date is None:
            status = CertificateStatus.VALIDADE_NAO_IDENTIFICADA
            msg = "Validade não identificada — revisar manualmente."
        elif is_certificate_expired(exp_date, ref_date):
            status = CertificateStatus.VENCIDA
            msg = f"Certidão vencida em {format_date_br(exp_date)}. Emitir nova certidão."
        # 4. Confidence / low signal check
        elif avg_confidence < 50.0:
            status = CertificateStatus.REVISAR_MANUALMENTE
            msg = "Documento identificado com baixa confiança. Revisar manualmente."
        else:
            status = CertificateStatus.OK
            msg = f"Certidão encontrada e aparentemente regular. Válida até {format_date_br(exp_date)}."

        results.append(
            CertificateResult(
                type=cert_type,
                name=link_info.name,
                short_name=link_info.short_name,
                issuer=link_info.issuer,
                status=status,
                found=True,
                cnpj=cert_cnpj,
                cnpj_formatted=format_cnpj(cert_cnpj),
                corporate_name=cert_corporate_name,
                issue_date=format_date_br(issue_date),
                expiration_date=format_date_br(exp_date),
                calculated_validity=calculated_val,
                validity_rule_text=rule_text,
                pages=sorted_pages,
                snippet=snippet,
                message=msg,
                issuance_url=link_info.issuance_url,
                confidence_score=round(avg_confidence, 1),
            )
        )

    return results
