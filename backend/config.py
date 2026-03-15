from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    sync_database_url: str

    # Cache
    redis_url: str = "redis://localhost:6379/0"

    # AI - Groq (primary)
    groq_api_key: str
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # AI - NVIDIA NIM (fallback)
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-405b-instruct"

    # GitHub
    github_token: str
    github_token_2: str = ""

    # Skills.sh
    skills_sh_base_url: str = "https://skills.sh"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    admin_token: str = "changeme"

    # Tier 1 threshold — skills with install_count >= this get stored in DB
    tier1_min_installs: int = 50
    # Max skills to store in Tier 1 (keep DB under 500MB)
    tier1_max_skills: int = 25000

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
