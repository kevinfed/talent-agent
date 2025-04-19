import traceback
from fastapi import FastAPI
from models import ResponseMessage, ErrorMessage

app = FastAPI()

@app.exception_handler(Exception)
async def handle_exc(e: Exception) -> ErrorMessage:
    return ErrorMessage(str(e) + "\n" + traceback.format_exc())

@app.get("/")
def root() -> ResponseMessage:
    return ResponseMessage("Application active <3")

if __name__ == "__main__":
    import gunicorn