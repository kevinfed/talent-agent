import logging
import traceback
import multiprocessing
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import AsyncAzureOpenAI
from database import Database
from settings import Settings
from routes.admin_router import router as admin_router
from routes.public_router import router as public_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup")
    try:
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
                logger.info("Created OpenAI and Database clients")
                yield {
                    "db": db,
                    "openai": openai,
                }
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(admin_router)

app.include_router(public_router)


@app.exception_handler(Exception)
async def handle_exc(r: Request, e: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {r.method} {r.url.path}: {str(e)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500, content={"ErrorMessage": f"An internal server error occurred"}
    )


if __name__ == "__main__":
    import gunicorn.app.base

    workers_count = min(9, multiprocessing.cpu_count() * 2 + 1)

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {
                key: value
                for key, value in self.options.items()
                if key in self.cfg.settings and value is not None
            }
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        "bind": "0.0.0.0:8000",
        "workers": workers_count,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "threads": 4,
        "timeout": 120,
        "accesslog": "-",
        "errorlog": "-",
        "loglevel": "info",
    }

    logger.info(f"Starting Gunicorn with {workers_count} workers")
    StandaloneApplication(app, options).run()
