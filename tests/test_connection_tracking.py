from datetime import datetime
import pytest

from linkpilot.config import Settings
import linkpilot.db as db
from linkpilot.repository import Repository


@pytest.fixture
def repo(tmp_path, monkeypatch):
    database = tmp_path / "connection-tracking.db"
    monkeypatch.setattr(
        db,
        "get_settings",
        lambda: Settings(
            llm_base_url="http://localhost:20128/v1",
            llm_api_key="",
            llm_model="",
            database_path=str(database),
        ),
    )
    db.init_db()
    return Repository()


def add_approved_prospect(repo, name):
    repo.add_prospect(name, "Example Ltd", "Power BI Hiring Manager", "Hiring Manager")
    prospect = repo.list_prospects()[0]
    repo.save_draft(prospect["id"], "Hello, I would like to connect.")
    draft = repo.list_drafts()[0]
    repo.update_draft(draft["id"], draft["message"], "approved")
    return prospect["id"]


def test_only_approved_prospects_can_be_recorded_as_sent(repo):
    repo.add_prospect("Jordan", "Example Ltd", "Recruiter", "Recruiter")
    prospect = repo.list_prospects()[0]
    with pytest.raises(ValueError, match="Approve a connection note"):
        repo.record_connection_sent(prospect["id"])
    assert repo.daily_connection_count() == 0


def test_manual_send_is_recorded_once_and_updates_status(repo):
    prospect_id = add_approved_prospect(repo, "Jordan")
    assert repo.record_connection_sent(prospect_id) == 1
    assert repo.daily_connection_count() == 1
    assert repo.get_prospect(prospect_id)["outreach_status"] == "connection_sent"
    with pytest.raises(ValueError, match="already recorded"):
        repo.record_connection_sent(prospect_id)
    assert repo.daily_connection_count() == 1


def test_daily_limit_is_enforced(repo):
    first = add_approved_prospect(repo, "Jordan")
    second = add_approved_prospect(repo, "Taylor")
    today = datetime.now().astimezone().date().isoformat()
    assert repo.record_connection_sent(first, daily_limit=1, sent_on=today) == 1
    with pytest.raises(ValueError, match="Daily limit reached"):
        repo.record_connection_sent(second, daily_limit=1, sent_on=today)
    assert repo.daily_connection_count(today) == 1


def test_unapproved_status_cannot_bypass_send_ledger(repo):
    repo.add_prospect("Casey", "Example Ltd", "Recruiter", "Recruiter")
    prospect = repo.list_prospects()[0]
    with pytest.raises(ValueError, match="manual-send confirmation"):
        repo.update_prospect_status(prospect["id"], "connection_sent")



def test_daily_count_uses_local_calendar_date_for_offset_timestamps(repo):
    prospect_id = add_approved_prospect(repo, "Morgan")
    target_date = "2026-11-01"
    with db.connect() as connection:
        connection.execute(
            "INSERT INTO connection_events(prospect_id, sent_at) VALUES(?, ?)",
            (prospect_id, f"{target_date}T00:15:00+05:30"),
        )

    assert repo.daily_connection_count(target_date) == 1
