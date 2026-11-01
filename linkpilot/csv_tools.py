import csv
import io

REQUIRED_COLUMNS = {"full_name", "company", "title"}

def parse_prospect_csv(raw: bytes):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded.") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV is empty or has no header row.")
    fields = {name.strip() for name in reader.fieldnames if name}
    missing = REQUIRED_COLUMNS - fields
    if missing:
        raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))
    rows = []
    for line_number, row in enumerate(reader, start=2):
        clean = {str(k).strip(): (v or "").strip() for k, v in row.items() if k}
        if not clean.get("full_name") or not clean.get("company") or not clean.get("title"):
            continue
        rows.append({
            "full_name": clean["full_name"],
            "company": clean["company"],
            "title": clean["title"],
            "category": clean.get("category") or "Other",
            "profile_url": clean.get("profile_url", ""),
            "source_url": clean.get("source_url", ""),
            "research_notes": clean.get("research_notes", ""),
        })
    return rows

def export_prospects_csv(rows):
    output = io.StringIO()
    fields = ["full_name", "company", "title", "category", "profile_url", "source_url", "research_notes"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe_row = {}
        for field in fields:
            value = str(row.get(field, "") or "")
            trimmed = value.lstrip(" \\t\\r\\n")
            if trimmed.startswith(("=", "+", "-", "@")):
                value = "'" + value
            safe_row[field] = value
        writer.writerow(safe_row)
    return output.getvalue().encode("utf-8-sig")
