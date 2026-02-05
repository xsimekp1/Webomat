from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: str = (
        "http://localhost:3000,"
        "https://webomat.vercel.app,"
        "https://frontend-*.vercel.app,"
        "https://*.vercel.app"
    )

    # Azure OpenAI (optional)
    azure_openai_api_version: str | None = None

    # Screenshot API (optional)
    screenshot_api_url: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in env file


@lru_cache()
def get_settings() -> Settings:
    return Settings()
