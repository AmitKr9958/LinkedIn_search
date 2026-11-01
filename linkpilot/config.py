import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    database_path: str

def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:20128/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        database_path=os.getenv("DATABASE_PATH", "data/linkpilot.db"),
    )
