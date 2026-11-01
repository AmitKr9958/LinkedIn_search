import pytest
from linkpilot.csv_tools import parse_prospect_csv

def test_csv_parser_validates_and_reads_rows():
    data = b"full_name,company,title,category\nAlex,Acme,Recruiter,Recruiter\n"
    rows = parse_prospect_csv(data)
    assert rows[0]["full_name"] == "Alex"
    assert rows[0]["category"] == "Recruiter"

def test_csv_parser_requires_columns():
    with pytest.raises(ValueError):
        parse_prospect_csv(b"name,company\nAlex,Acme\n")

def test_csv_export_neutralizes_formula_cells():
    from linkpilot.csv_tools import export_prospects_csv
    data = export_prospects_csv([{
        "full_name": "=HYPERLINK(\"https://bad.example\")",
        "company": "Acme",
        "title": "Recruiter",
    }]).decode("utf-8-sig")
    assert "'=HYPERLINK" in data
