from pydantic import BaseModel, Field
import datetime

class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    username: str
    password: str

class User(UserBase):
    id: str
    is_active: bool
    is_admin: bool
    # class Config:
    #     orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class CreateAccessToken(BaseModel):
    token: str
    created_by: str