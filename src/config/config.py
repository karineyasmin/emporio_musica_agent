"""Application settings and environment validation."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System configuration parameters."""

    PROJECT_NAME: str = "Emporio da Musica Agent"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database & Vector Store
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "emporio_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # API Keys & Models
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    # API & CORS
    CORS_ORIGINS: list[str] = ["*"]
    API_PORT: int = 8000

    # Streamlit
    API_URL: str = "http://api:8000"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
