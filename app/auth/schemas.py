from pydantic import BaseModel, Field
import datetime

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    email: str
    password: str

class User(UserBase):
    id: str
    is_active: bool
    is_admin: bool
    # class Config:
    #     orm_mode = True

class UserLogin(BaseModel):
    email: str
    password: str

class UserRespone(BaseModel):
    id: str
    email: str

class Token(BaseModel):
    
    access_token: str
    token_type: str
    user: UserRespone

class TokenData(BaseModel):
    email: str | None

class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str

class CreateAccessToken(BaseModel):
    token: str
    created_by: str


class LoginRequest(BaseModel):
    email: str
    password: str