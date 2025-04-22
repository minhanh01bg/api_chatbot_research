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


