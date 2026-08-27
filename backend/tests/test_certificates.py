from datetime import date
import pytest
from app.config.certificate_links import CertificateType
from app.schemas.certificate import CertificateStatus
from app.services.certificate_classifier import evaluate_all_certificates

FIXED_REF_DATE = date(2026, 8, 27)

def test_all_five_certificates_present_and_valid():
    pages = [
        # Page 1: Federal CND
        """
        MINISTÉRIO DA FAZENDA
        SECRETARIA DA RECEITA FEDERAL DO BRASIL
        PROCURADORIA-GERAL DA FAZENDA NACIONAL
        CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO
        CNPJ: 05.340.639/0001-30
        Nome: PRIME BENEFICIOS LTDA
        Ressalvado o direito de a Fazenda Nacional cobrar e inscrever quaisquer dívidas.
        Emitida em: 01/06/2026
        Válida até: 28/11/2026
        Código de controle: A123.B456.C789.D012
        """,
        # Page 2: FGTS CRF
        """
        CAIXA ECONÔMICA FEDERAL
        CERTIFICADO DE REGULARIDADE DO FGTS - CRF
        Inscrição: 05.340.639/0001-30
        Razão Social: PRIME BENEFICIOS LTDA
        A Caixa Econômica Federal certifica que a empresa encontra-se em situação regular perante o FGTS.
        Validade: 15/08/2026 a 15/09/2026
        Certificação Número: 20260815123456
        """,
        # Page 3: CNDT
        """
        PODER JUDICIÁRIO
        JUSTIÇA DO TRABALHO
        TRIBUNAL SUPERIOR DO TRABALHO
        CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS - CNDT
        Nome: PRIME BENEFICIOS LTDA
        CNPJ: 05.340.639/0001-30
        Certifica-se que NÃO CONSTAM débitos inadimplidos no Banco Nacional de Devedores Trabalhistas - BNDT.
        Expedição: 10/05/2026
        Validade: 06/11/2026
        Código de autenticação: 987654321/2026
        """,
        # Page 4: Declaração ICMS SEFAZ/SE
        """
        ESTADO DE SERGIPE
        SECRETARIA DE ESTADO DA FAZENDA
        DECLARAÇÃO DE RECOLHIMENTO DO ICMS
        Número da Declaração: 2026/009876
        CNPJ: 05.340.639/0001-30
        Declara-se para os devidos fins que o contribuinte encontra-se regular quanto ao recolhimento do ICMS.
        Data de Emissão: 01/08/2026
        Válida até: 31/08/2026
        Autenticação: ABC-123-XYZ-789
        """,
        # Page 5: CND Estadual SEFAZ/SE
        """
        ESTADO DE SERGIPE
        SECRETARIA DE ESTADO DA FAZENDA
        CERTIDÃO NEGATIVA DE DÉBITOS ESTADUAIS
        Certidão nº: 2026/123456
        CNPJ: 05.340.639/0001-30
        Razão Social: PRIME BENEFICIOS LTDA
        Certificamos que NÃO CONSTAM débitos relativos a tributos estaduais e dívida ativa estadual.
        Emitida em: 10/08/2026
        Válida até 10/10/2026
        Código de segurança: SEFAZ99887766
        """,
    ]

    results = evaluate_all_certificates(
        pages_text=pages,
        confirmed_supplier_cnpj="05340639000130",
        reference_date=FIXED_REF_DATE,
    )

    assert len(results) == 5
    for cert in results:
        assert cert.found is True
        assert cert.status == CertificateStatus.OK
        assert cert.cnpj == "05340639000130"

def test_missing_and_expired_certificates():
    # Only 1 certificate present, and it's expired
    pages = [
        """
        CAIXA ECONÔMICA FEDERAL
        CERTIFICADO DE REGULARIDADE DO FGTS - CRF
        CNPJ: 05.340.639/0001-30
        Situação: Regular perante o FGTS
        Válido até: 10/01/2026
        """,
    ]

    results = evaluate_all_certificates(
        pages_text=pages,
        confirmed_supplier_cnpj="05340639000130",
        reference_date=FIXED_REF_DATE,
    )

    fgts_res = next(r for r in results if r.type == CertificateType.FGTS)
    assert fgts_res.found is True
    assert fgts_res.status == CertificateStatus.VENCIDA
    assert fgts_res.expiration_date == "10/01/2026"

    # Other 4 should be AUSENTE
    for cert in results:
        if cert.type != CertificateType.FGTS:
            assert cert.found is False
            assert cert.status == CertificateStatus.AUSENTE

def test_divergent_cnpj():
    pages = [
        """
        MINISTÉRIO DA FAZENDA
        CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO
        CNPJ: 28.008.410/0001-06
        Válida até: 30/12/2026
        Código: 123456
        """
    ]

    results = evaluate_all_certificates(
        pages_text=pages,
        confirmed_supplier_cnpj="05340639000130",  # Expected Prime Beneficios, but doc is Bamex
        reference_date=FIXED_REF_DATE,
    )

    fed_res = next(r for r in results if r.type == CertificateType.FEDERAL)
    assert fed_res.found is True
    assert fed_res.status == CertificateStatus.CNPJ_DIVERGENTE
    assert fed_res.cnpj == "28008410000106"

def test_positive_debts_certificate():
    pages = [
        """
        PODER JUDICIÁRIO
        JUSTIÇA DO TRABALHO
        CERTIDÃO POSITIVA DE DÉBITOS TRABALHISTAS
        CNPJ: 05.340.639/0001-30
        Constam débitos inscritos no Banco Nacional de Devedores Trabalhistas.
        Validade: 30/12/2026
        """
    ]

    results = evaluate_all_certificates(
        pages_text=pages,
        confirmed_supplier_cnpj="05340639000130",
        reference_date=FIXED_REF_DATE,
    )

    cndt_res = next(r for r in results if r.type == CertificateType.CNDT)
    assert cndt_res.found is True
    assert cndt_res.status == CertificateStatus.REVISAR_MANUALMENTE

def test_checklist_false_positive_resistance():
    # An index page mentioning all certificates, but with no certificate body/codes
    checklist_page = """
    PROCESSO ADMINISTRATIVO Nº 001/2026
    ÍNDICE / SUMÁRIO / CHECKLIST DE DOCUMENTOS:
    - Fl. 10: Certidão Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União
    - Fl. 12: Certificado de Regularidade do FGTS - CRF
    - Fl. 14: Certidão Negativa de Débitos Trabalhistas - CNDT
    - Fl. 16: Declaração de Recolhimento do ICMS SEFAZ
    - Fl. 18: Certidão Negativa de Débitos Estaduais SEFAZ
    Despacho do fiscal.
    """

    results = evaluate_all_certificates(
        pages_text=[checklist_page],
        confirmed_supplier_cnpj="05340639000130",
        reference_date=FIXED_REF_DATE,
    )

    for cert in results:
        assert cert.found is False
        assert cert.status == CertificateStatus.AUSENTE
