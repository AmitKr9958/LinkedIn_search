import sqlite3
from pathlib import Path

from linkpilot.config import Settings
import linkpilot.db as db

def test_existing_database_gets_outreach_status_migration(tmp_path, monkeypatch):
    database = Path(tmp_path) / "legacy.db"
    conn = sqlite3.connect(database)
    conn.execute("""CREATE TABLE prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL, company TEXT NOT NULL, title TEXT NOT NULL,
        category TEXT NOT NULL, profile_url TEXT, source_url TEXT, research_notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute(
        "INSERT INTO prospects(full_name,company,title,category) VALUES(?,?,?,?)",
        ("Jordan", "Example Ltd", "Recruiter", "Recruiter"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(
        db,
        "get_settings",
        lambda: Settings(
            llm_base_url="http://localhost:20128/v1",
            llm_api_key="",
            llm_model="",
            database_path=str(database),
        ),
    )
    db.init_db()

    conn = sqlite3.connect(database)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(prospects)")}
    status = conn.execute("SELECT outreach_status FROM prospects WHERE full_name='Jordan'").fetchone()[0]
    conn.close()
    assert "outreach_status" in columns
    assert status == "not_contacted"
