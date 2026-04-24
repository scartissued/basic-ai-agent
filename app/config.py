from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Basic AI Agent"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    weather_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
