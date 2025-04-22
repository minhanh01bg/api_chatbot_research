from fastapi import APIRouter, status, Depends, Request
from modules.chat import utils
from modules.chat import chatbot
from modules.chat import schemas
from modules.chat.graph import graph

chat = APIRouter()


@chat.post('/langgraph_adaptive_rag', status_code=status.HTTP_200_OK)
async def langgraph_adaptive_rag(data: schemas.Langgraph_adaptive_schema, request: Request):
    # Pass request in initial state
    result = graph.invoke({
        "question": data.question,
        "request": request
    })
    return result['generation']
