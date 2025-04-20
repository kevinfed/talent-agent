import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # openai deps
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_VERSION: str
    # db deps
    AZURE_COSMOS_URL: str
    AZURE_COSMOS_KEY: str
    DB_NAME: str
    HISTORY_CONTAINER: str
    KB_CONTAINER: str

    # pass name of env file while running locally
    model_config = SettingsConfigDict(
        env_file=".env" if os.environ.get("WEBSITE_SITE_NAME") is None else None,
        extra="ignore",
    )
