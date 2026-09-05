from pydantic import BaseModel, Field
class RegisterIn(BaseModel):
    username: str = Field(min_length=5, max_length=32, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)
class LoginIn(BaseModel):
    username: str
    password: str
class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'
