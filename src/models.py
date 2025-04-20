from pydantic import BaseModel


class ResponseMessage(BaseModel):
    text: str


class ChatRequest(BaseModel):
    text: str
