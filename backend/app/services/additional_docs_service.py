import re
from app.schemas.document import AdditionalDocumentResult, AdditionalDocType, DocumentStatus
from app.schemas.supplier import SupplierRuleResult
from app.services.cnpj_service import normalize_text

PAYMENT_DATA_PHRASES = [
    "dados para pagamento",
    "dados de pagamento",
    "dados bancarios",
    "dados bancários",
    "informacoes bancarias",
    "informações bancárias",
    "dados para credito",
    "dados para crédito",
    "ordem de pagamento bancario",
]

BANK_KEYWORDS = ["banco", "agencia", "agência", "conta corrente", "chave pix", "pix"]

NEGATION_PREFIXES = ["sem dados", "nao ha dados", "ausencia de dados"]

ATESTO_PHRASES = [
    "atesto",
    "atesto que",
    "atesto para os devidos fins",
    "servicos foram prestados",
    "serviços foram prestados",
    "material foi recebido",
    "materiais foram recebidos",
    "termo de recebimento",
    "termo de atesto",
    "recebimento definitivo",
    "recebimento provisorio",
    "recebimento provisório",
    "fiscal do contrato",
    "gestor do contrato",
]

def check_payment_data_sheet(pages_text: list[str]) -> tuple[bool, list[int], str | None]:
    """
    Checks if a payment data sheet is present using a combination of signals.
    Returns (found, pages, snippet).
    """
    matching_pages: list[int] = []
    snippet: str | None = None

    for page_idx, raw_text in enumerate(pages_text):
        page_num = page_idx + 1
        norm_text = normalize_text(raw_text)

        # Check if text is only a negation
        if any(neg in norm_text for neg in NEGATION_PREFIXES) and not ("agencia" in norm_text or "conta" in norm_text or "pix" in norm_text):
            continue

        # Direct explicit phrase match + banking context
        has_direct_phrase = any(phrase in norm_text for phrase in PAYMENT_DATA_PHRASES)
        bank_signals_count = sum(1 for kw in BANK_KEYWORDS if kw in norm_text)

        # Must have direct phrase and at least one bank detail, OR strong combination of bank details (>=3)
        if (has_direct_phrase and bank_signals_count >= 1) or (bank_signals_count >= 3 and "pagamento" in norm_text):
            matching_pages.append(page_num)
            if not snippet:
                for line in raw_text.split("\n"):
                    l_norm = normalize_text(line)
                    if any(p in l_norm for p in PAYMENT_DATA_PHRASES) or "banco" in l_norm:
                        snippet = line.strip()[:200]
                        break

    return len(matching_pages) > 0, matching_pages, snippet

ATESTO_NEGATION_PREFIXES = [
    "sem atesto",
    "sem termo",
    "ausencia de atesto",
    "nao ha atesto",
    "falta de atesto",
]

def check_atesto(pages_text: list[str]) -> tuple[bool, list[int], str | None]:
    """
    Checks if atesto is present using keyword combinations.
    Returns (found, pages, snippet).
    """
    matching_pages: list[int] = []
    snippet: str | None = None

    for page_idx, raw_text in enumerate(pages_text):
        page_num = page_idx + 1
        norm_text = normalize_text(raw_text)

        # Check if text is only a negation
        if any(neg in norm_text for neg in ATESTO_NEGATION_PREFIXES) and not ("servicos foram prestados" in norm_text or "material foi recebido" in norm_text or "fiscal" in norm_text):
            continue

        # Strong matches
        if any(p in norm_text for p in ATESTO_PHRASES):
            matching_pages.append(page_num)
            if not snippet:
                for line in raw_text.split("\n"):
                    l_norm = normalize_text(line)
                    if any(p in l_norm for p in ATESTO_PHRASES):
                        snippet = line.strip()[:200]
                        break

    return len(matching_pages) > 0, matching_pages, snippet

def evaluate_additional_documents(
    pages_text: list[str],
    supplier_rule: SupplierRuleResult,
) -> list[AdditionalDocumentResult]:
    """
    Evaluates additional documents:
    1. Supplier Specific Report
    2. Folha de dados para pagamento
    3. Atesto
    """
    docs: list[AdditionalDocumentResult] = []

    # 1. Supplier Report
    if supplier_rule.report_required:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.SUPPLIER_REPORT,
                name=f"Relatório: {supplier_rule.report_name}",
                found=False,  # Internal report needs to be generated / verified
                status=DocumentStatus.REVISAR_MANUALMENTE,
                pages=[],
                snippet=None,
                message=supplier_rule.instructions,
                is_required=True,
                instructions=supplier_rule.instructions,
                warnings=supplier_rule.warnings,
            )
        )
    else:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.SUPPLIER_REPORT,
                name="Relatório Adicional de Fornecedor",
                found=True,
                status=DocumentStatus.NAO_APLICAVEL,
                pages=[],
                snippet=None,
                message="Relatório adicional: não necessário para este fornecedor.",
                is_required=False,
                instructions="Não necessário para este fornecedor.",
                warnings=[],
            )
        )

    # 2. Folha de dados para pagamento
    payment_found, payment_pages, payment_snippet = check_payment_data_sheet(pages_text)
    if payment_found:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.PAYMENT_DATA_SHEET,
                name="Folha de Dados para Pagamento",
                found=True,
                status=DocumentStatus.OK,
                pages=payment_pages,
                snippet=payment_snippet,
                message="Folha de dados bancários/pagamento identificada no processo.",
                is_required=True,
                instructions="Conferir se os dados bancários correspondem aos da nota fiscal.",
                warnings=[],
            )
        )
    else:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.PAYMENT_DATA_SHEET,
                name="Folha de Dados para Pagamento",
                found=False,
                status=DocumentStatus.AUSENTE,
                pages=[],
                snippet=None,
                message="Folha de dados para pagamento não identificada. Verifique se precisa ser adicionada.",
                is_required=True,
                instructions="Adicionar folha contendo os dados bancários para crédito do pagamento.",
                warnings=[],
            )
        )

    # 3. Atesto
    atesto_found, atesto_pages, atesto_snippet = check_atesto(pages_text)
    if atesto_found:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.ATESTO,
                name="Atesto do Serviço / Material",
                found=True,
                status=DocumentStatus.OK,
                pages=atesto_pages,
                snippet=atesto_snippet,
                message="Atesto identificado no processo.",
                is_required=True,
                instructions="Conferir a assinatura e data do servidor responsável pelo atesto.",
                warnings=[],
            )
        )
    else:
        docs.append(
            AdditionalDocumentResult(
                type=AdditionalDocType.ATESTO,
                name="Atesto do Serviço / Material",
                found=False,
                status=DocumentStatus.AUSENTE,
                pages=[],
                snippet=None,
                message="Atesto não identificado. Adicione o atesto antes de finalizar o processo.",
                is_required=True,
                instructions="Adicionar o termo de atesto assinado pelo responsável.",
                warnings=[],
            )
        )

    return docs
