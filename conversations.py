
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Conversation
from app.services.auth_service import get_customer_from_token

router = APIRouter(prefix="/conversations", tags=["Conversations"])
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_logged_in_customer(
    credentials: HTTPAuthorizationCredentials,
    db: Session
):
    try:
        return get_customer_from_token(
            db, credentials.credentials
        )
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


@router.post("/")
def create_conversation(
    data: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    customer = get_logged_in_customer(credentials, db)

    conversation = Conversation(
        customer_id=customer.id,
        title=data.title
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at
    }


@router.get("/")
def list_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    customer = get_logged_in_customer(credentials, db)

    conversations = db.scalars(
        select(Conversation)
        .where(Conversation.customer_id == customer.id)
        .order_by(Conversation.id.desc())
    ).all()

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at
        }
        for conversation in conversations
    ]
