from pydantic import BaseModel


class ResponseMessage(BaseModel):
    text: str


class ErrorMessage(BaseModel):
    err: str


class ChatRequest(BaseModel):
    text: str
