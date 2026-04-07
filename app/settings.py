import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    database_url: str | None
    openai_api_key: str | None
    openai_model: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "RealEstate MVP"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        database_url=os.getenv("DATABASE_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
