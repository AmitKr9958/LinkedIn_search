from pathlib import Path

def test_ai_module_does_not_include_browser_automation():
    source = Path("linkpilot/ai.py").read_text(encoding="utf-8").lower()
    assert "playwright" not in source
    assert "selenium" not in source
