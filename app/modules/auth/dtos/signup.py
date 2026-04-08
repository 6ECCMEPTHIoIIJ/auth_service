from pydantic import BaseModel, Field


class SignupRequestBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=1024)


class SignupResponse(BaseModel):
    id: str
    name: str
