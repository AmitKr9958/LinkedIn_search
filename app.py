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

st.set_page_config(page_title="LinkPilot AI", page_icon="🤝", layout="wide")
init_db()
repo = Repository()
settings = get_settings()

st.title("🤝 LinkPilot AI")
st.caption("Professional networking research and personalized outreach — with your approval.")
with st.sidebar:
    st.header("Workspace")
    page = st.radio("Navigate", ["Overview", "Companies", "Discovery", "Prospects", "Approval queue", "Settings"])
    st.divider()
    st.info("Human approval required. No LinkedIn login, scraping, browser automation or automatic sending.")

if page == "Overview":
    stats = repo.stats()
    cols = st.columns(4)
    for col, label, key in zip(cols, ["Companies", "Prospects", "Drafts", "Approved"],
                               ["companies", "prospects", "drafts", "approved"]):
        col.metric(label, stats[key])
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
            target_company = st.selectbox("Target company", saved_companies)
        else:
            target_company = st.text_input("Target company", placeholder="e.g. Accenture")
        prospect_location = st.text_input("Professional location", "India")
        target_roles = st.multiselect(
            "Find these professional roles",
            list(ROLE_SEARCH_TERMS.keys()),
            default=["Recruiter", "Talent Acquisition", "HR", "Hiring Manager"],
        )
        per_role = st.slider("Maximum profiles per role", min_value=1, max_value=10, value=5)
        discover = st.form_submit_button("Find public profiles", type="primary")

    if discover:
        if not settings.exa_api_key:
            st.error("Automated search needs an Exa API key. Add EXA_API_KEY=... to your .env file, save it, and restart Streamlit.")
        elif not target_company.strip():
            st.error("Enter or select a target company.")
        elif not target_roles:
            st.error("Select at least one professional role.")
        else:
            try:
                with st.spinner("Searching public results and checking for duplicates..."):
                    candidates = search_public_professionals(
                        target_company, target_roles, prospect_location,
                        settings.exa_api_key, max_results_per_role=per_role,
                    )
                    added = sum(1 for candidate in candidates if repo.add_prospect_if_new(candidate))
                st.success(f"Found {len(candidates)} matching public profile result(s); added {added} new prospect(s); skipped {len(candidates) - added} duplicate(s).")
                if candidates:
                    st.dataframe(
                        [{"Name (verify)": p["full_name"], "Title (verify)": p["title"],
                          "Category": p["category"], "Profile": p["profile_url"]} for p in candidates],
                        use_container_width=True, hide_index=True,
                    )
                    st.info("Search snippets can be incomplete or outdated. Verify each person's current employer and role before drafting or contacting them. New prospects are now available on the Prospects page.")
                else:
                    st.warning("No public LinkedIn profile results matched these filters. Try a different location, company spelling or role.")
            except (PublicSearchError, ValueError) as exc:
                st.error(str(exc))

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
    st.caption("You can import records from a CSV you are authorized to use. The app does not collect LinkedIn profile data itself.")
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
        if st.button("Update outreach status"):
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
    st.subheader("Review and approve drafts")
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
                st.success("Approved — not sent.")
            if item["profile_url"]:
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
