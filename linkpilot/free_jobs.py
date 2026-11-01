"""Free public job search using the unauthenticated freehire read API.

The public API is documented for personal, non-commercial use without a key.
See https://freehire.me/docs/api for current limits and licensing.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://freehire.me/api/v1"
DEFAULT_QUERY = (
    '"Power BI" OR "Business Intelligence" OR "Data Analyst" '
    'OR "Microsoft Fabric" OR "Reporting Analyst"'
)


class FreeJobsError(RuntimeError):
    """Raised when the public job API cannot return valid results."""


def search_india_jobs(
    query: str = DEFAULT_QUERY,
    limit: int = 50,
    location: str = "Delhi NCR",
    min_experience: int | None = 5,
    max_experience: int | None = 8,
    posted_within_days: int | None = 2,
    timeout: int = 20,
) -> list[dict]:
    """Search current India job postings without an API key."""
    if not query or not query.strip():
        raise ValueError("A job search query is required.")
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    # Restrict matching to titles: searching descriptions was returning unrelated
    # jobs that only mentioned Power BI somewhere in their text.
    params_dict = {
        "q": query.strip(),
        "q_fields": "title",
        "sort": "posted_at",
        "order": "desc",
        "limit": limit,
        "offset": 0,
    }
    city_filters = {
        "delhi ncr": ["Delhi", "Gurugram", "Noida"],
        "delhi": ["Delhi"],
        "gurugram": ["Gurugram"],
        "noida": ["Noida"],
        "jaipur": ["Jaipur"],
        "india": [],
        "all india": [],
        "all": [],
    }
    selected_cities = city_filters.get(location.strip().casefold())
    if selected_cities is None:
        raise ValueError("Choose a supported location filter.")
    if selected_cities:
        # Geography filters are ORed by freehire, so do not combine cities with countries=IN.
        params_dict["cities"] = ",".join(selected_cities)
    else:
        params_dict["countries"] = "IN"

    if min_experience is not None:
        params_dict["experience_years_min"] = min_experience
    if max_experience is not None:
        params_dict["experience_years_max"] = max_experience
    if min_experience is not None or max_experience is not None:
        params_dict["experience_include_unspecified"] = "true"
    if posted_within_days is not None:
        params_dict["posted_within_days"] = posted_within_days

    params = urlencode(params_dict)
    request = Request(
        f"{BASE_URL}/jobs/search?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "LinkPilot-AI/1.0 (personal job research)",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            raise FreeJobsError(
                "freehire rate limit reached. Please wait and try again later."
            ) from exc
        raise FreeJobsError(f"freehire returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise FreeJobsError(f"Could not reach freehire: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FreeJobsError("freehire returned an invalid JSON response.") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        message = payload.get("error", "Unexpected response format") if isinstance(payload, dict) else "Unexpected response format"
        raise FreeJobsError(f"freehire response error: {message}")

    return [job for job in payload["data"] if isinstance(job, dict)]


def filter_jobs_by_location(jobs: list[dict], location: str) -> list[dict]:
    """Defensive local location filter for API responses and provider aliases."""
    wanted = location.strip().casefold()
    if not wanted or wanted in {"india", "all india", "all"}:
        return jobs

    aliases = {
        "delhi ncr": ("delhi", "new delhi", "gurugram", "gurgaon", "noida"),
        "gurugram": ("gurugram", "gurgaon"),
    }
    terms = aliases.get(wanted, (wanted,))
    filtered = []
    for job in jobs:
        location_text = str(job.get("location", "")).casefold()
        cities = job.get("cities") or []
        if isinstance(cities, str):
            cities = [cities]
        city_text = " ".join(str(city) for city in cities).casefold()
        if any(term in location_text or term in city_text for term in terms):
            filtered.append(job)
    return filtered
