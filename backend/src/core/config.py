from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "KeepAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database connection
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # Database pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Auth
    SECRET_KEY: str = "changethis"  # In prod: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_TIMEOUT_SECONDS: float = 60.0
    # Map task_type labels to specific models, e.g. '{"code": "codellama", "analysis": "llama3"}'
    MODEL_ROUTING: dict[str, str] = {}

    # CORS — use specific origins in production, e.g. '["https://myapp.com"]'
    CORS_ORIGINS: list[str] = ["*"]

    # Rate limiting (slowapi format: "N/period")
    RATE_LIMIT_LLM: str = "20/minute"

    # Development mode — enables hot reload via uvicorn
    DEV_MODE: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
