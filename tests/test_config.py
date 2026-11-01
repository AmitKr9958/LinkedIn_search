import pytest

from linkpilot.config import get_settings


def test_example_placeholders_are_not_treated_as_configured_secrets(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "replace_with_your_9router_key")
    monkeypatch.setenv("LLM_MODEL", "replace_with_exact_model_id")
    monkeypatch.setenv("EXA_API_KEY", "")
    settings = get_settings()
    assert settings.llm_api_key == ""
    assert settings.llm_model == ""
    assert settings.exa_api_key == ""


def test_real_configured_values_are_preserved(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "router-secret-value")
    monkeypatch.setenv("LLM_MODEL", "provider/model")
    monkeypatch.setenv("EXA_API_KEY", "exa-secret-value")
    settings = get_settings()
    assert settings.llm_api_key == "router-secret-value"
    assert settings.llm_model == "provider/model"
    assert settings.exa_api_key == "exa-secret-value"
