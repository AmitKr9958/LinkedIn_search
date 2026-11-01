from urllib.parse import quote_plus

ROLE_SEARCH_TERMS = {
    "Recruiter": '"technical recruiter" OR recruiter',
    "Talent Acquisition": '"talent acquisition" OR "TA manager"',
    "HR": '"HR manager" OR "HR business partner"',
    "Hiring Manager": '"BI manager" OR "Power BI manager" OR "analytics manager"',
    "Department Head": '"head of data" OR "head of analytics"',
    "Director": '"director of analytics" OR "BI director"',
    "VP / AVP": '"VP analytics" OR "AVP data" OR "vice president data"',
    "C-suite / Founder": 'CTO OR CEO OR COO OR founder',
}

def build_public_search_url(company: str, categories: list[str]) -> str:
    if not company.strip():
        raise ValueError("Company name is required.")
    terms = [ROLE_SEARCH_TERMS[c] for c in categories if c in ROLE_SEARCH_TERMS]
    if not terms:
        terms = list(ROLE_SEARCH_TERMS.values())
    query = f'site:linkedin.com/in/ "{company.strip()}" ({" OR ".join(terms)})'
    return "https://www.google.com/search?q=" + quote_plus(query)

def build_search_query(company: str, category: str) -> str:
    if category not in ROLE_SEARCH_TERMS:
        raise ValueError("Unknown prospect category.")
    return f'site:linkedin.com/in/ "{company.strip()}" ({ROLE_SEARCH_TERMS[category]})'

def build_company_search_url(role_keywords: str, location: str) -> str:
    if not role_keywords.strip():
        raise ValueError("Enter at least one role or skill keyword.")
    location_part = f' "{location.strip()}"' if location.strip() else ""
    query = f'companies hiring ({role_keywords.strip()}){location_part} (jobs OR careers OR hiring)'
    return "https://www.google.com/search?q=" + quote_plus(query)
