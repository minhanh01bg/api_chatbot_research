from fastapi import APIRouter, status, UploadFile, File, Form, Request, HTTPException
from modules.document import schemas, utils
from typing import List
from database import documents_collection

document = APIRouter()


@document.post("/add", status_code=status.HTTP_200_OK)
async def add_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    tags: List[str] = Form(None),
    request: Request = None
):
    # Save metadata first to get document ID
    doc_metadata = {
        "title": title,
        "description": description,
        "tags": tags,
        "filename": file.filename
    }
    document_id = await utils.save_to_mongodb(doc_metadata)

    # Process document and add to vectorstore
    doc_content = await utils.process_document(file)

    # Add to vectorstore with document ID reference
    vectorstore = request.app.state.vectorstore
    vectorstore_id = await utils.add_to_vectorstore(doc_content, vectorstore, document_id, request)

    # Update document metadata with vectorstore ID
    await utils.update_document(document_id, {"vectorstore_id": vectorstore_id})

    return {
        "message": "Document added successfully",
        "document_id": document_id
    }


@document.get("/search", status_code=status.HTTP_200_OK)
async def search_documents(query: schemas.DocumentSearchSchema):
    results = await utils.search_documents(query.search_text)
    return results


@document.delete("/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document(doc_id: str, request: Request):
    result = await utils.delete_document(doc_id, request)
    if result:
        return {"message": "Document and related embeddings deleted successfully"}
    raise HTTPException(status_code=404, detail="Document not found")


@document.get("/documents", status_code=status.HTTP_200_OK)
async def get_documents(
    skip: int = 0,
    limit: int = 10,
    search: str = None
):
    """
    Get list of documents with pagination and optional search
    """
    return await utils.get_documents(skip=skip, limit=limit, search=search)
