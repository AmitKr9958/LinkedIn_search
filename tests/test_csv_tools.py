import pytest
from linkpilot.csv_tools import parse_prospect_csv, export_prospects_csv

def test_csv_parser_validates_and_reads_rows():
    data = b"full_name,company,title,category\\nAlex,Acme,Recruiter,Recruiter\\n"
    rows = parse_prospect_csv(data)
    assert rows[0]["full_name"] == "Alex"
    assert rows[0]["category"] == "Recruiter"

def test_csv_parser_requires_columns():
    with pytest.raises(ValueError):
        parse_prospect_csv(b"name,company\\nAlex,Acme\\n")

def test_csv_parser_rejects_non_utf8():
    with pytest.raises(ValueError, match="UTF-8"):
        parse_prospect_csv(b"\\xff\\xfe\\x00")

def test_csv_export_neutralizes_formula_cells():
    data = export_prospects_csv([{
        "full_name": "=HYPERLINK(\\\"https://bad.example\\\")",
        "company": "Acme",
        "title": "Recruiter",
    }]).decode("utf-8-sig")
    assert "'=HYPERLINK" in data

def test_csv_export_neutralizes_leading_whitespace_formula():
    data = export_prospects_csv([{
        "full_name": "  =1+1",
        "company": "Acme",
        "title": "Recruiter",
    }]).decode("utf-8-sig")
    assert "'  =1+1" in data
