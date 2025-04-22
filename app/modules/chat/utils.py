# from modules.score.config import Config
# Config()
from IPython.display import Image, display
from configs import configs
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import numpy as np
from langchain_openai import OpenAIEmbeddings
from typing import Annotated, Literal, Sequence, Dict, List
from typing_extensions import TypedDict

from langchain import hub
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, MessagesPlaceholder, ChatPromptTemplate
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_openai import ChatOpenAI
import os
from langchain.agents import tool

# In[]
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, create_react_agent
from langgraph.types import Command
# ChatOpenAI.model_rebuild()
openai_llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY)
openai_embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small", api_key=configs.OPENAI_API_KEY)

google_embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07", google_api_key=configs.GOOGLE_API_KEY)  # gemini-embedding-exp-03-07, text-embedding-004, embedding-001

google_llm = ChatGoogleGenerativeAI(
    model=configs.GENMINI_MODEL, api_key=configs.GOOGLE_API_KEY)


# @tool
def cosine_similarity(teacher_text: str, student_text: str) -> float:
    """Calculate cosine similarity for two text embeddings"""
    embedding1 = openai_embeddings_model.embed_query(teacher_text)
    embedding2 = openai_embeddings_model.embed_query(student_text)

    print(f"Length of embedding1: {len(embedding1)}")
    print(f"Length of embedding2: {len(embedding2)}")

    dot_product = np.dot(embedding1, embedding2)
    norm_vec1 = np.linalg.norm(embedding1)
    norm_vec2 = np.linalg.norm(embedding2)

    cosine_sim = dot_product / (norm_vec1 * norm_vec2)
    return cosine_sim


# @tool
# def make_style_prompt(style: str) -> str:
#     """Find or Extract style from the text"""
#     return style


# tools = [cosine_similarity,]


# def call_tools(msg: AIMessage) -> List[Dict]:
#     """Simple sequential tool calling helper."""
#     tool_map = {tool.name: tool for tool in tools}
#     tool_calls = msg.tool_calls.copy()
#     for tool_call in tool_calls:
#         tool_call["output"] = tool_map[tool_call["name"]].invoke(
#             tool_call["args"])
#     return tool_calls

class StyleExcute(BaseModel):
    """Class to hold the structured output of the style comparison."""
    teacher_style: str = Field(description="style of teacher prompt")
    student_style: str = Field(description="style of student prompt")


style_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                " You can only extract stylistic features from each input prompt."
                " Focus exclusively on style-related elements such as:"
                " Tone, mood, word choice, level of description, sentence structure, imagery, and narrative voice."
                " Identify the stylistic features of each prompt clearly and separately."
                " Do not compare the prompts. Only return the style features of each one individually."
                " Use the format:\nStyle of Prompt 1:\n- ...\nStyle of Prompt 2:\n- ..."
            )
        ),
        ("placeholder", "{messages}")
    ]
)

google_styler = style_prompt | ChatGoogleGenerativeAI(
    model=configs.GENMINI_MODEL, api_key=configs.GOOGLE_API_KEY).with_structured_output(StyleExcute)
openai_styler = style_prompt | ChatOpenAI(
    model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY).with_structured_output(StyleExcute)
