from fastapi import APIRouter, status, Depends, Request
from fastapi.responses import StreamingResponse
from modules.chat import utils
from modules.chat import chatbot
from modules.chat import schemas
from modules.chat.graph import graph

chat_router = APIRouter()


@chat_router.post('/langgraph_adaptive_rag', status_code=status.HTTP_200_OK)
async def langgraph_adaptive_rag(data: schemas.Langgraph_adaptive_schema, request: Request):
    # Pass request in initial state
    result = graph.invoke({
        "question": data.question,
        "request": request
    })
    return result['generation']

def stream_response(data: schemas.Langgraph_adaptive_schema, request: Request):
    """
    Stream response for LangGraph Adaptive RAG
    """
    for message, metadata in graph.stream({"question": data.question, "request": request}, stream_mode="messages"):
        if metadata["langgraph_node"] == "generate":
            # Print the message
            # print(message)
            yield f"{message.content}"

        # for key, value in output.items():
        #     # Node
        #     print(f"Node '{key}':")
        #     # Optional: print full state at each node
        #     # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
        #     if key == 'generate':
        #         print(value)
        #         yield f"{value['generation']}\n\n"

@chat_router.post('/chat', status_code=status.HTTP_200_OK)
async def chat(data: schemas.Langgraph_adaptive_schema, request: Request):
    """
    Chat endpoint for LangGraph Adaptive RAG
    """
    return StreamingResponse(
        stream_response(data, request),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream"}
    )
