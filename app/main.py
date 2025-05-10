from exceptions import AppBaseException
from datetime import datetime
from auth.utils import create_access_token, pwd_context
from fastapi.middleware.cors import CORSMiddleware
from configs import configs
from auth import models
from database import users_collection, tokens_collection
from auth.routes import auth
from modules.chat.routes import chat_router
from modules.document.routes import document
from modules.document.utils import initialize_vectorstore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import warnings

warnings.filterwarnings('ignore')


# models.Base.metadata.create_all(bind=engine)

class AppState:
    """Application state class to store global variables"""

    def __init__(self):
        self.vectorstore = None


app = FastAPI()
app.state = AppState()

origins = ["*", ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(f"/alembic", StaticFiles(directory="alembic"), name="alembic")
app.include_router(chat_router, prefix=configs.ROUTER, tags=['Chat'])
app.include_router(auth, prefix=configs.ROUTER, tags=['Auth'])
app.include_router(document, prefix=configs.ROUTER, tags=['Document'])


async def create_superuser(email=None, password=None, is_active=True, is_admin=True, ):
    """
    Tạo một superuser nếu chưa tồn tại.
    Nếu email và password không được truyền vào, sẽ lấy từ configs.
    """

    email = email
    password = password
    is_active = is_active
    is_admin = is_admin

    # Hash password
    hashed_password = pwd_context.hash(password)

    existing_user = await users_collection.find_one({"email": email})

    if existing_user is None:
        mongo_user = {
            "email": email,
            "hashed_password": hashed_password,
            "is_active": is_active,
            "is_admin": is_admin,
            "created_time": datetime.utcnow(),
            "updated_time": datetime.utcnow(),
        }
        await users_collection.insert_one(mongo_user)
        print(f"✅ Superuser '{email}' created in MongoDB!")
        # Create token
        access_token, to_encode = await create_access_token(data={"sub": email})
        expired_at = datetime.fromtimestamp(to_encode.get("exp"))

        # Save token MongoDB
        await tokens_collection.insert_one({
            "access_token": access_token,
            "email": email,
            "expired_at": expired_at
        })
    else:
        print(f"✅ Superuser '{email}' already exists in MongoDB!")


@app.on_event("startup")
async def startup_event():
    # Create superuser
    await create_superuser(
        email=configs.toml_settings['superuser']['email'],
        password=configs.toml_settings['superuser']['password'],
        is_active=configs.toml_settings['superuser']['is_activate'],
        is_admin=configs.toml_settings['superuser']['is_admin'],
    )

    # Initialize vectorstore and store in app state
    app.state.vectorstore = await initialize_vectorstore()
    print(f"✅ Vectorstore initialized and stored in app state")


@app.exception_handler(AppBaseException)
async def app_base_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail}
    )
