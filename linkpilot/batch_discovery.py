"""Run public prospect discovery for saved companies.

Examples:
    python -m linkpilot.batch_discovery
    python -m linkpilot.batch_discovery --company Accenture --location "Delhi NCR"
    python -m linkpilot.batch_discovery --roles Recruiter "Talent Acquisition" "Hiring Manager"
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from linkpilot.config import get_settings
from linkpilot.db import init_db
from linkpilot.public_search import DEFAULT_ROLES, ROLE_QUERIES, search_public_professionals
from linkpilot.repository import Repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover publicly indexed professional profiles.")
    parser.add_argument("--company", help="Search one company. Omit to search all saved companies.")
    parser.add_argument("--location", default="Delhi NCR", help="Location to include in public search queries.")
    parser.add_argument("--roles", nargs="+", choices=sorted(ROLE_QUERIES), default=DEFAULT_ROLES)
    parser.add_argument("--max-results-per-role", type=int, default=5)
    parser.add_argument("--log-file", default="logs/daily-discovery.log")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )
    settings = get_settings()
    if not settings.exa_api_key:
        logging.error("EXA_API_KEY is missing. Add it to .env; no search was performed.")
        return 2

    init_db()
    repo = Repository()
    companies = [args.company.strip()] if args.company and args.company.strip() else repo.company_names()
    if not companies:
        logging.error("No companies saved. Add companies in the app before scheduling discovery.")
        return 2

    total_found = 0
    total_added = 0
    failures = 0
    for company in companies:
        try:
            candidates = search_public_professionals(
                company=company,
                roles=args.roles,
                location=args.location,
                api_key=settings.exa_api_key,
                max_results_per_role=args.max_results_per_role,
            )
            added = sum(1 for candidate in candidates if repo.add_prospect_if_new(candidate))
            total_found += len(candidates)
            total_added += added
            logging.info(
                "Company=%s found=%d added=%d duplicates=%d",
                company, len(candidates), added, len(candidates) - added,
            )
        except Exception as exc:
            failures += 1
            logging.exception("Discovery failed for company=%s: %s", company, exc)

    logging.info(
        "Finished companies=%d found=%d added=%d failures=%d",
        len(companies), total_found, total_added, failures,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
