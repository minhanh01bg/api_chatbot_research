from fastapi import APIRouter, status, Depends
from modules.chat import utils
from modules.chat import chatbot
from modules.chat import schemas
from modules.chat.graph import graph
chat = APIRouter()


@chat.post('/test', status_code=status.HTTP_200_OK)
async def test(prompt: str = "how many emails did i get in the last 5 days?"):
    from modules.chat.utils import google_styler, cosine_similarity
    result = google_styler.invoke({"messages": [("user", prompt)]})
    print(result)
    return cosine_similarity(result.teacher_style, result.student_style)

@chat.post('/langgraph_adaptive_rag', status_code=status.HTTP_200_OK)
async def langgraph_adaptive_rag(data: schemas.Langgraph_adaptive_schema):
    question = data.question
    return graph.invoke({"question": question})