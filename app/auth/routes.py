from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Union, Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_db
from auth.utils import (
    create_access_token, check_auth_admin, pwd_context, oauth2_scheme, security, get_current_user, create_permanent_jwt
) 
from auth.service import login_for_access_token
import auth.schemas as schemas
from auth import models
from datetime import datetime
from auth.service import update_token
from database import users_collection, permanent_tokens_collection
auth = APIRouter()


@auth.post("/login", response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    output = await login_for_access_token(form_data.username, form_data.password)
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Incorrect username or password"}],
            headers={"WWW-Authenticate": "Bearer"},
        )

    return output

@auth.post('/change_password')
async def change_password(data: schemas.ChangePasswordRequest, check=Depends(check_auth_admin)):
    # Find user in MongoDB
    user = await users_collection.find_one({"username": data.username})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check
    if not pwd_context.verify(data.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # (hash)
    hashed_new_password = pwd_context.hash(data.new_password)
    await users_collection.update_one(
        {"username": data.username},
        {"$set": {
            "hashed_password": hashed_new_password,
            "updated_time": datetime.utcnow()
        }}
    )

    # create new token
    new_token, to_encode = await create_access_token(data={"sub": user["username"]})
    expired_at = datetime.fromtimestamp(to_encode.get("exp"))

    # Update token in MongoDB
    await update_token(user["username"], new_token, expired_at)

    return {"message": "Password updated successfully"}

@auth.post('/create_access_token', status_code=status.HTTP_201_CREATED, response_model=schemas.CreateAccessToken)
async def create_at(check=Depends(check_auth_admin)):
    admin_username = check.get("username")
    new_token = create_permanent_jwt({"sub": admin_username})
    # Lưu token vào MongoDB
    token_doc = {"token": new_token, "created_by": admin_username}
    await permanent_tokens_collection.insert_one(token_doc)
    return {"token": new_token, "created_by": admin_username}
