from fastapi import APIRouter, status
from modules.chat import utils

chat = APIRouter()

@chat.post('/test', status_code=status.HTTP_200_OK)
async def test(prompt: str = "how many emails did i get in the last 5 days?"):
    from modules.chat.utils import google_styler, cosine_similarity
    result =  google_styler.invoke({"messages": [("user", prompt)]})
    print(result)
    return cosine_similarity(result.teacher_style, result.student_style)
