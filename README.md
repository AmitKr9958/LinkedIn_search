# LinkPilot AI

A local-first, human-approved professional networking research and outreach CRM.

## Safety boundary
This app does not log in to LinkedIn, scrape LinkedIn pages, automate LinkedIn browser activity, send connection requests, or bypass platform controls. The Discovery page builds public-web search queries for you to review manually. Add prospect details only from sources you are permitted to use. The app drafts messages, manages approvals and opens profile URLs so you can review and act yourself.

## Features
- Company directory and hiring-focus notes.
- Public professional search-query builder for recruiter, TA, HR, hiring manager and leadership roles.
- Manual prospect entry.
- CSV prospect import with required-column validation and duplicate skipping.
- CSV export.
- Heuristic role relevance scoring.
- 9Router-compatible personalized message drafting.
- Editable draft and explicit approval queue.
- Manual outreach lifecycle tracking: not contacted, drafted, approved, connection sent, connected, replied and archived.
- CSV export with spreadsheet-formula injection protection.
- Local SQLite persistence.
- GitHub Actions test workflow.

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
2. Use Discovery to create a public-web search link and manually review results.
3. Add prospects manually or import a CSV from permitted sources.
4. Generate, edit and approve a role-specific note.
5. Open the profile and decide/send manually on LinkedIn.
6. Update the prospect status manually (connection sent, connected, replied, etc.) in the CRM.

## Tests
Run `pytest -q`.

## Important
An approved note is not a sent connection request. Sending remains a manual action. Do not put API keys, passwords, sensitive personal data or private contact details into the research notes.

## Roadmap
More complete prospect lifecycle tracking, configurable relevance rules, compliant research-provider adapters, follow-up reminders, analytics, security hardening and optional Supabase persistence.
