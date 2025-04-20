from pydantic_settings import BaseSettings


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
