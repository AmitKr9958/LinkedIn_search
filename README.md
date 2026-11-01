# LinkPilot AI

A local-first, human-approved professional networking research and outreach CRM.

## Safety boundary
This app does not log in to LinkedIn, scrape LinkedIn pages, automate LinkedIn browser activity, send connection requests, or bypass platform controls. The Discovery page builds public-web search queries for you to review manually. Add prospect details only from sources you are permitted to use. The app drafts messages, manages approvals and opens profile URLs so you can review and act yourself.

## Features
- Company directory and hiring-focus notes.
- Company hiring search-query builder for BI / Power BI / Data Analyst roles.
- Automated public professional discovery through the Exa Search API for publicly indexed LinkedIn profile URLs, with manual review.
- Duplicate detection based on normalized public profile URLs.
- Batch discovery across all companies saved in the local directory.
- Optional Windows Task Scheduler job for daily public-profile discovery, with local logs.
- Manual public-web search links remain available as a fallback.
- Manual prospect entry.
- CSV prospect import with required-column validation and duplicate skipping.
- CSV export.
- Heuristic role relevance scoring.
- 9Router-compatible personalized message drafting.
- Editable draft and explicit approval queue.
- Manual-send confirmation workflow with a hard 30-request daily recording cap, approval requirement, duplicate-send prevention and a local activity ledger.
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

## Automated public prospect discovery

CSV import is optional. To search for prospects automatically, create an Exa API key from [Exa](https://dashboard.exa.ai/api-keys) and add it to `.env` as `EXA_API_KEY=...`. Restart Streamlit, open **Discovery**, choose a company, location and professional roles, then click **Find public profiles**. The app stores matching public LinkedIn `/in/` profile URLs in the local prospect CRM and skips duplicate profile URLs. Search results can be incomplete or outdated, so verify each person's current employer and role before drafting or contacting them. Exa API availability, quotas and charges depend on the account; check its current pricing before use. If no Exa key is configured, manual public-search links still work and CSV is not required.

The integration uses Exa's public search endpoint and filters results to LinkedIn profile URL paths. It does not log in to LinkedIn, scrape pages, collect private contact data, bypass access controls or send connection requests. Searches are one request per selected role and company, so broad searches can use more of your provider quota. Start with a small number of companies and roles.

## Optional daily discovery on Windows

After adding companies in the app and configuring `EXA_API_KEY` in `.env`, you can run discovery for every saved company:

```powershell
python -m linkpilot.batch_discovery --location "Delhi NCR"
```

To schedule it daily at 9:00 AM, run this once from PowerShell in the repository:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install_daily_discovery.ps1
```

The task runs as your Windows user while you are logged in and the computer is awake. It does not run while the laptop is shut down. Logs are written to `logs/daily-discovery.log`. To start it manually after installation:

```powershell
Start-ScheduledTask -TaskName "LinkPilot Daily Public Discovery"
```

Remove the scheduled task with:

```powershell
Unregister-ScheduledTask -TaskName "LinkPilot Daily Public Discovery" -Confirm:$false
```

The task searches the companies already saved in the app; it does not invent or automatically add target companies.

## 9Router
Start 9Router and connect a provider/model available to your account. Put the exact OpenAI-compatible base URL, API key and model identifier displayed by your 9Router setup in `.env`. Never commit `.env`.

## Storage
SQLite is used locally by default at `data/linkpilot.db`. No hosted database is required for the initial release.

## Workflow
1. Add target companies.
2. Use Discovery to find companies with relevant openings, then build public-web searches for decision-makers and manually review results.
3. Add prospects manually or import a CSV from permitted sources.
4. Generate, edit and approve a role-specific note.
5. Open the approved profile, review the final note, and send the connection request yourself on LinkedIn.
6. Return to the Approval queue, tick the confirmation that you sent it, and choose **Record as sent**. The app enforces a maximum of 30 recorded sends per local calendar day and prevents duplicate records for the same prospect.
7. Update later statuses (connected, replied or archived) in the Prospects page.

## Tests
Run `pytest -q`.

## Important
An approved note is not a sent connection request. Sending remains a manual action. The 30/day cap applies to requests recorded in this local CRM; it cannot observe or limit invitations sent outside the app or on another device. Do not put API keys, passwords, sensitive personal data or private contact details into the research notes.

## Roadmap
More complete prospect lifecycle tracking, configurable relevance rules, compliant research-provider adapters, follow-up reminders, analytics, security hardening and optional Supabase persistence.
