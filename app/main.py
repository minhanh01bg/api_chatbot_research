from exceptions import AppBaseException
from datetime import datetime
from auth.utils import create_access_token, pwd_context
from fastapi.middleware.cors import CORSMiddleware
from configs import configs
from auth import models
from database import users_collection, tokens_collection
from auth.routes import auth
from modules.chat.routes import chat
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import warnings

warnings.filterwarnings('ignore')


# models.Base.metadata.create_all(bind=engine)

app = FastAPI()


origins = ["*", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(f"/alembic", StaticFiles(directory="alembic"), name="alembic")
app.include_router(chat, prefix=configs.ROUTER, tags=['Chat'])
app.include_router(auth, prefix=configs.ROUTER, tags=['Auth'])



async def create_superuser(username=None, password=None, is_active=True, is_admin=True, user_id=None):
    """
    Tạo một superuser nếu chưa tồn tại.
    Nếu username và password không được truyền vào, sẽ lấy từ configs.
    """

    username = username
    password = password
    is_active = is_active
    is_admin = is_admin
    user_id = user_id

    # Hash password
    hashed_password = pwd_context.hash(password)

    existing_user = await users_collection.find_one({"username": username})

    if existing_user is None:
        mongo_user = {
            "_id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "is_active": is_active,
            "is_admin": is_admin,
            "created_time": datetime.utcnow(),
            "updated_time": datetime.utcnow(),
        }
        await users_collection.insert_one(mongo_user)
        print(f"✅ Superuser '{username}' created in MongoDB!")
        # Create token
        access_token, to_encode = await create_access_token(data={"sub": username})
        expired_at = datetime.fromtimestamp(to_encode.get("exp"))

        # Save token MongoDB
        await tokens_collection.insert_one({
            # "_id": user_id,
            "access_token": access_token,
            "username": username,
            "expired_at": expired_at
        })
    else:
        print(f"✅ Superuser '{username}' already exists in MongoDB!")



@app.on_event("startup")
async def startup_event():
    await create_superuser(
        username=configs.toml_settings['superuser']['username'],
        password=configs.toml_settings['superuser']['password'],
        is_active=configs.toml_settings['superuser']['is_activate'],
        is_admin=configs.toml_settings['superuser']['is_admin'],
        user_id=configs.toml_settings['superuser']['id']
    )


@app.exception_handler(AppBaseException)
async def app_base_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail}
    )
