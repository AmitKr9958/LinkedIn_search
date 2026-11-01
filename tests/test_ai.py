from types import SimpleNamespace
import pytest
from linkpilot.config import Settings
import linkpilot.ai as ai

class FakeModels:
    def list(self):
        return SimpleNamespace(data=[SimpleNamespace(id="test-model")])

class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "test-model"
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="Hello, I would be glad to connect.")
        )])

class FakeClient:
    def __init__(self, **kwargs):
        self.models = FakeModels()
        self.chat = SimpleNamespace(completions=FakeCompletions())

def configured_settings():
    return Settings("http://localhost:20128/v1", "test-key", "test-model", "data/test.db")

def test_ai_connection_and_message_generation(monkeypatch):
    monkeypatch.setattr(ai, "get_settings", configured_settings)
    monkeypatch.setattr(ai, "OpenAI", FakeClient)
    service = ai.DraftService()
    assert service.test_connection() == ["test-model"]
    message = service.generate({
        "full_name": "Alex", "company": "Acme", "title": "Recruiter",
        "category": "Recruiter", "research_notes": "Hiring for BI roles",
    })
    assert message == "Hello, I would be glad to connect."

def test_ai_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        ai, "get_settings",
        lambda: Settings("http://localhost:20128/v1", "", "", "data/test.db"),
    )
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        ai.DraftService()
