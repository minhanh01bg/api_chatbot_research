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


@auth.post("/login",response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def access_token(data: schemas.LoginRequest):
    output = await login_for_access_token(data.email, data.password)
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Incorrect email or password"}],
            headers={"WWW-Authenticate": "Bearer"},
        )

    return output

@auth.post('/change_password', status_code=status.HTTP_200_OK)
async def change_password(
    data: schemas.ChangePasswordRequest,
    current_user=Depends(get_current_user)
):
    # Ensure user is authenticated
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify old password
    if not pwd_context.verify(data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Hash new password and update in DB
    hashed_new_password = pwd_context.hash(data.new_password)
    update_result = await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": {
            "hashed_password": hashed_new_password,
            "updated_time": datetime.utcnow()
        }}
    )
    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update password")

    # Create new access token
    new_token, to_encode = await create_access_token(data={"sub": current_user["email"]})
    expired_at = datetime.fromtimestamp(to_encode.get("exp"))

    # Update token in MongoDB
    await update_token(current_user["email"], new_token, expired_at)

    return {"message": "Password updated successfully", "access_token": new_token}

@auth.post('/create_access_token', status_code=status.HTTP_201_CREATED, response_model=schemas.CreateAccessToken)
async def create_at(check=Depends(check_auth_admin)):
    admin_email = check.get("email")
    new_token = create_permanent_jwt({"sub": admin_email})
    # Lưu token vào MongoDB
    token_doc = {"token": new_token, "created_by": admin_email}
    await permanent_tokens_collection.insert_one(token_doc)
    return {"token": new_token, "created_by": admin_email}


@auth.post('/register', status_code=status.HTTP_201_CREATED, response_model=schemas.User)
async def register(user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    user_data = {
        "email": user.email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_admin": False,
        "created_time": datetime.utcnow(),
        "updated_time": datetime.utcnow()
    }
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Insert new user into MongoDB
    result = await users_collection.insert_one(user_data)
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create user")
    # Get the inserted user
    new_user = await users_collection.find_one({"_id": result.inserted_id})
    if not new_user:
        raise HTTPException(status_code=500, detail="Failed to retrieve created user")
    # Create a response object
    response_user = schemas.User(
        id=str(new_user["_id"]),
        email=new_user["email"],
        is_active=new_user["is_active"],
        is_admin=new_user["is_admin"],
        created_time=new_user["created_time"],
        updated_time=new_user["updated_time"]
    )
    return response_user