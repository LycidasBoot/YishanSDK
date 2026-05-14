from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://crawler:crawler123@localhost:5432/crawler_stats"
    api_base_url: str = "http://localhost:8000"
    site_id: int = 1
    log_path: str = "./sample_access.log"
    offset_path: str = "./agent_offset.json"
    dashboard_username: str = "yishankeji"
    dashboard_password: str = "YishanSDK8888"
    session_secret: str = "change-me-in-production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
