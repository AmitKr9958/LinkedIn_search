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
    repo.save_draft(prospect["id"], "Hello Taylor, I would be glad to connect.")
    draft = repo.list_drafts()[0]
    assert draft["status"] == "draft"
    repo.update_draft(draft["id"], "Revised note", "approved")
    assert repo.list_drafts()[0]["status"] == "approved"

def test_invalid_status_rejected():
    repo = Repository()
    with pytest.raises(ValueError):
        repo.update_draft(1, "x", "sent")
