import pytest
from app.config.certificate_links import CertificateType
from app.schemas.supplier import SupplierInfo, SupplierRuleResult
from app.schemas.certificate import CertificateResult, CertificateStatus
from app.schemas.document import AdditionalDocumentResult, AdditionalDocType, DocumentStatus
from app.services.instruction_service import generate_final_instructions

def test_dynamic_instructions_with_pending_items():
    supplier = SupplierInfo(
        cnpj="05340639000130",
        cnpj_formatted="05.340.639/0001-30",
        corporate_name="Prime Benefícios",
        confidence=95.0,
        is_confirmed=True,
    )

    rule = SupplierRuleResult(
        cnpj="05340639000130",
        display_name="Prime Benefícios",
        report_required=True,
        report_name="Consumo Subunidade/Veículo",
        instructions="Para obtê-lo, acesse a aba Relatórios.",
        warnings=[],
    )

    certificates = [
        CertificateResult(
            type=CertificateType.FEDERAL,
            name="Certidão Federal",
            short_name="Certidão Federal",
            issuer="Receita Federal",
            status=CertificateStatus.OK,
            found=True,
            expiration_date="20/12/2026",
            message="OK",
            issuance_url="https://url",
        ),
        CertificateResult(
            type=CertificateType.ICMS_DECLARATION,
            name="Declaração de Recolhimento do ICMS",
            short_name="Declaração ICMS",
            issuer="SEFAZ/SE",
            status=CertificateStatus.AUSENTE,
            found=False,
            message="Não encontrada",
            issuance_url="https://url",
        ),
    ]

    additional_docs = [
        AdditionalDocumentResult(
            type=AdditionalDocType.PAYMENT_DATA_SHEET,
            name="Folha de Dados para Pagamento",
            found=False,
            status=DocumentStatus.AUSENTE,
            message="Ausente",
        ),
        AdditionalDocumentResult(
            type=AdditionalDocType.ATESTO,
            name="Atesto",
            found=True,
            status=DocumentStatus.OK,
            pages=[5],
            message="Presente",
        ),
    ]

    instructions = generate_final_instructions(supplier, rule, certificates, additional_docs)
    assert instructions.overall_status == "PENDENTE"
    assert len(instructions.pending_items) == 3
    # Check pending items contains ICMS declaration, supplier report, and payment data sheet
    assert any("Declaração de Recolhimento do ICMS" in item for item in instructions.pending_items)
    assert any("Consumo Subunidade/Veículo" in item for item in instructions.pending_items)
    assert any("folha de dados para pagamento" in item.lower() for item in instructions.pending_items)

def test_dynamic_instructions_all_clean():
    supplier = SupplierInfo(
        cnpj="00000000000191",
        cnpj_formatted="00.000.000/0001-91",
        corporate_name="Empresa Regular",
        confidence=90.0,
        is_confirmed=True,
    )

    rule = SupplierRuleResult(
        cnpj="00000000000191",
        display_name="Empresa Regular",
        report_required=False,
        instructions="Não necessário.",
    )

    certificates = [
        CertificateResult(
            type=CertificateType.FEDERAL,
            name="Certidão Federal",
            short_name="Certidão Federal",
            issuer="Receita Federal",
            status=CertificateStatus.OK,
            found=True,
            expiration_date="20/12/2026",
            message="OK",
            issuance_url="https://url",
        )
    ]

    additional_docs = [
        AdditionalDocumentResult(
            type=AdditionalDocType.PAYMENT_DATA_SHEET,
            name="Folha de Dados para Pagamento",
            found=True,
            status=DocumentStatus.OK,
            pages=[2],
            message="Presente",
        ),
        AdditionalDocumentResult(
            type=AdditionalDocType.ATESTO,
            name="Atesto",
            found=True,
            status=DocumentStatus.OK,
            pages=[3],
            message="Presente",
        ),
    ]

    instructions = generate_final_instructions(supplier, rule, certificates, additional_docs)
    assert instructions.overall_status == "REGULAR"
    assert len(instructions.pending_items) == 0
    assert "Nenhuma pendência automática identificada." in instructions.completion_message
