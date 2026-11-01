# LinkPilot AI

A local-first, human-approved professional networking research and outreach CRM.

## Safety boundary
This app does not log in to LinkedIn, scrape LinkedIn pages, automate LinkedIn browser activity, send connection requests, or bypass platform controls. Add prospect details from sources you are permitted to use. The app drafts messages, manages approvals and opens profile URLs so you can review and act manually.

## Windows setup (PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```
Open http://localhost:8501.

## 9Router
Start 9Router and connect a provider/model available to your account. Put the exact OpenAI-compatible base URL, API key and model identifier displayed by your 9Router setup in `.env`. Never commit `.env`.

## Storage
SQLite is used locally by default at `data/linkpilot.db`. No hosted database is required for the initial release.

## Workflow
1. Add target companies.
2. Add professional prospects from permitted sources or your own research.
3. Generate a role-specific note.
4. Edit and approve the draft.
5. Open the profile and decide/send manually on LinkedIn.
6. Record outcomes in the CRM.

## Tests
Run `pytest -q`.

## Current MVP
Company/prospect management, 9Router message drafting, review/approval queue, SQLite persistence and basic tests.

## Roadmap
CSV import/export, duplicate detection, compliant public-web research providers, relevance scoring, reminders, analytics and optional Supabase persistence.
