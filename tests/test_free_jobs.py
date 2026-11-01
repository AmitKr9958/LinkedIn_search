import json
from io import BytesIO

import pytest

from linkpilot.free_jobs import (
    DEFAULT_QUERY,
    FreeJobsError,
    filter_jobs_by_location,
    search_india_jobs,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_search_india_jobs_uses_keyless_api_and_normalizes_results(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse({"data": [{"title": "Power BI Developer"}]})

    monkeypatch.setattr("linkpilot.free_jobs.urlopen", fake_urlopen)
    jobs = search_india_jobs(DEFAULT_QUERY, limit=20)

    assert jobs == [{"title": "Power BI Developer"}]
    assert "/jobs/search?" in captured["url"]
    assert "countries=IN" in captured["url"]
    assert "limit=20" in captured["url"]


def test_search_india_jobs_rejects_invalid_limit():
    with pytest.raises(ValueError):
        search_india_jobs(limit=0)


def test_search_india_jobs_reports_invalid_response(monkeypatch):
    monkeypatch.setattr(
        "linkpilot.free_jobs.urlopen",
        lambda request, timeout: FakeResponse({"unexpected": []}),
    )
    with pytest.raises(FreeJobsError):
        search_india_jobs()


def test_location_filter_matches_delhi_ncr_aliases():
    jobs = [
        {"title": "Analyst", "location": "Gurgaon, India"},
        {"title": "Developer", "location": "Noida, Uttar Pradesh"},
        {"title": "Engineer", "location": "Bengaluru, India"},
    ]

    filtered = filter_jobs_by_location(jobs, "Delhi NCR")

    assert [job["title"] for job in filtered] == ["Analyst", "Developer"]


def test_location_filter_india_keeps_all_returned_jobs():
    jobs = [{"location": "Mumbai"}, {"location": "Remote"}]
    assert filter_jobs_by_location(jobs, "India") == jobs
