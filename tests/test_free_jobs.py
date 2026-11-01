import json
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
    jobs = search_india_jobs(DEFAULT_QUERY, limit=20, location="India")

    assert jobs == [{"title": "Power BI Developer"}]
    assert "/jobs/search?" in captured["url"]
    assert "countries=IN" in captured["url"]
    assert "q_fields=title" in captured["url"]
    assert "experience_years_min=5" in captured["url"]
    assert "experience_years_max=8" in captured["url"]
    assert "experience_include_unspecified=true" in captured["url"]
    assert "posted_within_days=2" in captured["url"]
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



def test_delhi_ncr_search_uses_server_side_city_filters(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse({"data": []})

    monkeypatch.setattr("linkpilot.free_jobs.urlopen", fake_urlopen)
    search_india_jobs(location="Delhi NCR")

    assert "cities=Delhi%2CGurugram%2CNoida" in captured["url"]
    assert "countries=IN" not in captured["url"]


def test_location_filter_supports_cities_array():
    jobs = [
        {"title": "Power BI Developer", "cities": ["Jaipur"]},
        {"title": "Analyst", "cities": ["Bengaluru"]},
    ]
    assert [job["title"] for job in filter_jobs_by_location(jobs, "Jaipur")] == [
        "Power BI Developer"
    ]


def test_search_rejects_unknown_location(monkeypatch):
    with pytest.raises(ValueError, match="supported location"):
        search_india_jobs(location="Moon")
