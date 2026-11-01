import json
from io import BytesIO
from linkpilot.public_search import search_public_professionals


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_public_search_returns_only_linkedin_profile_urls_and_deduplicates(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse({
            "results": [
                {
                    "title": "Amit Example - Talent Acquisition Manager at Acme | LinkedIn",
                    "url": "https://www.linkedin.com/in/amit-example/?trk=public",
                    "highlights": ["Works in talent acquisition at Acme."],
                },
                {
                    "title": "Acme company page",
                    "url": "https://www.linkedin.com/company/acme/",
                    "highlights": ["Not a person profile."],
                },
                {
                    "title": "External profile",
                    "url": "https://example.com/person",
                    "highlights": ["Not LinkedIn."],
                },
            ]
        })

    monkeypatch.setattr("linkpilot.public_search.urlopen", fake_urlopen)
    rows = search_public_professionals(
        "Acme", ["Recruiter", "Talent Acquisition"], "India", "test-exa-key"
    )

    assert len(calls) == 2
    assert len(rows) == 1
    assert rows[0]["full_name"] == "Amit Example"
    assert rows[0]["profile_url"] == "https://www.linkedin.com/in/amit-example"
    assert "Talent Acquisition" in rows[0]["research_notes"]


def test_public_search_requires_api_key():
    import pytest
    with pytest.raises(ValueError, match="EXA_API_KEY"):
        search_public_professionals("Acme", ["Recruiter"], "India", "")


def test_public_search_requires_valid_role():
    import pytest
    with pytest.raises(ValueError, match="at least one"):
        search_public_professionals("Acme", ["Unknown"], "India", "test-key")
