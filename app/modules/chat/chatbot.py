# from modules.chat.documents import retriever
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from configs import configs
# Data model


class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "web_search"] = Field(
        ...,
        description="Given a user question choose to route it to web search or a vectorstore.",
    )


# LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY)

structured_llm_router = llm.with_structured_output(RouteQuery)

# Prompt
system = """You are an expert at routing a user question to a vectorstore or web search.
The vectorstore contains documents related to agents, prompt engineering, adversarial attacks and WorldReader (Trợ lý hỗ trợ mua bán sách).
Use the vectorstore for questions on these topics. Otherwise, use web-search."""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router

# In[]: test question_router
# print(
#     question_router.invoke(
#         {"question": "Who will the Bears draft first in the NFL draft?"}
#     )
# )
# print(question_router.invoke({"question": "What is the best way to build a LangChain agent?"}))

# In[]: Docs relevant?

# Retrieval Grader

# Data model
class GradeDocument(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY)

structured_llm_grader = llm.with_structured_output(GradeDocument)

# Prompt
system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Retrieved document: \n\n {document} \n\n User question: {question}"
        ),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
# In[]: test
# question = "agent memory"

# docs = retriever.invoke(question)
# doc_txt = docs[1].page_content

# print(retrieval_grader.invoke({"question": question, "document": doc_txt}))

# In[] Generate
from langchain import hub
from langchain_core.output_parsers import StrOutputParser

# Prompt
prompt = hub.pull('rlm/rag-prompt')

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY)

# Post-processing
def format_docs(docs):
    """Format documents for display."""
    return "\n\n".join([doc.page_content for doc in docs])

# chain
rag_chain = prompt | llm | StrOutputParser()

# run 
# generation = rag_chain.invoke({"context": docs, "question": question})
# print(generation)

# In[] Hallucination Grader

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY)

structured_llm_grader = llm.with_structured_output(GradeHallucinations)

# Prompt
system = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)

hallucination_grader = hallucination_prompt | structured_llm_grader
# print(hallucination_grader.invoke({"documents": docs, "generation": generation}))

# In[]: Answer Grader
# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# LLM with function call
llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY, temperature=0)
structured_llm_grader = llm.with_structured_output(GradeAnswer)

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n 
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""

answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_prompt | structured_llm_grader
# print(answer_grader.invoke({"question": question, "generation": generation}))
# In[] Question Re-writer

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=configs.OPENAI_API_KEY, temperature=0)

# Prompt
system = """You a question re-writer that converts an input question to a better version that is optimized \n 
     for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()
# print(question_rewriter.invoke({"question": question}))

# In[] web search tool
from langchain_community.tools.tavily_search import TavilySearchResults
import os
os.environ['TAVILY_API_KEY'] = configs.TAVILY_KEY
web_search_tool = TavilySearchResults(k=3)
