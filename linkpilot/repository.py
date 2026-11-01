from datetime import datetime
from linkpilot.db import connect

class Repository:
    def add_company(self, name, website="", careers_url="", hiring_focus=""):
        with connect() as c:
            c.execute("INSERT INTO companies(name,website,careers_url,hiring_focus) VALUES(?,?,?,?)",
                      (name, website, careers_url, hiring_focus))

    def list_companies(self):
        with connect() as c:
            return [dict(r) for r in c.execute("SELECT * FROM companies ORDER BY name COLLATE NOCASE")]

    def company_names(self):
        return [r["name"] for r in self.list_companies()]

    def add_prospect(self, full_name, company, title, category, profile_url="", source_url="", research_notes=""):
        with connect() as c:
            c.execute("""INSERT INTO prospects(full_name,company,title,category,profile_url,source_url,research_notes)
                         VALUES(?,?,?,?,?,?,?)""",
                      (full_name, company, title, category, profile_url, source_url, research_notes))

    def add_prospect_if_new(self, prospect):
        """Insert a discovered prospect only if its public profile URL is not already stored."""
        profile_url = (prospect.get("profile_url") or "").strip().rstrip("/")
        with connect() as c:
            if profile_url:
                existing = c.execute(
                    "SELECT id FROM prospects WHERE lower(rtrim(profile_url, '/'))=lower(?) LIMIT 1",
                    (profile_url,),
                ).fetchone()
                if existing:
                    return False
            c.execute(
                """INSERT INTO prospects(full_name,company,title,category,profile_url,source_url,research_notes)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    prospect.get("full_name", "Name not available"),
                    prospect.get("company", ""),
                    prospect.get("title", "Profile found — verify current role"),
                    prospect.get("category", "Other"),
                    profile_url,
                    prospect.get("source_url", ""),
                    prospect.get("research_notes", ""),
                ),
            )
            return True

    def list_prospects(self):
        with connect() as c:
            return [dict(r) for r in c.execute("SELECT * FROM prospects ORDER BY created_at DESC,id DESC")]

    def get_prospect(self, prospect_id):
        with connect() as c:
            row = c.execute("SELECT * FROM prospects WHERE id=?", (prospect_id,)).fetchone()
            return dict(row) if row else None

    def save_draft(self, prospect_id, message):
        with connect() as c:
            row = c.execute("SELECT id FROM drafts WHERE prospect_id=? ORDER BY id DESC LIMIT 1",
                            (prospect_id,)).fetchone()
            if row:
                c.execute("UPDATE drafts SET message=?,status='draft',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                          (message, row["id"]))
            else:
                c.execute("INSERT INTO drafts(prospect_id,message) VALUES(?,?)", (prospect_id, message))
            c.execute("UPDATE prospects SET outreach_status='drafted' WHERE id=?", (prospect_id,))

    def list_drafts(self):
        with connect() as c:
            rows = c.execute("""SELECT d.*,p.full_name,p.company,p.title,p.profile_url,p.source_url,p.outreach_status
                                FROM drafts d JOIN prospects p ON p.id=d.prospect_id
                                ORDER BY d.updated_at DESC,d.id DESC""")
            return [dict(r) for r in rows]

    def update_draft(self, draft_id, message, status="draft"):
        if status not in {"draft", "approved", "archived"}:
            raise ValueError("Invalid draft status")
        with connect() as c:
            c.execute("UPDATE drafts SET message=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (message, status, draft_id))
            if status == "approved":
                row = c.execute("SELECT prospect_id FROM drafts WHERE id=?", (draft_id,)).fetchone()
                if row:
                    c.execute("UPDATE prospects SET outreach_status='approved' WHERE id=?", (row["prospect_id"],))

    def stats(self):
        with connect() as c:
            return {
                "companies": c.execute("SELECT COUNT(*) FROM companies").fetchone()[0],
                "prospects": c.execute("SELECT COUNT(*) FROM prospects").fetchone()[0],
                "drafts": c.execute("SELECT COUNT(*) FROM drafts").fetchone()[0],
                "approved": c.execute("SELECT COUNT(*) FROM drafts WHERE status='approved'").fetchone()[0],
            }

    def daily_connection_count(self, on_date=None):
        """Return connection requests manually recorded for a local calendar date."""
        target_date = on_date or datetime.now().astimezone().date().isoformat()
        with connect() as c:
            return c.execute(
                "SELECT COUNT(*) FROM connection_events WHERE substr(sent_at,1,10)=?",
                (target_date,),
            ).fetchone()[0]

    def record_connection_sent(self, prospect_id, daily_limit=30, sent_on=None):
        """Record a request only after the user has manually sent it on LinkedIn."""
        now = datetime.now().astimezone()
        target_date = sent_on or now.date().isoformat()
        sent_at = now.isoformat(timespec="seconds") if sent_on is None else f"{target_date}T12:00:00"
        with connect() as c:
            # Serialize the check-and-insert so parallel app sessions cannot exceed the cap.
            c.execute("BEGIN IMMEDIATE")
            prospect = c.execute(
                "SELECT id, outreach_status FROM prospects WHERE id=?",
                (prospect_id,),
            ).fetchone()
            if not prospect:
                raise ValueError("Prospect not found.")
            approved = c.execute(
                "SELECT 1 FROM drafts WHERE prospect_id=? AND status='approved' LIMIT 1",
                (prospect_id,),
            ).fetchone()
            if not approved:
                raise ValueError("Approve a connection note before recording a sent request.")
            if c.execute(
                "SELECT 1 FROM connection_events WHERE prospect_id=?",
                (prospect_id,),
            ).fetchone():
                raise ValueError("A connection request is already recorded for this prospect.")
            sent_count = c.execute(
                "SELECT COUNT(*) FROM connection_events WHERE date(sent_at)=?",
                (target_date,),
            ).fetchone()[0]
            if sent_count >= daily_limit:
                raise ValueError(f"Daily limit reached ({daily_limit} connection requests).")
            c.execute(
                "INSERT INTO connection_events(prospect_id,sent_at) VALUES(?,?)",
                (prospect_id, sent_at),
            )
            c.execute(
                "UPDATE prospects SET outreach_status='connection_sent' WHERE id=?",
                (prospect_id,),
            )
            return sent_count + 1

    def update_prospect_status(self, prospect_id, status):
        allowed = {"not_contacted", "drafted", "approved", "connected", "replied", "archived"}
        if status not in allowed:
            raise ValueError("Invalid prospect outreach status; use the manual-send confirmation workflow.")
        with connect() as c:
            c.execute("UPDATE prospects SET outreach_status=? WHERE id=?", (status, prospect_id))
