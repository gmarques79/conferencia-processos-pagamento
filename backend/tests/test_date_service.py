from datetime import date
import pytest
from app.services.date_service import (
    parse_date_str,
    extract_dates_from_text,
    extract_issue_and_expiration_dates,
    is_certificate_expired,
)

def test_parse_numeric_date():
    assert parse_date_str("27/08/2026") == date(2026, 8, 27)
    assert parse_date_str("01-01-2025") == date(2025, 1, 1)
    assert parse_date_str("31.12.2024") == date(2024, 12, 31)

def test_parse_textual_date():
    assert parse_date_str("27 de agosto de 2026") == date(2026, 8, 27)
    assert parse_date_str("05 de Maio de 2025") == date(2025, 5, 5)
    assert parse_date_str("1 de março de 2026") == date(2026, 3, 1)
    assert parse_date_str("31 de dezembro de 2026") == date(2026, 12, 31)

def test_extract_dates_from_text():
    sample = "Emitido em 10/05/2026 com validade até 20 de outubro de 2026."
    dates = extract_dates_from_text(sample)
    assert len(dates) == 2
    assert dates[0] == date(2026, 5, 10)
    assert dates[1] == date(2026, 10, 20)

def test_extract_explicit_issue_and_expiration():
    text = """
    SECRETARIA DA RECEITA FEDERAL DO BRASIL
    Data de emissão: 01/03/2026
    Válida até 28/08/2026
    Código de controle: A1B2.C3D4.E5F6
    """
    issue_date, exp_date, calc, rule = extract_issue_and_expiration_dates(text)
    assert issue_date == date(2026, 3, 1)
    assert exp_date == date(2026, 8, 28)
    assert calc is False
    assert rule is None

def test_extract_relative_validity_rule():
    text = """
    TRIBUNAL SUPERIOR DO TRABALHO
    Data de emissão: 10 de janeiro de 2026
    Esta certidão é válida por 180 dias a contar da emissão.
    """
    issue_date, exp_date, calc, rule = extract_issue_and_expiration_dates(text)
    assert issue_date == date(2026, 1, 10)
    # 10 Jan 2026 + 180 days = 9 July 2026
    assert exp_date == date(2026, 7, 9)
    assert calc is True
    assert "180 dias" in rule

def test_month_and_year_transitions():
    # Year end transition: 15/12/2025 + 30 days -> 14/01/2026
    text = """
    Data de emissão: 15/12/2025
    Validade de 30 dias a partir da data de emissão.
    """
    issue_date, exp_date, calc, rule = extract_issue_and_expiration_dates(text)
    assert issue_date == date(2025, 12, 15)
    assert exp_date == date(2026, 1, 14)
    assert calc is True

def test_is_certificate_expired():
    ref_date = date(2026, 8, 27)
    # Expired yesterday
    assert is_certificate_expired(date(2026, 8, 26), ref_date) is True
    # Expires today (not expired yet during the day)
    assert is_certificate_expired(date(2026, 8, 27), ref_date) is False
    # Expires tomorrow
    assert is_certificate_expired(date(2026, 8, 28), ref_date) is False
