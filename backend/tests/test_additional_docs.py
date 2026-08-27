import pytest
from app.schemas.supplier import SupplierRuleResult
from app.schemas.document import AdditionalDocType, DocumentStatus
from app.services.additional_docs_service import evaluate_additional_documents

def test_payment_data_sheet_and_atesto_detected():
    pages = [
        # Page 1: Folha de Dados para Pagamento
        """
        FOLHA DE INFORMAÇÕES BANCÁRIAS E DADOS PARA PAGAMENTO
        Banco: Banco do Brasil (001)
        Agência: 1234-5
        Conta Corrente: 98765-4
        Chave PIX: financeiro@empresa.com.br
        Favorecido: PRIME BENEFICIOS LTDA
        """,
        # Page 2: Atesto
        """
        TERMO DE ATESTO E RECEBIMENTO
        ATESTO para os devidos fins de direito que os serviços foram prestados a contento,
        em conformidade com o Contrato Administrativo nº 10/2026 e a Nota Fiscal anexa.
        Data: 20/08/2026
        Fiscal do Contrato: João da Silva
        """,
    ]

    rule = SupplierRuleResult(
        cnpj="05340639000130",
        display_name="Prime Benefícios",
        report_required=True,
        report_name="Consumo Subunidade/Veículo",
        instructions="Acessar aba Relatórios.",
        warnings=[],
    )

    docs = evaluate_additional_documents(pages, rule)
    assert len(docs) == 3

    # Supplier report
    rep = next(d for d in docs if d.type == AdditionalDocType.SUPPLIER_REPORT)
    assert rep.is_required is True
    assert rep.status == DocumentStatus.REVISAR_MANUALMENTE

    # Payment data sheet
    pay = next(d for d in docs if d.type == AdditionalDocType.PAYMENT_DATA_SHEET)
    assert pay.found is True
    assert pay.status == DocumentStatus.OK
    assert pay.pages == [1]

    # Atesto
    atesto = next(d for d in docs if d.type == AdditionalDocType.ATESTO)
    assert atesto.found is True
    assert atesto.status == DocumentStatus.OK
    assert atesto.pages == [2]

def test_additional_docs_missing_and_generic_supplier():
    pages = ["Documento qualquer sem dados bancários e sem termo de recebimento."]

    rule = SupplierRuleResult(
        cnpj="00000000000191",
        display_name="Fornecedor Padrão",
        report_required=False,
        report_name=None,
        instructions="Não necessário",
        warnings=[],
    )

    docs = evaluate_additional_documents(pages, rule)
    rep = next(d for d in docs if d.type == AdditionalDocType.SUPPLIER_REPORT)
    assert rep.is_required is False
    assert rep.status == DocumentStatus.NAO_APLICAVEL

    pay = next(d for d in docs if d.type == AdditionalDocType.PAYMENT_DATA_SHEET)
    assert pay.found is False
    assert pay.status == DocumentStatus.AUSENTE

    atesto = next(d for d in docs if d.type == AdditionalDocType.ATESTO)
    assert atesto.found is False
    assert atesto.status == DocumentStatus.AUSENTE
