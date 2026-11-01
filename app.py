from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from linkpilot.db import init_db
from linkpilot.repository import Repository
from linkpilot.ai import DraftService
from linkpilot.config import get_settings
from linkpilot.csv_tools import parse_prospect_csv, export_prospects_csv
from linkpilot.scoring import relevance_score
from linkpilot.discovery import build_public_search_url, build_company_search_url, build_search_query, ROLE_SEARCH_TERMS
from linkpilot.public_search import search_public_professionals, PublicSearchError
from linkpilot.free_jobs import search_india_jobs, filter_jobs_by_location, FreeJobsError

st.set_page_config(page_title="LinkPilot AI", page_icon="🤝", layout="wide")
init_db()
repo = Repository()
settings = get_settings()

st.title("🤝 LinkPilot AI")
st.caption("Professional networking research and personalized outreach — with your approval.")
with st.sidebar:
    st.header("Workspace")
    page = st.radio("Navigate", ["Overview", "Companies", "Jobs", "Discovery", "Prospects", "Approval queue", "Settings"])
    st.divider()
    st.info("Human approval required. No LinkedIn login, scraping, browser automation or automatic sending.")

if page == "Overview":
    stats = repo.stats()
    sent_today = repo.daily_connection_count()
    cols = st.columns(6)
    metrics = [
        ("Companies", stats["companies"]), ("Prospects", stats["prospects"]),
        ("Drafts", stats["drafts"]), ("Approved", stats["approved"]),
        ("Sent today", sent_today), ("Daily remaining", max(0, 30 - sent_today)),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    st.subheader("Getting started")
    st.markdown("1. Add companies.\n2. Add professionals using permitted sources.\n3. Generate a 9Router draft.\n4. Review and approve.\n5. Open the profile and send manually if appropriate.")
    st.warning("Metrics reflect this local database only.")

elif page == "Companies":
    st.subheader("Company directory")
    with st.form("company_form", clear_on_submit=True):
        name = st.text_input("Company name")
        website = st.text_input("Website (optional)")
        careers = st.text_input("Careers page (optional)")
        focus = st.text_input("Hiring focus", placeholder="Power BI, Data Analytics, Fabric")
        save = st.form_submit_button("Save company")
        if save:
            if not name.strip():
                st.error("Company name is required.")
            else:
                try:
                    repo.add_company(name.strip(), website.strip(), careers.strip(), focus.strip())
                    st.success("Company saved.")
                except Exception as exc:
                    st.error(f"Could not save company: {exc}")
    st.dataframe(repo.list_companies(), use_container_width=True, hide_index=True)


elif page == "Jobs":
    st.subheader("Free job discovery — India")
    st.caption(
        "Uses freehire's public, no-key job-search API. Search results are hiring signals, "
        "not verified recruiter/contact records. Keyword matching is restricted to job titles."
    )
    st.info(
        "No API key is needed for personal, non-commercial use. The search applies location, "
        "experience and posting-date filters at the API where supported. Unspecified experience "
        "may still be included; verify each vacancy before applying."
    )
    job_query = st.text_input(
        "Job keywords",
        '"Power BI" OR "Business Intelligence" OR "Data Analyst" OR "Microsoft Fabric" OR "Reporting Analyst"',
    )
    job_location = st.selectbox(
        "Location filter",
        ["Delhi NCR", "India", "Gurugram", "Noida", "Delhi", "Jaipur"],
        index=0,
    )
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        min_experience = st.selectbox("Minimum experience (years)", [None, 0, 2, 3, 5, 6, 8, 10], index=4,
                                      format_func=lambda value: "Any / include unspecified" if value is None else str(value))
    with filter_col2:
        max_experience = st.selectbox("Maximum experience (years)", [None, 3, 5, 6, 8, 10, 12, 15], index=4,
                                      format_func=lambda value: "Any / include unspecified" if value is None else str(value))
    posted_days = st.selectbox("Posted within", [1, 2, 3, 7, 14, 30, None], index=1,
                               format_func=lambda value: "Any date" if value is None else f"Last {value} day(s)")
    job_limit = st.slider("Maximum jobs to retrieve", min_value=10, max_value=100, value=50, step=10)
    if st.button("Search free job listings", type="primary"):
        try:
            with st.spinner("Searching freehire public job listings..."):
                jobs = search_india_jobs(
                    job_query,
                    limit=job_limit,
                    location=job_location,
                    min_experience=min_experience,
                    max_experience=max_experience,
                    posted_within_days=posted_days,
                )
                filtered_jobs = filter_jobs_by_location(jobs, job_location)
            st.session_state["freehire_jobs"] = filtered_jobs
            st.session_state["freehire_location"] = job_location
            st.success(
                f"Received {len(jobs)} listing(s); "
                f"{len(filtered_jobs)} match the {job_location} filter."
            )
        except (FreeJobsError, ValueError) as exc:
            st.error(str(exc))

    jobs = st.session_state.get("freehire_jobs", [])
    if jobs:
        rows = []
        for job in jobs:
            rows.append({
                "Job title": job.get("title", ""),
                "Company": job.get("company", ""),
                "Location": job.get("location", ""),
                "Posted": job.get("posted_at", ""),
                "Experience (min)": (job.get("enrichment") or {}).get("experience_years_min", ""),
                "Experience (max)": (job.get("enrichment") or {}).get("experience_years_max", ""),
                "Apply link": job.get("apply_url") or job.get("url", ""),
                "Source": job.get("source", ""),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
        companies_to_save = sorted({
            str(job.get("company", "")).strip()
            for job in jobs if str(job.get("company", "")).strip()
        })
        st.caption("Save companies found in these postings to your company directory.")
        if st.button("Save discovered hiring companies"):
            known = {name.casefold() for name in repo.company_names()}
            added = 0
            for company_name in companies_to_save:
                if company_name.casefold() not in known:
                    repo.add_company(
                        company_name,
                        hiring_focus="Found in freehire job listings; verify current vacancies",
                    )
                    known.add(company_name.casefold())
                    added += 1
            st.success(f"Saved {added} new company/companies. Existing companies were skipped.")
        st.caption("Open each original application link to verify the vacancy and apply on the employer/board site.")
    else:
        st.info("Run a search to see current India job listings. The API may return no matches for a narrow keyword or location.")
    st.markdown("[freehire API documentation](https://freehire.me/docs/api) · [public-apis Jobs catalogue](https://github.com/public-apis/public-apis#jobs)")

elif page == "Discovery":
    st.subheader("Company discovery")
    st.caption("Find public job and careers pages for companies hiring in your target skill area.")
    company_keywords = st.text_input("Target skills / roles", "Power BI OR Business Intelligence OR Data Analyst")
    target_location = st.text_input("Target location", "India", key="company_search_location")
    if company_keywords.strip():
        st.link_button("Search companies and job openings",
                       build_company_search_url(company_keywords, target_location))

    st.divider()
    st.subheader("Automated public professional discovery")
    st.caption(
        "Searches an external public-web index for publicly indexed LinkedIn profile URLs. "
        "It does not sign in to LinkedIn or scrape profile pages."
    )
    saved_companies = repo.company_names()
    with st.form("automated_discovery_form"):
        if saved_companies:
            target_companies = st.multiselect(
                "Target companies (select one or more)",
                saved_companies,
                default=saved_companies[:1],
            )
        else:
            typed_company = st.text_input("Target company", placeholder="e.g. Accenture")
            target_companies = [typed_company.strip()] if typed_company.strip() else []
        prospect_location = st.text_input("Professional location", "Delhi NCR")
        target_roles = st.multiselect(
            "Find these professional roles",
            list(ROLE_SEARCH_TERMS.keys()),
            default=["Recruiter", "Talent Acquisition", "HR", "Hiring Manager"],
        )
        per_role = st.slider("Maximum profiles per role and company", min_value=1, max_value=5, value=3)
        discover = st.form_submit_button("Find public profiles", type="primary")

    if discover:
        if not settings.exa_api_key:
            st.error("Automated search needs an Exa API key. Add EXA_API_KEY=... to your .env file, save it, and restart Streamlit.")
        elif not target_companies:
            st.error("Enter or select at least one target company.")
        elif not target_roles:
            st.error("Select at least one professional role.")
        else:
            try:
                candidates = []
                added = 0
                failures = []
                request_count = len(target_companies) * len(target_roles)
                with st.spinner(f"Searching {len(target_companies)} company/company target(s) across {len(target_roles)} role(s) — up to {request_count} provider requests..."):
                    for target_company in target_companies:
                        try:
                            if target_company.casefold() not in {name.casefold() for name in saved_companies}:
                                repo.add_company(
                                    target_company,
                                    hiring_focus="Added from automated public prospect discovery",
                                )
                                saved_companies.append(target_company)
                            company_results = search_public_professionals(
                                target_company, target_roles, prospect_location,
                                settings.exa_api_key, max_results_per_role=per_role,
                            )
                            candidates.extend(company_results)
                            added += sum(1 for candidate in company_results if repo.add_prospect_if_new(candidate))
                        except (PublicSearchError, ValueError) as exc:
                            failures.append(f"{target_company}: {exc}")
                st.success(f"Found {len(candidates)} result(s); added {added} new prospect(s); skipped {len(candidates) - added} duplicate(s).")
                if failures:
                    st.warning("Some company searches failed:\n" + "\n".join(failures))
                if candidates:
                    st.dataframe(
                        [{"Name (verify)": p["full_name"], "Target company": p["company"],
                          "Title (verify)": p["title"], "Category": p["category"],
                          "Profile": p["profile_url"]} for p in candidates],
                        use_container_width=True, hide_index=True,
                    )
                    st.info("Search snippets can be incomplete or outdated. Verify each person's current employer and role before drafting or contacting them. New prospects are now available on the Prospects page.")
                else:
                    st.warning("No public LinkedIn profile results matched these filters. Try a different location, company spelling or role.")
            except Exception as exc:
                st.error(f"Discovery could not complete: {exc}")

    if not settings.exa_api_key:
        st.info("No EXA_API_KEY configured. You can still use the manual public-search links below; CSV import is not required.")
    st.divider()
    st.subheader("Manual public search links")
    st.caption("Fallback search links if automated public search is not configured.")
    companies = repo.company_names()
    company = st.selectbox("Company for manual search", [""] + companies) if companies else st.text_input("Company for manual search")
    selected_roles = st.multiselect(
        "Professional roles for manual search",
        list(ROLE_SEARCH_TERMS.keys()),
        default=["Recruiter", "Talent Acquisition", "HR", "Hiring Manager"],
        key="manual_search_roles",
    )
    if company.strip() and selected_roles:
        search_url = build_public_search_url(company, selected_roles)
        for role in selected_roles:
            st.code(build_search_query(company, role))
        st.link_button("Open public web search", search_url)

elif page == "Prospects":
    st.subheader("Professional prospects")
    st.caption("No CSV is required. Discover public profiles automatically or add a professional manually.")
    with st.expander("Optional: import existing prospects from a CSV file"):
        st.caption("You do not need a CSV. Use the Discovery page to find public profiles automatically.")
        upload = st.file_uploader("Choose a prospects CSV", type=["csv"])
        if upload is not None and st.button("Import CSV prospects"):
            try:
                imported = parse_prospect_csv(upload.getvalue())
                existing = {(p["full_name"].casefold(), p["company"].casefold()) for p in repo.list_prospects()}
                added = 0
                skipped = 0
                for row in imported:
                    key = (row["full_name"].casefold(), row["company"].casefold())
                    if key in existing:
                        skipped += 1
                        continue
                    repo.add_prospect(**row)
                    existing.add(key)
                    added += 1
                st.success(f"Imported {added} prospects; skipped {skipped} duplicates.")
            except Exception as exc:
                st.error(f"CSV import failed: {exc}")

    companies = repo.company_names()
    with st.form("prospect_form", clear_on_submit=True):
        full_name = st.text_input("Full name")
        company = st.selectbox("Company", [""] + companies) if companies else st.text_input("Company name")
        title = st.text_input("Current professional title")
        category = st.selectbox("Category", ["Recruiter", "Talent Acquisition", "HR", "Hiring Manager", "Department Head", "Director", "VP / AVP", "C-suite / Founder", "Other"])
        profile = st.text_input("Profile URL (optional)")
        source = st.text_input("Permitted source URL (optional)")
        notes = st.text_area("Professional research notes", help="Only enter relevant professional context.")
        save = st.form_submit_button("Save prospect")
        if save:
            if not full_name.strip() or not company.strip() or not title.strip():
                st.error("Name, company and title are required.")
            else:
                repo.add_prospect(full_name.strip(), company.strip(), title.strip(), category, profile.strip(), source.strip(), notes.strip())
                st.success("Prospect saved.")
    prospects = repo.list_prospects()
    if prospects:
        st.divider()
        display_rows = []
        for p in prospects:
            p_view = dict(p)
            p_view["relevance_score"] = relevance_score(p["category"], p["title"])
            display_rows.append(p_view)
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
        st.download_button(
            "Export prospects CSV",
            data=export_prospects_csv(prospects),
            file_name="linkpilot_prospects.csv",
            mime="text/csv",
        )
        options = {f"{p['full_name']} — {p['title']} at {p['company']} (#{p['id']})": p["id"] for p in prospects}
        chosen = st.selectbox("Choose a prospect", list(options))
        prospect = repo.get_prospect(options[chosen])
        status_options = ["not_contacted", "drafted", "approved", "connection_sent", "connected", "replied", "archived"]
        current_status = prospect.get("outreach_status", "not_contacted")
        new_status = st.selectbox("Outreach status", status_options,
                                  index=status_options.index(current_status) if current_status in status_options else 0)
        if st.button("Update outreach status", disabled=(new_status == current_status)):
            repo.update_prospect_status(prospect["id"], new_status)
            st.success("Outreach status updated.")
        if st.button("Generate personalized note", type="primary"):
            try:
                with st.spinner("Generating draft..."):
                    draft = DraftService().generate(prospect)
                repo.save_draft(prospect["id"], draft)
                st.session_state["draft_editor"] = draft
                st.success("Draft generated. Review it below.")
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
        edited = st.text_area("Connection note", key="draft_editor", height=130)
        if edited.strip() and st.button("Save edited note"):
            repo.save_draft(prospect["id"], edited.strip())
            st.success("Draft saved.")

elif page == "Approval queue":
    st.subheader("Review, approve and track connection requests")
    sent_today = repo.daily_connection_count()
    remaining = max(0, 30 - sent_today)
    meter_left, meter_right = st.columns(2)
    meter_left.metric("Requests recorded today", f"{sent_today} / 30")
    meter_right.metric("Remaining today", remaining)
    st.caption("The counter records requests only after you have sent them yourself on LinkedIn. It does not send invitations.")
    drafts = repo.list_drafts()
    if not drafts:
        st.info("No drafts yet.")
    for item in drafts:
        with st.expander(f"{item['full_name']} — {item['title']} at {item['company']} | {item['status']}"):
            st.write(item["message"])
            st.caption(f"Source: {item['source_url'] or 'Not recorded'}")
            note = st.text_area("Final note", value=item["message"], key=f"note_{item['id']}")
            left, right = st.columns(2)
            if left.button("Save edits", key=f"save_{item['id']}"):
                repo.update_draft(item["id"], note, "draft")
                st.success("Saved.")
            if item["status"] != "approved":
                if right.button("Approve note", key=f"approve_{item['id']}", type="primary"):
                    repo.update_draft(item["id"], note, "approved")
                    st.success("Approved. This does not send a LinkedIn request.")
            else:
                st.success("Approved note — ready for your manual LinkedIn action.")
                if item.get("outreach_status") == "connection_sent":
                    st.success("Request already recorded as sent.")
                else:
                    if item["profile_url"]:
                        st.link_button("Open LinkedIn profile", item["profile_url"])
                    else:
                        st.warning("No profile URL is saved for this prospect.")
                    confirmed = st.checkbox(
                        "I have sent this connection request manually on LinkedIn",
                        key=f"sent_confirm_{item['id']}",
                    )
                    if st.button(
                        "Record as sent",
                        key=f"record_sent_{item['id']}",
                        type="primary",
                        disabled=(remaining <= 0 or not confirmed),
                    ):
                        try:
                            total = repo.record_connection_sent(item["prospect_id"], daily_limit=30)
                            st.success(f"Recorded. {total} of 30 requests counted today.")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
            if item["profile_url"] and item["status"] != "approved":
                st.link_button("Open profile for manual review", item["profile_url"])

elif page == "Settings":
    st.subheader("Configuration")
    st.write("9Router base URL:", settings.llm_base_url)
    st.write("Model:", settings.llm_model or "Not configured")
    st.write("API key configured:", bool(settings.llm_api_key))
    st.divider()
    st.subheader("Public prospect discovery")
    st.write("Exa search API configured:", bool(settings.exa_api_key))
    st.caption("Set EXA_API_KEY in .env to search publicly indexed professional profile pages. CSV is optional.")
    st.write("Database:", settings.database_path)
    if st.button("Test 9Router connection"):
        try:
            with st.spinner("Checking 9Router..."):
                available_models = DraftService().test_connection()
            st.success(f"Connected. {len(available_models)} model(s) are visible.")
            if available_models:
                st.code("\\n".join(available_models[:30]))
        except Exception as exc:
            st.error(f"Connection test failed: {exc}")
    st.info("Keep secrets in .env. Never commit API keys.")
    st.markdown("[9Router documentation](https://docs.9router.com/)")
    st.markdown("[LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)")
