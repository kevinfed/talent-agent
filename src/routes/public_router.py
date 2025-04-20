import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.routing import APIRouter
from fastapi import BackgroundTasks, Depends
from utils import get_deps
from models import ChatRequest, ResponseMessage


router = APIRouter()


@router.get("/")
def root() -> ResponseMessage:
    return ResponseMessage("Application active <3")


@router.post("/talent-agent")
async def chat(
    chatRequest: ChatRequest,
    background_tasks: BackgroundTasks,
    deps: dict = Depends(get_deps),
) -> ResponseMessage: ...
