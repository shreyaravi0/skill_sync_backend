from fastapi import APIRouter, HTTPException
from app.utils.firebase import db
from google.cloud.firestore import SERVER_TIMESTAMP

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_id(mentor: str, mentee: str):
    return f"{mentor}_{mentee}"


@router.post("/send")
def send_message(mentor: str, mentee: str, sender: str, text: str):

    chat_id = get_chat_id(mentor, mentee)

    # Chat document reference
    chat_ref = db.collection("chats").document(chat_id)

    # Create chat room automatically if missing
    chat_ref.set({
        "participants": [mentor, mentee],
        "last_updated": SERVER_TIMESTAMP
    }, merge=True)

    # Insert message
    chat_ref.collection("messages").add({
        "sender": sender,
        "text": text,
        "timestamp": SERVER_TIMESTAMP,
    })

    return {"message": "sent"}


@router.get("/history")
def get_history(mentor: str, mentee: str):
    chat_id = get_chat_id(mentor, mentee)

    msgs = (
        db.collection("chats")
        .document(chat_id)
        .collection("messages")
        .order_by("timestamp")
        .stream()
    )

    return [m.to_dict() for m in msgs]
