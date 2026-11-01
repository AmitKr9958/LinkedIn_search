ROLE_WEIGHTS = {
    "recruiter": 100,
    "talent acquisition": 100,
    "hr": 90,
    "hiring manager": 100,
    "department head": 85,
    "director": 75,
    "vp / avp": 65,
    "c-suite / founder": 45,
    "other": 30,
}

def relevance_score(category: str, title: str = "", hiring_focus: str = "") -> int:
    """Transparent heuristic score; it is a prioritization aid, not a prediction."""
    category_key = (category or "other").strip().lower()
    base = ROLE_WEIGHTS.get(category_key, 30)
    text = f"{title} {hiring_focus}".lower()
    if any(term in text for term in ("power bi", "business intelligence", "analytics", "data", "fabric")):
        base += 10
    if any(term in text for term in ("recruit", "talent acquisition", "hiring", "people")):
        base += 5
    return min(base, 100)
