
from .schemas import MessageBase, ChatSession, ChatHistoryResponse, SessionResponse, SessionData
from database import chat_sessions_collection
from datetime import datetime
from fastapi import Depends, HTTPException, Query, Response

async def save_question(
    role: str,
    question: str,
    chat_session: str,
    # site_id: str,
) -> MessageBase:
    message = MessageBase(
        role=role,
        content=question
    )

    db_chat_session = await chat_sessions_collection.find_one({"session_id": chat_session})

    if not db_chat_session:
        new_session = ChatSession(
            session_id=chat_session,
            messages=[message]
        )
        await chat_sessions_collection.insert_one(new_session.dict())
    else:
        await chat_sessions_collection.update_one(
            {"session_id": chat_session},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_time": datetime.utcnow()}
            }
        )
    return message


async def get_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> SessionResponse:
    skip = (page - 1) * page_size
    total_records = await chat_sessions_collection.count_documents({})

    cursor = chat_sessions_collection.find().sort(
        "created_time", -1).skip(skip).limit(page_size)
    sessions = await cursor.to_list(length=page_size)

    session_list = []
    for session in sessions:
        user_messages = [msg for msg in session.get(
            "messages", []) if msg["role"] == "user"]

        # Convert MongoDB _id to string and create session data
        session_dict = {
            # Ensure _id is properly converted to string
            "_id": str(session["_id"]),
            "session_id": session["session_id"],
            "created_time": session["created_time"],
            "updated_time": session["updated_time"],
            # "messages": [MessageBase(**msg).dict() for msg in session.get("messages", [])],
            "first_question": user_messages[0]["content"] if user_messages else None,
            "question_count": len(user_messages)
        }
        # session_data = SessionData(**session_dict)
        session_list.append(session_dict)

    total_pages = (total_records + page_size -
                   1) // page_size if total_records > 0 else 1

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": total_pages,
        "data": session_list
    }


async def get_chat_history(
    session_id: str,
) -> ChatHistoryResponse:
    session = await chat_sessions_collection.find_one({"session_id": session_id})
    if not session:
        return {
            "session_id": session_id,
            "data": []
        }

    messages = [MessageBase(**msg) for msg in session.get("messages", [])]
    total_records = len(messages)

    return {
        "session_id": session_id,
        "data": messages
    }


async def delete_session(session_id: str, site_id: str):
    # Kiểm tra xem session có tồn tại không
    db_session = await chat_sessions_collection.find_one({"session_id": session_id, "site_id": site_id})
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Xóa ChatSession
    await chat_sessions_collection.delete_one({"session_id": session_id, "site_id": site_id})

    # Xóa tất cả ChatHistory liên quan
    # await chat_histories_collection.delete_many({"session_id": session_id, "site_id": site_id})

    return {"message": f"Session {session_id} and its histories deleted successfully"}