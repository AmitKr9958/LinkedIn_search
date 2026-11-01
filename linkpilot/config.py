import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    database_path: str
    exa_api_key: str = ""


def _configured_value(name: str, default: str = "") -> str:
    """Treat example placeholders as missing configuration, not real credentials."""
    value = os.getenv(name, default).strip()
    lowered = value.casefold()
    if not value or lowered.startswith(("replace_with_", "your_actual_", "your_")):
        return ""
    return value


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:20128/v1").strip(),
        llm_api_key=_configured_value("LLM_API_KEY"),
        llm_model=_configured_value("LLM_MODEL"),
        database_path=os.getenv("DATABASE_PATH", "data/linkpilot.db").strip(),
        exa_api_key=_configured_value("EXA_API_KEY"),
    )
