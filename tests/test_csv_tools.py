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
