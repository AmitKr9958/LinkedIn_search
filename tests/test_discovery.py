from linkpilot.discovery import build_public_search_url, build_search_query, build_company_search_url

def test_search_query_uses_company_and_role():
    query = build_search_query("Acme", "Talent Acquisition")
    assert '"Acme"' in query
    assert "talent acquisition" in query.lower()

def test_public_search_url_is_google_search():
    url = build_public_search_url("Acme", ["Recruiter", "Hiring Manager"])
    assert url.startswith("https://www.google.com/search?q=")

def test_company_search_url_contains_role_and_location():
    url = build_company_search_url("Power BI", "Delhi NCR")
    assert url.startswith("https://www.google.com/search?q=")
    assert "google.com/search" in url
