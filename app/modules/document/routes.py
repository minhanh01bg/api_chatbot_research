from fastapi import APIRouter, status, UploadFile, File, Form, Request
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
    # Process document and add to vectorstore
    doc_content = await utils.process_document(file)

    # Add to vectorstore
    vectorstore = request.app.state.vectorstore
    vectorstore_id = await utils.add_to_vectorstore(doc_content, vectorstore)
    print(f"Vectorstore ID: {vectorstore_id}")
    # Save metadata to MongoDB
    doc_metadata = {
        "title": title,
        "description": description,
        "tags": tags,
        "vectorstore_id": vectorstore_id,
        "filename": file.filename
    }

    document_id = await utils.save_to_mongodb(doc_metadata)

    return {
        "message": "Document added successfully",
        "document_id": document_id
    }


@document.get("/search", status_code=status.HTTP_200_OK)
async def search_documents(query: schemas.DocumentSearchSchema):
    results = await utils.search_documents(query.search_text)
    return results
