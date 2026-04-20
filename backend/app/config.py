from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    claude_haiku_model: str = "claude-haiku-4-5"
    database_url: str = "sqlite:///./closecheck.db"
    upload_dir: str = "./uploads"
    reports_dir: str = "./reports"
    max_file_size_mb: int = 25
    max_files_per_job: int = 20
    api_key: str = "dev-key"
    demo_mode: bool = True
    rate_limit_window_hours: int = 24
    rate_limit_max_files: int = 20

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()

# Ensure directories exist on import
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
