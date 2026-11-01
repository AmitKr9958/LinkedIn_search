from linkpilot.scoring import relevance_score

def test_recruiter_and_bi_context_scores_high():
    assert relevance_score("Recruiter", "Power BI Talent Acquisition") == 100

def test_unknown_category_has_safe_default():
    assert relevance_score("Unknown", "General role") == 30

def test_score_is_bounded():
    assert 0 <= relevance_score("Other", "Data recruiter analytics") <= 100
