from pydantic import BaseModel, Field


class SigninRequestBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=1024)


class SigninResponse(BaseModel):
    id: str
