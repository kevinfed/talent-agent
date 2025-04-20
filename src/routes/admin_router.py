import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.routing import APIRouter
from fastapi import BackgroundTasks, Depends
from utils import get_deps
from models import ChatRequest, ResponseMessage


router = APIRouter()
