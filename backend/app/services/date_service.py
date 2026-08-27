from datetime import date, datetime, timedelta
import re
import unicodedata

MONTH_MAP = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "março": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
}

# Regex for numeric dates (DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY)
NUMERIC_DATE_REGEX = re.compile(
    r"\b(0?[1-9]|[12][0-9]|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20\d\d)\b"
)

# Regex for textual dates e.g. "27 de agosto de 2026"
TEXTUAL_DATE_REGEX = re.compile(
    r"\b(0?[1-9]|[12][0-9]|3[01])\s+de\s+([a-zA-ZçÇáÁéÉíÍóÓúÚ]+)\s+de\s+(20\d\d)\b",
    re.IGNORECASE,
)

# Regex for relative validity e.g. "válida por 180 dias", "validade de 30 dias"
RELATIVE_VALIDITY_REGEX = re.compile(
    r"(?:válid[ao]|validade)(?:\s+(?:por|de|pelo\s+prazo\s+de))?\s+(\d{1,3})\s+dias(?:\s+(?:a\s+contar|a\s+partir)\s+d[aeo]\s+(?:emiss[aã]o|data))?",
    re.IGNORECASE,
)

def remove_accents(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def parse_date_str(date_str: str) -> date | None:
    """Tries parsing a Brazilian date string in numeric or textual format."""
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Try numeric match
    m_num = NUMERIC_DATE_REGEX.search(date_str)
    if m_num:
        try:
            day = int(m_num.group(1))
            month = int(m_num.group(2))
            year = int(m_num.group(3))
            return date(year, month, day)
        except ValueError:
            pass

    # Try textual match
    m_text = TEXTUAL_DATE_REGEX.search(date_str)
    if m_text:
        day = int(m_text.group(1))
        month_name = remove_accents(m_text.group(2).lower())
        year = int(m_text.group(3))
        if month_name in MONTH_MAP:
            try:
                return date(year, MONTH_MAP[month_name], day)
            except ValueError:
                pass

    return None

def format_date_br(d: date | None) -> str | None:
    """Formats date to DD/MM/YYYY."""
    if not d:
        return None
    return d.strftime("%d/%m/%Y")

def extract_dates_from_text(text: str) -> list[date]:
    """Finds all valid dates in text, returned in order of appearance."""
    dates: list[date] = []
    
    # Check numeric dates
    for m in NUMERIC_DATE_REGEX.finditer(text):
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            dates.append(d)
        except ValueError:
            pass
            
    # Check textual dates
    for m in TEXTUAL_DATE_REGEX.finditer(text):
        month_name = remove_accents(m.group(2).lower())
        if month_name in MONTH_MAP:
            try:
                d = date(int(m.group(3)), MONTH_MAP[month_name], int(m.group(1)))
                dates.append(d)
            except ValueError:
                pass
                
    return dates

def extract_issue_and_expiration_dates(
    text: str,
) -> tuple[date | None, date | None, bool, str | None]:
    """
    Extracts (issue_date, expiration_date, is_calculated, validity_rule_text).
    """
    issue_date: date | None = None
    expiration_date: date | None = None
    calculated = False
    rule_text: str | None = None

    # Patterns for Expiration / Validity
    validity_patterns = [
        # "válida até 27/08/2026" / "validade até 27/08/2026" / "Válido até: 27/08/2026"
        r"(?:válid[ao]\s+at[eé]|validade\s+at[eé]|validade\s*:\s*at[eé]?|vencimento\s*:\s*|data\s+de\s+validade\s*:\s*|expira[cç][aã]o\s*:\s*)([^\n\r,;\.]{6,35})",
        # "válid[ao] de 01/01/2026 a 30/06/2026"
        r"(?:válid[ao]\s+de\s+[^\n\r,;]+\s+a\s+)([^\n\r,;\.]{6,35})",
        # "Validade desta certidão: 27/08/2026"
        r"(?:validade\s+desta\s+certid[aã]o\s*:\s*)([^\n\r,;\.]{6,35})",
    ]

    for pat in validity_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            extracted_d = parse_date_str(m.group(1))
            if extracted_d:
                expiration_date = extracted_d
                break

    # Patterns for Issue Date
    issue_patterns = [
        r"(?:emitid[ao]\s+em|data\s+de\s+emiss[aã]o\s*:?|emiss[aã]o\s*:|expedid[ao]\s+em|data\s+da\s+emiss[aã]o\s*:?)([^\n\r,;\.]{6,35})",
        r"(?:Bras[ií]lia|Aracaju|Salvador|S[aã]o\s+Paulo|Rio\s+de\s+Janeiro)[^\n\r\d]{1,30}(\d{1,2}\s+de\s+[a-zA-ZçÇáÁéÉíÍóÓúÚ]+\s+de\s+20\d\d)",
    ]

    for pat in issue_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            extracted_d = parse_date_str(m.group(1))
            if extracted_d:
                issue_date = extracted_d
                break

    # If expiration not found explicitly, check for relative rule: "válida por X dias a partir da emissão"
    if not expiration_date:
        m_rel = RELATIVE_VALIDITY_REGEX.search(text)
        if m_rel:
            days_count = int(m_rel.group(1))
            rule_text = f"Calculada a partir da regra textual do documento ({days_count} dias a partir da emissão)"
            if issue_date:
                expiration_date = issue_date + timedelta(days=days_count)
                calculated = True
            else:
                # If issue date not found specifically via keyword, check all dates in document
                all_dates = extract_dates_from_text(text)
                if all_dates:
                    # Lowest date is usually emission
                    issue_date = min(all_dates)
                    expiration_date = issue_date + timedelta(days=days_count)
                    calculated = True

    # If still neither found, but text has dates, check if we can safely infer
    if not issue_date and not expiration_date:
        all_dates = extract_dates_from_text(text)
        if len(all_dates) == 1:
            # Ambiguous: could be issue or expiration
            pass
        elif len(all_dates) >= 2:
            # If sorted, smallest is likely emission, largest likely expiration if plausible
            sorted_dates = sorted(all_dates)
            if sorted_dates[0] != sorted_dates[-1]:
                # If they are within 1 year of each other
                diff = (sorted_dates[-1] - sorted_dates[0]).days
                if 15 <= diff <= 366:
                    issue_date = sorted_dates[0]
                    expiration_date = sorted_dates[-1]

    return issue_date, expiration_date, calculated, rule_text

def is_certificate_expired(expiration_date: date | None, reference_date: date | None = None) -> bool:
    """Checks whether the certificate has expired compared to reference_date (default: today)."""
    if not expiration_date:
        return False
    ref = reference_date or date.today()
    return expiration_date < ref
