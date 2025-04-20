import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncAzureOpenAI

from database import Database
from settings import Settings
from core.chat_agent import agent as chat_agent
from models import ResponseMessage, ErrorMessage, ChatRequest

settings = Settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with AsyncAzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_VERSION,
    ) as openai:
        async with Database.connect(
            settings.AZURE_COSMOS_URL,
            settings.AZURE_COSMOS_KEY,
            settings.DB_NAME,
            settings.HISTORY_CONTAINER,
            settings.KB_CONTAINER,
        ) as db:
            yield {
                "db": db,
                "openai": openai,
            }


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def handle_exc(e: Exception) -> ErrorMessage:
    return ErrorMessage(str(e) + "\n" + traceback.format_exc())


@app.get("/")
def root() -> ResponseMessage:
    return ResponseMessage("Application active <3")


@app.post("/talent-agent")
async def chat(chatRequest: ChatRequest) -> ResponseMessage: ...


if __name__ == "__main__":
    import gunicorn
