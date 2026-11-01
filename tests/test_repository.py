import pytest
from linkpilot.db import init_db
from linkpilot.repository import Repository

def test_company_prospect_draft_and_approval(tmp_path, monkeypatch):
    import sqlite3
    from pathlib import Path
    import linkpilot.db as db
    import linkpilot.repository as repository_module

    def test_connect():
        conn = sqlite3.connect(Path(tmp_path) / "test.db")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(db, "connect", test_connect)
    monkeypatch.setattr(repository_module, "connect", test_connect)
    init_db()
    repo = Repository()
    repo.add_company("Acme", "", "", "Power BI")
    assert repo.company_names() == ["Acme"]
    repo.add_prospect("Taylor Recruiter", "Acme", "Talent Acquisition Manager",
                      "Talent Acquisition", "https://example.org/profile", "", "Supports analytics hiring")
    prospect = repo.list_prospects()[0]
    assert prospect["outreach_status"] == "not_contacted"
    repo.update_prospect_status(prospect["id"], "connection_sent")
    assert repo.get_prospect(prospect["id"])["outreach_status"] == "connection_sent"
    repo.save_draft(prospect["id"], "Hello Taylor, I would be glad to connect.")
    draft = repo.list_drafts()[0]
    assert draft["status"] == "draft"
    repo.update_draft(draft["id"], "Revised note", "approved")
    assert repo.list_drafts()[0]["status"] == "approved"
    assert repo.get_prospect(prospect["id"])["outreach_status"] == "approved"

def test_invalid_status_rejected():
    repo = Repository()
    with pytest.raises(ValueError):
        repo.update_draft(1, "x", "sent")

def test_discovered_profile_url_is_deduplicated(tmp_path, monkeypatch):
    import sqlite3
    from pathlib import Path
    import linkpilot.db as db
    import linkpilot.repository as repository_module

    def test_connect():
        conn = sqlite3.connect(Path(tmp_path) / "dedupe.db")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(db, "connect", test_connect)
    monkeypatch.setattr(repository_module, "connect", test_connect)
    init_db()
    repo = Repository()
    prospect = {
        "full_name": "Alex Example",
        "company": "Acme",
        "title": "Recruiter",
        "category": "Recruiter",
        "profile_url": "https://www.linkedin.com/in/alex-example",
        "source_url": "https://www.linkedin.com/in/alex-example",
        "research_notes": "Public result",
    }
    assert repo.add_prospect_if_new(prospect) is True
    assert repo.add_prospect_if_new(prospect) is False
    assert len(repo.list_prospects()) == 1
