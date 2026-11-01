from linkpilot.discovery import build_public_search_url, build_search_query

def test_search_query_uses_company_and_role():
    query = build_search_query("Acme", "Talent Acquisition")
    assert '"Acme"' in query
    assert "talent acquisition" in query.lower()

def test_public_search_url_is_google_search():
    url = build_public_search_url("Acme", ["Recruiter", "Hiring Manager"])
    assert url.startswith("https://www.google.com/search?q=")
