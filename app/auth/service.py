from sqlalchemy.orm import Session
from auth import models
from datetime import datetime
from auth import schemas
from auth.utils import (
    create_access_token, check_auth_admin, pwd_context, oauth2_scheme, security, get_current_user
)
from fastapi import HTTPException, status
from database import tokens_collection, users_collection


def add_token(db: Session, email: str, access_token: str, expired_at: datetime):
    db_token = models.Token(access_token=access_token,
                            email=email, expired_at=expired_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


async def update_token(email: str, access_token: str, expired_at: datetime):
    await tokens_collection.update_one(
        {"email": email},
        {"$set": {
            "access_token": access_token,
            "expired_at": expired_at
        }},
        upsert=True  # Nếu chưa có token thì tạo mới
    )


async def get_token_by_user_id(email: str):
    return await tokens_collection.find_one({"email": email})


async def authenticate_user(email: str, password: str):
    user = await users_collection.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=[{"msg": "User not found"}]
        )

    if not pwd_context.verify(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Incorrect password"}]
        )
    
    return user


async def login_for_access_token(email: str, password: str):
    user = await authenticate_user(email, password)
    if not user:
        return None

    # check token expired
    token = await get_token_by_user_id(email)
    
    if token and token["expired_at"] >= datetime.utcnow():
        access_token = token["access_token"]
    else:
        access_token, to_encode = await create_access_token(data={"sub": email})
        expiration_date = datetime.fromtimestamp(to_encode.get("exp"))

        if token:
            # Update token
            await tokens_collection.update_one(
                {"email": email},
                {"$set": {"access_token": access_token, "expired_at": expiration_date}}
            )
        else:
            # Add new token
            await tokens_collection.insert_one({
                "email": email,
                "access_token": access_token,
                "expired_at": expiration_date
            })
    data = {"id": str(user["_id"]),"email": email}
    return {"access_token": access_token, "token_type": "bearer", "user": data}