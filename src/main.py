from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root() -> str:
    return {
        "Response": "Application active <3"
    }

if __name__ == "__main__":
    import gunicorn