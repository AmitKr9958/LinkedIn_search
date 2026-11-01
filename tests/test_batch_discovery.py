import sys

from linkpilot.config import Settings
import linkpilot.batch_discovery as batch


def test_batch_discovery_runs_for_saved_companies_and_reports_totals(monkeypatch, tmp_path):
    calls = []

    class FakeRepo:
        def company_names(self):
            return ["Acme", "Example Ltd"]

        def add_prospect_if_new(self, prospect):
            return True

    monkeypatch.setattr(batch, "get_settings", lambda: Settings(
        "http://localhost:20128/v1", "", "", str(tmp_path / "db.sqlite"), "exa-test"
    ))
    monkeypatch.setattr(batch, "init_db", lambda: None)
    monkeypatch.setattr(batch, "Repository", FakeRepo)

    def fake_search(company, roles, location, api_key, max_results_per_role):
        calls.append((company, roles, location, api_key, max_results_per_role))
        return [{"full_name": "Public Profile"}]

    monkeypatch.setattr(batch, "search_public_professionals", fake_search)
    monkeypatch.setattr(sys, "argv", [
        "batch_discovery", "--location", "Delhi NCR",
        "--log-file", str(tmp_path / "discovery.log"),
    ])

    assert batch.main() == 0
    assert [call[0] for call in calls] == ["Acme", "Example Ltd"]
    assert all(call[2] == "Delhi NCR" for call in calls)


def test_batch_discovery_fails_cleanly_without_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr(batch, "get_settings", lambda: Settings(
        "http://localhost:20128/v1", "", "", str(tmp_path / "db.sqlite"), ""
    ))
    monkeypatch.setattr(sys, "argv", [
        "batch_discovery", "--log-file", str(tmp_path / "discovery.log"),
    ])
    assert batch.main() == 2
