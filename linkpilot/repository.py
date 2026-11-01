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

    def list_drafts(self):
        with connect() as c:
            rows = c.execute("""SELECT d.*,p.full_name,p.company,p.title,p.profile_url,p.source_url
                                FROM drafts d JOIN prospects p ON p.id=d.prospect_id
                                ORDER BY d.updated_at DESC,d.id DESC""")
            return [dict(r) for r in rows]

    def update_draft(self, draft_id, message, status="draft"):
        if status not in {"draft", "approved", "archived"}:
            raise ValueError("Invalid draft status")
        with connect() as c:
            c.execute("UPDATE drafts SET message=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (message, status, draft_id))

    def stats(self):
        with connect() as c:
            return {
                "companies": c.execute("SELECT COUNT(*) FROM companies").fetchone()[0],
                "prospects": c.execute("SELECT COUNT(*) FROM prospects").fetchone()[0],
                "drafts": c.execute("SELECT COUNT(*) FROM drafts").fetchone()[0],
                "approved": c.execute("SELECT COUNT(*) FROM drafts WHERE status='approved'").fetchone()[0],
            }
