from fastapi import UploadFile, HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from configs import configs
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from database import documents_collection, db
from datetime import datetime
from bson import ObjectId
import tempfile
import os
import numpy as np

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=configs.OPENAI_API_KEY
)

# Add new collection for embeddings
embeddings_collection = db['embeddings']


async def serialize_embeddings(embeddings_data):
    """Convert numpy arrays to lists for MongoDB storage"""
    serialized = []
    for item in embeddings_data:
        if isinstance(item['embedding'], np.ndarray):
            item['embedding'] = item['embedding'].tolist()
        serialized.append(item)
    return serialized


async def load_embeddings_from_mongodb():
    """Load embeddings from MongoDB and initialize vectorstore"""
    stored_embeddings = await embeddings_collection.find({}).to_list(length=None)

    if not stored_embeddings:
        return None

    # Prepare data for FAISS
    text_embeddings = []
    ids = []

    for doc in stored_embeddings:
        text = doc['document']['content']
        vector = np.array(doc['embedding'])
        text_embeddings.append((text, vector))
        ids.append(str(doc['_id']))

    # Initialize FAISS with stored embeddings
    vectorstore = FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=embeddings,
        ids=ids
    )
    print(f"Size of FAISS: {len(vectorstore.docstore._dict)}")
    return vectorstore


async def process_document(file: UploadFile) -> str:
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename[-5:]) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()

        # Choose loader based on file type
        if file.filename.endswith('.pdf'):
            loader = PyPDFLoader(temp_file.name)
        elif file.filename.endswith('.docx'):
            loader = Docx2txtLoader(temp_file.name)
        else:
            loader = TextLoader(temp_file.name)

        try:
            documents = loader.load()
        except Exception as e:
            os.unlink(temp_file.name)
            raise HTTPException(
                status_code=400,
                detail=f"Error processing document: {str(e)}"
            )

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        splits = text_splitter.split_documents(documents)

        # Cleanup temp file
        os.unlink(temp_file.name)

        return splits


async def add_to_vectorstore(documents, vectorstore, document_id: str, request) -> str:
    """Add documents to vectorstore and save embeddings to MongoDB"""
    # Generate embeddings
    texts = [doc.page_content for doc in documents]
    metadata = [doc.metadata for doc in documents]
    embedded_vectors = await embeddings.aembed_documents(texts)

    # Save to MongoDB and collect IDs
    embeddings_data = []
    inserted_ids = []

    for text, meta, vector in zip(texts, metadata, embedded_vectors):
        doc_data = {
            "document": {"content": text, "metadata": meta},
            "embedding": vector,
            "document_id": document_id,  # Add document reference
            "created_at": datetime.utcnow()
        }
        result = await embeddings_collection.insert_one(doc_data)
        inserted_ids.append(str(result.inserted_id))
        embeddings_data.append((text, vector))

    # Add to FAISS
    if vectorstore is not None:
        vectorstore.add_embeddings(
            text_embeddings=embeddings_data,
            ids=inserted_ids
        )
    else:
        vectorstore = FAISS.from_embeddings(
            text_embeddings=embeddings_data,
            embedding=embeddings,
            ids=inserted_ids
        )
        # Update app state with new vectorstore
        request.app.state.vectorstore = vectorstore

    num_docs = await embeddings_collection.count_documents({})
    print(f"Num docs in collection: {num_docs}")
    print(f'ids: ', inserted_ids)

    print(f'Size docs in FAISS: {len(vectorstore.docstore._dict)}')
    return f"faiss_collection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


async def search_documents(query: str, vectorstore, k: int = 4):
    """Search documents using loaded vectorstore"""
    if vectorstore is None:
        raise HTTPException(
            status_code=400,
            detail="No documents found in the database"
        )

    results = vectorstore.similarity_search(query, k=k)
    return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]


async def save_to_mongodb(metadata: dict) -> str:
    """Save document metadata to MongoDB"""
    metadata["created_at"] = datetime.utcnow()
    metadata["updated_at"] = datetime.utcnow()
    result = await documents_collection.insert_one(metadata)
    return str(result.inserted_id)


async def get_document_by_id(doc_id: str):
    """Get document metadata from MongoDB by ID"""
    try:
        document = await documents_collection.find_one({"_id": ObjectId(doc_id)})
        if document:
            document["_id"] = str(document["_id"])
            return document
        return None
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid document ID: {str(e)}")


async def update_document(doc_id: str, update_data: dict):
    """Update document metadata in MongoDB"""
    update_data["updated_at"] = datetime.utcnow()
    try:
        result = await documents_collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error updating document: {str(e)}")


async def delete_document(doc_id: str, request):
    """Delete document and its embeddings"""
    try:
        # Get document from MongoDB
        document = await get_document_by_id(doc_id)
        if document:
            # Delete from MongoDB collections
            await documents_collection.delete_one({"_id": ObjectId(doc_id)})

            # Find embeddings for this document
            embedding_docs = await embeddings_collection.find(
                {"document_id": doc_id}
            ).to_list(length=None)
            print(
                f"Found {len(embedding_docs)} embeddings for document ID {doc_id}")
            # Get vectorstore from app state
            vectorstore = request.app.state.vectorstore
            if vectorstore is not None and embedding_docs:
                # Delete from FAISS
                embedding_ids = [str(doc['_id']) for doc in embedding_docs]
                deleted = vectorstore.delete(ids=embedding_ids)
                print(f"Deleted {len(embedding_ids)} embeddings from FAISS")
                if deleted:
                    print(
                        f"Deleted {len(embedding_ids)} embeddings from vectorstore")

                # Update app state vectorstore
                request.app.state.vectorstore = vectorstore

            # Delete from MongoDB embeddings collection
            await embeddings_collection.delete_many({"document_id": doc_id})

            return True
        return False
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error deleting document: {str(e)}")


async def list_documents(skip: int = 0, limit: int = 10):
    """List documents with pagination"""
    cursor = documents_collection.find().skip(skip).limit(limit)
    documents = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        documents.append(doc)
    return documents


async def get_documents(skip: int = 0, limit: int = 10, search: str = None):
    """Get documents with pagination and optional search"""
    # Base query
    query = {}

    # Add search if provided
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]

    # Execute query with pagination
    cursor = documents_collection.find(query).skip(skip).limit(limit)
    total = await documents_collection.count_documents(query)

    # Get documents
    documents = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        documents.append(doc)

    return {
        "total": total,
        "documents": documents,
        "skip": skip,
        "limit": limit
    }


async def initialize_vectorstore():
    """Initialize vectorstore on startup"""
    stored_embeddings = await embeddings_collection.find({}).to_list(length=None)

    if not stored_embeddings:
        return None

    # Prepare data for FAISS
    text_embeddings = []
    ids = []

    for doc in stored_embeddings:
        text = doc['document']['content']
        vector = np.array(doc['embedding'])
        text_embeddings.append((text, vector))
        ids.append(str(doc['_id']))

    # Initialize FAISS with stored embeddings
    vectorstore = FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=embeddings,
        ids=ids
    )
    print(f"Size of FAISS: {len(vectorstore.docstore._dict)}")
    return vectorstore
