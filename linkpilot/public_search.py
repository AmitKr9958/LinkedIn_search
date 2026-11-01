"""Public professional-profile discovery via the Exa Search API.

Searches public web-index results only. It does not log in to LinkedIn, crawl
LinkedIn profile pages, or automate LinkedIn interactions.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

EXA_SEARCH_URL = "https://api.exa.ai/search"
ROLE_QUERIES = {
    "Recruiter": '"technical recruiter" OR recruiter OR "executive recruiter"',
    "Talent Acquisition": '"talent acquisition" OR "TA manager" OR "talent partner"',
    "HR": '"HR manager" OR "HR business partner" OR "people partner"',
    "Hiring Manager": '"BI manager" OR "Power BI manager" OR "analytics manager" OR "data manager"',
    "Department Head": '"head of data" OR "head of analytics" OR "head of business intelligence"',
    "Director": '"director of analytics" OR "BI director" OR "data director"',
    "VP / AVP": '"VP analytics" OR "AVP data" OR "vice president data"',
    "C-suite / Founder": 'CTO OR CEO OR COO OR founder',
}
DEFAULT_ROLES = ["Recruiter", "Talent Acquisition", "HR", "Hiring Manager"]


class PublicSearchError(RuntimeError):
    """Raised when public search cannot complete."""


def _is_linkedin_profile(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme in {"http", "https"}
        and host in {"linkedin.com", "www.linkedin.com"}
        and parsed.path.startswith("/in/")
        and len(parsed.path.strip("/").split("/")) == 2
    )


def _canonical_profile_url(url: str) -> str:
    parsed = urlparse(url.strip())
    # Keep the public profile path, removing tracking query strings and fragments.
    path = re.sub(r"/+", "/", parsed.path).rstrip("/")
    return urlunparse(("https", "www.linkedin.com", path, "", "", ""))


def _profile_parts(title: str, highlights: list[str], role: str) -> tuple[str, str, str]:
    clean_title = re.sub(r"\s*[|–-]\s*LinkedIn\s*$", "", title or "", flags=re.I).strip()
    parts = re.split(r"\s+[|–—-]\s+", clean_title, maxsplit=1)
    name = parts[0].strip() if parts else ""
    current_role = parts[1].strip() if len(parts) > 1 else "Profile found — verify current role"
    excerpt = " ".join(str(x) for x in highlights if x).strip()
    return name or "Name not available", current_role, excerpt[:1800]


def search_public_professionals(
    company: str,
    roles: list[str],
    location: str,
    api_key: str,
    max_results_per_role: int = 5,
    timeout: int = 25,
) -> list[dict]:
    """Search public web index for LinkedIn /in/ profile URLs.

    Each selected role causes one Exa search request. Check your Exa plan and
    usage limits before running broad searches. Search results are unverified.
    """
    if not company.strip():
        raise ValueError("Enter a target company.")
    if not api_key.strip():
        raise ValueError("Add EXA_API_KEY to your .env file to enable automated discovery.")
    selected = list(dict.fromkeys(role for role in roles if role in ROLE_QUERIES))
    if not selected:
        raise ValueError("Select at least one professional role.")
    limit = max(1, min(int(max_results_per_role), 10))
    found: dict[str, dict] = {}

    for role in selected:
        place = f" in {location.strip()}" if location.strip() else ""
        query = (
            f"Public LinkedIn profile pages for {ROLE_QUERIES[role]} "
            f"currently working at {company.strip()}{place}. "
            "Prioritize profiles whose current employer and role match the request."
        )
        payload = {
            "query": query,
            "type": "auto",
            "numResults": limit,
            "includeDomains": ["linkedin.com"],
            "contents": {"highlights": True},
        }
        request = Request(
            EXA_SEARCH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": api_key.strip()},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise PublicSearchError(f"Public search provider returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PublicSearchError(f"Could not reach the public search provider: {exc}") from exc

        results = data.get("results", [])
        if not isinstance(results, list):
            raise PublicSearchError("Public search provider returned an unexpected results format.")
        for item in results:
            if not isinstance(item, dict):
                continue
            raw_url = str(item.get("url") or "").strip()
            if not _is_linkedin_profile(raw_url):
                continue
            canonical = _canonical_profile_url(raw_url)
            title = str(item.get("title") or "")
            highlights = item.get("highlights") or []
            if isinstance(highlights, str):
                highlights = [highlights]
            if not isinstance(highlights, list):
                highlights = []
            name, current_role, excerpt = _profile_parts(title, highlights, role)
            key = canonical.casefold()
            note = (
                f"Found via Exa public search. Search category: {role}. "
                "Verify employer, title and relevance manually.\n" + excerpt
            ).strip()
            existing = found.get(key)
            if existing:
                existing["research_notes"] = (existing["research_notes"] + "\n" + note)[:3500]
                continue
            found[key] = {
                "full_name": name,
                "company": company.strip(),
                "title": current_role,
                "category": role,
                "profile_url": canonical,
                "source_url": raw_url,
                "research_notes": note,
            }
    return list(found.values())
