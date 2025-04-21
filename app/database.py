from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import datetime
from configs import configs
app = FastAPI()

# MongoDB
MONGODB_URL = configs.MONGO_URL 
client = AsyncIOMotorClient(MONGODB_URL)
db = client["token"] 
async def get_db():
    yield db

# Collections
users_collection = db["users"]
tokens_collection = db["tokens"]
permanent_tokens_collection = db["permanentTokens"]

# 
models_collection = db['aiModels']