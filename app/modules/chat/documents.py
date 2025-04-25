from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from configs import configs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """A class to handle document processing, splitting and indexing operations."""

    def __init__(self):
        """Initialize the DocumentProcessor with default settings."""
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=configs.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=500,
            chunk_overlap=0
        )
        self.vectorstore = None
        self.retriever = None

    async def load_documents(self, urls: List[str]) -> List[Document]:
        """
        Load documents from given URLs.

        Args:
            urls: List of URLs to load documents from

        Returns:
            List of loaded documents
        """
        try:
            docs = [WebBaseLoader(url).load() for url in urls]
            return [item for sublist in docs for item in sublist]
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            raise

    async def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.

        Args:
            documents: List of documents to split

        Returns:
            List of split documents
        """
        try:
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            raise

    async def index_documents(self, documents: List[Document], collection_name: str = "rag-chroma") -> None:
        """
        Index documents into vector store.

        Args:
            documents: List of documents to index
            collection_name: Name of the collection to store vectors
        """
        try:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                collection_name=collection_name,
                embedding=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever()
            logger.info(f"Successfully indexed {len(documents)} documents")
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise

    async def process_urls(self, urls: List[str], collection_name: str = "rag-chroma") -> None:
        """
        Process URLs through the complete pipeline: load, split and index.

        Args:
            urls: List of URLs to process
            collection_name: Name of the collection to store vectors
        """
        docs = await self.load_documents(urls)
        split_docs = await self.split_documents(docs)
        await self.index_documents(split_docs, collection_name)

    def get_retriever(self):
        """Get the document retriever."""
        if self.retriever is None:
            raise ValueError("No documents have been indexed yet")
        return self.retriever

# Example usage:
# processor = DocumentProcessor()
# urls = [
#     "https://lilianweng.github.io/posts/2023-06-23-agent/",
#     "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
#     "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
# ]
# await processor.process_urls(urls)
# retriever = processor.get_retriever()
