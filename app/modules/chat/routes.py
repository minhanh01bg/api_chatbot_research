from fastapi import APIRouter, status, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from modules.chat import utils
from modules.chat import chatbot
from modules.chat import schemas
from modules.chat.graph import graph
from modules.chat import service
chat_router = APIRouter()


@chat_router.post('/langgraph_adaptive_rag', status_code=status.HTTP_200_OK)
async def langgraph_adaptive_rag(data: schemas.Langgraph_adaptive_schema, request: Request):
    # Pass request in initial state
    result = graph.invoke({
        "question": data.question,
        "request": request
    })
    return result['generation']

def stream_response(data: schemas.Langgraph_adaptive_schema, request: Request, background_tasks: BackgroundTasks):
    """
    Stream response for LangGraph Adaptive RAG
    """
    answers = ""
    for message, metadata in graph.stream({"question": data.question, "request": request}, stream_mode="messages"):
        if metadata["langgraph_node"] == "generate":
            answers += message.content
            yield f"{message.content}"

    background_tasks.add_task(service.save_question, "assistant", answers, data.session_id)

@chat_router.post('/chat', status_code=status.HTTP_200_OK)
async def chat(data: schemas.Langgraph_adaptive_schema, request: Request, background_tasks: BackgroundTasks):
    """
    Chat endpoint for LangGraph Adaptive RAG
    """
    await service.save_question("user", data.question, data.session_id)
    return StreamingResponse(
        stream_response(data, request, background_tasks=background_tasks),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
    )

@chat_router.get('/chat_sessions', status_code=status.HTTP_200_OK)
async def get_chat_sessions(
    page: int = 1,
    page_size: int = 10,
) -> schemas.SessionResponse:
    """
    Get chat sessions with pagination
    """
    return await service.get_sessions(page=page, page_size=page_size)

@chat_router.get('/chat_history', status_code=status.HTTP_200_OK)
async def get_chat_history(
    session_id: str,
) -> schemas.ChatHistoryResponse:
    """
    Get chat history for a specific session with pagination
    """
    return await service.get_chat_history(session_id=session_id,)