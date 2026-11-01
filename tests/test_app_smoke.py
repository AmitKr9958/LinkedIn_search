import pytest
from streamlit.testing.v1 import AppTest

@pytest.mark.parametrize(
    "page",
    ["Overview", "Companies", "Discovery", "Prospects", "Approval queue", "Settings"],
)
def test_streamlit_page_renders_without_exception(tmp_path, monkeypatch, page):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app-test.db"))
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception

    if page != "Overview":
        app.radio[0].set_value(page).run()
    assert not app.exception
