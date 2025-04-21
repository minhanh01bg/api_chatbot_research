from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth import models
from database import get_db
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form, Depends, Security, Header
from auth.config import settings
from database import users_collection, tokens_collection, permanent_tokens_collection
# from sqlalchemy.future import select 
from sqlalchemy import select
# Khởi tạo CryptContext để mã hóa mật khẩu
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Khởi tạo OAuth2PasswordBearer và HTTPBearer
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token")


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt, to_encode



# Check token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Signature has expired"}],
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if not username:
            raise credentials_exception

        # Find user MongoDB
        user = await users_collection.find_one({"username": username})
        if not user:
            raise credentials_exception

        # Check token
        token = await tokens_collection.find_one({"access_token": credentials.credentials})
        if not token:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return user

# Check admin
async def check_auth_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    user = await get_current_user(credentials)
    
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "User is not admin"}]
        )
    return user


async def check_permanent_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=[{"msg": "Invalid token"}],
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Truy vấn MongoDB
    db_token = await permanent_tokens_collection.find_one({"token": credentials.credentials})
    
    if db_token is None:
        raise credentials_exception

    return db_token


def create_permanent_jwt(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=
                             settings.ALGORITHM)
    return encoded_jwt