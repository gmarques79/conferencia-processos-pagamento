from pydantic import BaseModel

class SupplierRule(BaseModel):
    cnpj: str  # 14 digits normalized
    display_name: str
    report_required: bool
    report_name: str | None = None
    instructions: str
    warnings: list[str] = []

# Registered supplier rules by 14-digit normalized CNPJ
SUPPLIER_RULES_REGISTRY: dict[str, SupplierRule] = {
    "05340639000130": SupplierRule(
        cnpj="05340639000130",
        display_name="Prime Benefícios",
        report_required=True,
        report_name="Consumo Subunidade/Veículo",
        instructions="Este fornecedor exige o relatório Consumo Subunidade/Veículo. Para obtê-lo, acesse a aba Relatórios.",
        warnings=[],
    ),
    "28008410000106": SupplierRule(
        cnpj="28008410000106",
        display_name="Bamex Manutenções",
        report_required=True,
        report_name="Manutenções",
        instructions="Este fornecedor exige o relatório Manutenções. Acesse Módulo de manutenção > Ordens de Serviço > Relatórios.",
        warnings=["Antes de gerar o relatório, filtre o status por Finalizada (Somente)."],
    ),
}

def get_supplier_rule(cnpj: str | None) -> SupplierRule:
    """
    Returns the specific rule for the normalized CNPJ or a default rule if none registered.
    """
    if not cnpj:
        return SupplierRule(
            cnpj="",
            display_name="Fornecedor Não Identificado",
            report_required=False,
            report_name=None,
            instructions="Relatório adicional: não necessário para este fornecedor.",
            warnings=[],
        )

    clean_cnpj = "".join(filter(str.isdigit, cnpj))
    if clean_cnpj in SUPPLIER_RULES_REGISTRY:
        return SUPPLIER_RULES_REGISTRY[clean_cnpj]

    return SupplierRule(
        cnpj=clean_cnpj,
        display_name="Fornecedor Padrão",
        report_required=False,
        report_name=None,
        instructions="Relatório adicional: não necessário para este fornecedor.",
        warnings=[],
    )
