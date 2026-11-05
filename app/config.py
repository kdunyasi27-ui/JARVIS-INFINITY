
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JARVIS INFINITY"
    app_env: str = "production"

    jarvis_api_token: str = "change-me"
    session_secret: str = "change-this-to-a-long-random-secret"

    database_path: str = "./data/jarvis.db"

    # Normal yapay zekâ bağlantısı
    model_base_url: str = ""
    model_api_key: str = ""
    model_name: str = ""
    model_fallbacks: str = ""
    model_timeout_seconds: int = 45

    # Gemini Live - gerçek zamanlı sesli asistan
    gemini_live_api_key: str = ""
    gemini_live_model: str = "gemini-3.8-live"

    # İnternet araması
    search_api_url: str = ""
    search_api_key: str = ""

    cors_origins: str = (
        "http://127.0.0.1:8000,"
        "http://localhost:8000"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def allowed_origins(self):
        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]


settings = Settings()
