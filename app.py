from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from linkpilot.db import init_db
from linkpilot.repository import Repository
from linkpilot.ai import DraftService
from linkpilot.config import get_settings

st.set_page_config(page_title="LinkPilot AI", page_icon="🤝", layout="wide")
init_db()
repo = Repository()
settings = get_settings()

st.title("🤝 LinkPilot AI")
st.caption("Professional networking research and personalized outreach — with your approval.")
with st.sidebar:
    st.header("Workspace")
    page = st.radio("Navigate", ["Overview", "Companies", "Prospects", "Approval queue", "Settings"])
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

elif page == "Prospects":
    st.subheader("Professional prospects")
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
        st.dataframe(prospects, use_container_width=True, hide_index=True)
        options = {f"{p['full_name']} — {p['title']} at {p['company']} (#{p['id']})": p["id"] for p in prospects}
        chosen = st.selectbox("Choose a prospect", list(options))
        prospect = repo.get_prospect(options[chosen])
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
    st.write("Database:", settings.database_path)
    st.info("Keep secrets in .env. Never commit API keys.")
    st.markdown("[9Router documentation](https://docs.9router.com/)")
    st.markdown("[LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)")
