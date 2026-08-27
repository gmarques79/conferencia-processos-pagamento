import pytest
from app.services.cnpj_service import (
    normalize_cnpj,
    validate_cnpj,
    format_cnpj,
    extract_cnpj_candidates,
)

def test_normalize_cnpj():
    assert normalize_cnpj("05.340.639/0001-30") == "05340639000130"
    assert normalize_cnpj("28.008.410/0001-06") == "28008410000106"
    assert normalize_cnpj("  12345678000199  ") == "12345678000199"
    assert normalize_cnpj("") == ""
    assert normalize_cnpj(None) == ""

def test_format_cnpj():
    assert format_cnpj("05340639000130") == "05.340.639/0001-30"
    assert format_cnpj("28008410000106") == "28.008.410/0001-06"
    assert format_cnpj("05.340.639/0001-30") == "05.340.639/0001-30"
    assert format_cnpj("") == ""

def test_validate_cnpj():
    # Valid real CNPJs
    assert validate_cnpj("05.340.639/0001-30") is True
    assert validate_cnpj("05340639000130") is True
    assert validate_cnpj("28.008.410/0001-06") is True
    assert validate_cnpj("28008410000106") is True
    assert validate_cnpj("00.000.000/0001-91") is True  # Banco do Brasil
    assert validate_cnpj("00360305000104") is True  # Caixa

    # Invalid CNPJs
    assert validate_cnpj("05.340.639/0001-31") is False  # wrong digit
    assert validate_cnpj("00000000000000") is False  # repeated
    assert validate_cnpj("11111111111111") is False  # repeated
    assert validate_cnpj("123456") is False  # short
    assert validate_cnpj("") is False
    assert validate_cnpj(None) is False

def test_extract_cnpj_candidates_with_context():
    page1 = """
    ESTADO DE SERGIPE
    SECRETARIA DE ESTADO DA FAZENDA - CNPJ: 13.128.798/0001-44 (Contratante)
    
    PROCESSO ADMINISTRATIVO DE PAGAMENTO
    Dados da Contratada / Fornecedor:
    Razão Social: PRIME BENEFICIOS LTDA
    CNPJ: 05.340.639/0001-30
    Nota Fiscal nº 12345
    """
    
    candidates = extract_cnpj_candidates([page1])
    assert len(candidates) >= 1
    # The supplier CNPJ should have highest confidence
    top = candidates[0]
    assert top.cnpj == "05340639000130"
    assert top.cnpj_formatted == "05.340.639/0001-30"
    assert top.confidence > 50.0
