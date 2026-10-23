
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Conversation, Message
from app.services.auth_service import get_customer_from_token

router = APIRouter(prefix="/conversations", tags=["Messages"])
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_customer(credentials, db):
    try:
        return get_customer_from_token(
            db, credentials.credentials
        )
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))


class MessageCreate(BaseModel):
    content: str


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    data: MessageCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    customer = get_customer(credentials, db)

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_id == customer.id
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.content
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at
    }


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    customer = get_customer(credentials, db)

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_id == customer.id
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
    ).all()

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at
        }
        for message in messages
    ]
