import pytest
from app.config.supplier_rules import get_supplier_rule, SUPPLIER_RULES_REGISTRY

def test_prime_beneficios_rule():
    # Test with normalized and formatted CNPJ
    rule = get_supplier_rule("05340639000130")
    assert rule.report_required is True
    assert rule.report_name == "Consumo Subunidade/Veículo"
    assert "aba Relatórios" in rule.instructions
    assert rule.display_name == "Prime Benefícios"

    rule_formatted = get_supplier_rule("05.340.639/0001-30")
    assert rule_formatted.report_required is True
    assert rule_formatted.report_name == "Consumo Subunidade/Veículo"

def test_bamex_manutencoes_rule():
    rule = get_supplier_rule("28008410000106")
    assert rule.report_required is True
    assert rule.report_name == "Manutenções"
    assert "Módulo de manutenção > Ordens de Serviço > Relatórios" in rule.instructions
    assert len(rule.warnings) >= 1
    assert "Finalizada (Somente)" in rule.warnings[0]
    assert rule.display_name == "Bamex Manutenções"

    rule_formatted = get_supplier_rule("28.008.410/0001-06")
    assert rule_formatted.report_required is True
    assert "Finalizada (Somente)" in rule_formatted.warnings[0]

def test_generic_unregistered_supplier_rule():
    # Banco do Brasil CNPJ
    rule = get_supplier_rule("00000000000191")
    assert rule.report_required is False
    assert rule.report_name is None
    assert "Relatório adicional: não necessário para este fornecedor." in rule.instructions
    assert len(rule.warnings) == 0

def test_empty_supplier_rule():
    rule = get_supplier_rule(None)
    assert rule.report_required is False
    assert rule.report_name is None
