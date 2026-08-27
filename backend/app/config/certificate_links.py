from enum import StrEnum
from pydantic import BaseModel

class CertificateType(StrEnum):
    FEDERAL = "FEDERAL"
    FGTS = "FGTS"
    CNDT = "CNDT"
    ICMS_DECLARATION = "ICMS_DECLARATION"
    STATE_CND = "STATE_CND"

class CertificateLinkInfo(BaseModel):
    code: CertificateType
    name: str
    short_name: str
    issuer: str
    issuance_url: str
    description: str

CERTIFICATE_DEFINITIONS: dict[CertificateType, CertificateLinkInfo] = {
    CertificateType.FEDERAL: CertificateLinkInfo(
        code=CertificateType.FEDERAL,
        name="Certidão Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União",
        short_name="Certidão Federal (Receita Federal / PGFN)",
        issuer="Receita Federal / Procuradoria-Geral da Fazenda Nacional (PGFN)",
        issuance_url="https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/PJ/Emitir",
        description="Comprova regularidade fiscal quanto a tributos federais e dívida ativa da União.",
    ),
    CertificateType.FGTS: CertificateLinkInfo(
        code=CertificateType.FGTS,
        name="Certificado de Regularidade do FGTS (CRF)",
        short_name="CRF - FGTS (CAIXA)",
        issuer="Caixa Econômica Federal",
        issuance_url="https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",
        description="Comprova regularidade do empregador perante o Fundo de Garantia do Tempo de Serviço.",
    ),
    CertificateType.CNDT: CertificateLinkInfo(
        code=CertificateType.CNDT,
        name="Certidão Negativa de Débitos Trabalhistas (CNDT)",
        short_name="CNDT (Tribunal Superior do Trabalho)",
        issuer="Tribunal Superior do Trabalho (TST)",
        issuance_url="https://cndt-certidao.tst.jus.br/inicio.faces",
        description="Comprova a inexistência de débitos inadimplidos perante a Justiça do Trabalho.",
    ),
    CertificateType.ICMS_DECLARATION: CertificateLinkInfo(
        code=CertificateType.ICMS_DECLARATION,
        name="Declaração de Recolhimento do ICMS",
        short_name="Declaração de Recolhimento do ICMS (SEFAZ/SE)",
        issuer="Secretaria de Estado da Fazenda de Sergipe (SEFAZ/SE)",
        issuance_url="https://www.sefaz.se.gov.br/SitePages/servico.aspx?cod=10",
        description="Declaração emitida pela SEFAZ/SE para comprovação de regularidade no recolhimento do ICMS.",
    ),
    CertificateType.STATE_CND: CertificateLinkInfo(
        code=CertificateType.STATE_CND,
        name="Certidão Negativa de Débitos Estaduais",
        short_name="Certidão Negativa Estadual (SEFAZ/SE)",
        issuer="Secretaria de Estado da Fazenda de Sergipe (SEFAZ/SE)",
        issuance_url="https://www.sefaz.se.gov.br/SitePages/certidoes.aspx",
        description="Certidão de débitos estaduais emitida pela SEFAZ/SE.",
    ),
}

def get_certificate_link_info(cert_type: CertificateType) -> CertificateLinkInfo:
    """Returns official link and metadata for a given certificate type."""
    return CERTIFICATE_DEFINITIONS[cert_type]
