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

class PhoneRequestIn(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    purpose: str = Field(pattern=r'^(register|login)$')

class PhoneVerifyIn(BaseModel):
    phone: str = Field(min_length=7, max_length=32)
    code: str = Field(min_length=4, max_length=8)
    purpose: str = Field(pattern=r'^(register|login)$')

class CompleteProfileIn(BaseModel):
    username: str = Field(min_length=5, max_length=32, pattern=r'^[a-zA-Z0-9_]+$')
    display_name: str = Field(min_length=1, max_length=80)
    avatar: str | None = Field(default=None, max_length=500)
