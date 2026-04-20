from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Basic AI Agent"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-lite"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
