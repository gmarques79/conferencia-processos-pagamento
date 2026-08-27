import re
import unicodedata
from app.schemas.supplier import SupplierCandidate

CNPJ_REGEX = re.compile(
    r"(?<!\d)(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{14})(?!\d)"
)

# Context weights
POSITIVE_CONTEXT_KEYWORDS = [
    ("fornecedor", 30),
    ("fornecedora", 30),
    ("dados do fornecedor", 40),
    ("contratada", 35),
    ("contratado", 30),
    ("dados da contratada", 40),
    ("credor", 30),
    ("credora", 30),
    ("razao social", 25),
    ("razão social", 25),
    ("nome empresarial", 25),
    ("nota fiscal", 25),
    ("danfe", 25),
    ("prestador", 25),
    ("prestadora", 25),
    ("empresa", 15),
    ("favorecido", 25),
    ("proponente", 20),
    ("emitente", 20),
]

NEGATIVE_CONTEXT_KEYWORDS = [
    ("contratante", -35),
    ("orgao", -30),
    ("órgão", -30),
    ("secretaria de estado", -40),
    ("governo do estado", -40),
    ("prefeitura", -40),
    ("tribunal", -35),
    ("receita federal", -30),
    ("caixa economica", -30),
    ("procuradoria", -30),
]

def normalize_text(text: str) -> str:
    """Normalizes text by removing diacritics and excessive whitespace, converting to lower."""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", text)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return " ".join(only_ascii.lower().split())

def normalize_cnpj(cnpj: str | None) -> str:
    """Strips formatting from CNPJ, returning only digits."""
    if not cnpj:
        return ""
    digits = "".join(filter(str.isdigit, str(cnpj)))
    return digits.zfill(14) if len(digits) <= 14 and len(digits) > 0 else digits

def format_cnpj(cnpj: str | None) -> str:
    """Formats 14-digit CNPJ to XX.XXX.XXX/XXXX-XX."""
    if not cnpj:
        return ""
    clean = normalize_cnpj(cnpj)
    if len(clean) != 14:
        return cnpj
    return f"{clean[0:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:14]}"

def validate_cnpj(cnpj: str | None) -> bool:
    """
    Validates Brazilian CNPJ algorithm (modulo 11 verification digits).
    Returns True if valid, False otherwise.
    """
    if not cnpj:
        return False
    
    clean = normalize_cnpj(cnpj)
    if len(clean) != 14:
        return False
    
    # Check for all repeated digits (e.g., 00000000000000, 11111111111111)
    if len(set(clean)) == 1:
        return False
    
    # 1st verification digit
    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_first = sum(int(clean[i]) * weights_first[i] for i in range(12))
    remainder_first = sum_first % 11
    d1 = 0 if remainder_first < 2 else 11 - remainder_first
    if int(clean[12]) != d1:
        return False
    
    # 2nd verification digit
    weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_second = sum(int(clean[i]) * weights_second[i] for i in range(13))
    remainder_second = sum_second % 11
    d2 = 0 if remainder_second < 2 else 11 - remainder_second
    if int(clean[13]) != d2:
        return False
    
    return True

def extract_corporate_name_near(text: str, match_pos: int) -> str | None:
    """Attempts to extract corporate name from text surrounding a CNPJ match."""
    # Look back/forward around 200 chars
    start = max(0, match_pos - 200)
    end = min(len(text), match_pos + 200)
    snippet = text[start:end]
    
    patterns = [
        r"(?:razão\s+social|razao\s+social|nome\s+empresarial|fornecedor|contratad[ao]|favorecido|prestador[a]?)\s*[:\-]?\s*([A-Z0-9À-Ú\s\.\-&]{4,60})",
        r"([A-Z0-9À-Ú\s\.\-&]{4,60})\s*[-–—]\s*(?:CNPJ|MF)",
    ]
    for pattern in patterns:
        m = re.search(pattern, snippet, re.IGNORECASE)
        if m:
            extracted = m.group(1).strip()
            # Clean trailing punctuation and keywords
            extracted = re.split(r"[\n\r]|(?:CNPJ|CPF|Inscrição|Endereço|Data)", extracted, flags=re.IGNORECASE)[0].strip()
            if len(extracted) >= 3 and not extracted.lower().startswith("secretaria"):
                return extracted
    return None

def extract_cnpj_candidates(pages_text: list[str]) -> list[SupplierCandidate]:
    """
    Extracts, validates, scores, and ranks CNPJ candidates found across all pages.
    """
    candidates_map: dict[str, dict] = {}

    for page_idx, page_text in enumerate(pages_text):
        page_num = page_idx + 1
        norm_page = normalize_text(page_text)
        
        for match in CNPJ_REGEX.finditer(page_text):
            raw_val = match.group(1)
            norm_val = normalize_cnpj(raw_val)
            
            if not validate_cnpj(norm_val):
                continue
            
            # Context around match
            m_start = max(0, match.start() - 150)
            m_end = min(len(page_text), match.end() + 150)
            context_raw = page_text[m_start:m_end].replace("\n", " ").strip()
            context_norm = normalize_text(context_raw)
            
            # Calculate match score
            score = 30.0  # base score for valid CNPJ
            
            # Position boost: earlier pages (page 1-5 typically contain process cover/invoices)
            if page_num == 1:
                score += 15.0
            elif page_num <= 3:
                score += 10.0
            elif page_num <= 5:
                score += 5.0
                
            for kw, weight in POSITIVE_CONTEXT_KEYWORDS:
                norm_kw = normalize_text(kw)
                if norm_kw in context_norm:
                    score += weight
                    
            for kw, weight in NEGATIVE_CONTEXT_KEYWORDS:
                norm_kw = normalize_text(kw)
                if norm_kw in context_norm:
                    score += weight
                    
            corporate_name = extract_corporate_name_near(page_text, match.start())
            
            if norm_val not in candidates_map:
                candidates_map[norm_val] = {
                    "cnpj": norm_val,
                    "cnpj_formatted": format_cnpj(norm_val),
                    "corporate_name": corporate_name,
                    "confidence_score": max(5.0, score),
                    "occurrences": 1,
                    "pages": [page_num],
                    "context_snippet": context_raw,
                }
            else:
                candidates_map[norm_val]["occurrences"] += 1
                candidates_map[norm_val]["confidence_score"] += min(20.0, max(5.0, score) * 0.3)
                if page_num not in candidates_map[norm_val]["pages"]:
                    candidates_map[norm_val]["pages"].append(page_num)
                if not candidates_map[norm_val]["corporate_name"] and corporate_name:
                    candidates_map[norm_val]["corporate_name"] = corporate_name
                if len(candidates_map[norm_val]["context_snippet"]) < len(context_raw):
                    candidates_map[norm_val]["context_snippet"] = context_raw

    # Convert to candidate objects and clamp score between 0 and 100
    results: list[SupplierCandidate] = []
    for c_data in candidates_map.values():
        score = min(100.0, max(10.0, c_data["confidence_score"]))
        results.append(
            SupplierCandidate(
                cnpj=c_data["cnpj"],
                cnpj_formatted=c_data["cnpj_formatted"],
                corporate_name=c_data["corporate_name"],
                confidence=round(score, 1),
                occurrences=c_data["occurrences"],
                page_numbers=c_data["pages"],
                context_snippet=c_data["context_snippet"],
            )
        )

    # Sort descending by confidence, then occurrences
    results.sort(key=lambda c: (c.confidence, c.occurrences), reverse=True)
    return results
