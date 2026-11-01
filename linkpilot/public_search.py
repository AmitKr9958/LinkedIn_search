"""Public professional-profile discovery via the Exa Search API.

Only public, indexed LinkedIn profile URLs are retained. This module does not
log in to LinkedIn, crawl profile pages, or automate LinkedIn interactions.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse


EXA_SEARCH_URL = "https://api.exa.ai/search"
ROLE_QUERIES = {
    "Recruiter": "recruiters and technical recruiters",
    "Talent Acquisition": "talent acquisition leaders and TA managers",
    "HR": "HR leaders and HR business partners",
    "Hiring Manager": "BI, Power BI and analytics hiring managers",
    "Department Head": "heads of data, business intelligence and analytics",
    "Director": "directors of analytics and business intelligence",
    "VP / AVP": "vice presidents and AVPs leading data or analytics",
    "C-suite / Founder": "CTOs, CEOs, COOs and founders",
}


class PublicSearchError(RuntimeError):
    """Raised when public search cannot complete."""


def _profile_parts(title: str, highlights: list[str], role: str) -> tuple[str, str, str]:
    clean_title = re.sub(r"\s*[|–-]\s*LinkedIn\s*$", "", title or "", flags=re.I).strip()
    # Search result titles commonly look like "Name - Role at Company".
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

    The API key is sent only to Exa. Results are not treated as verified facts;
    the UI asks the user to review each profile before outreach.
    """
    if not company.strip():
        raise ValueError("Enter a target company.")
    if not api_key.strip():
        raise ValueError("Add EXA_API_KEY to your .env file to enable automated discovery.")
    selected = [role for role in roles if role in ROLE_QUERIES]
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
            "includeDomains": ["linkedin.com/in"],
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

        for item in data.get("results", []):
            url = str(item.get("url") or "").strip()
            parsed = urlparse(url)
            if parsed.netloc.lower() not in {"linkedin.com", "www.linkedin.com"}:
                continue
            if not parsed.path.startswith("/in/"):
                continue
            canonical = url.split("?")[0].rstrip("/")
            title = str(item.get("title") or "")
            highlights = item.get("highlights") or []
            name, current_role, excerpt = _profile_parts(title, highlights, role)
            existing = found.get(canonical.casefold())
            note = f"Found via Exa public search. Search category: {role}. Verify employer, title and relevance manually.\n{excerpt}".strip()
            if existing:
                existing["research_notes"] = (existing["research_notes"] + "\n" + note)[:3500]
                continue
            found[canonical.casefold()] = {
                "full_name": name,
                "company": company.strip(),
                "title": current_role,
                "category": role,
                "profile_url": canonical,
                "source_url": canonical,
                "research_notes": note,
            }
    return list(found.values())
