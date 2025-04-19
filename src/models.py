from pydantic import BaseModel

class ResponseMessage(BaseModel):
    mssg: str

class ErrorMessage(BaseModel):
    err: str