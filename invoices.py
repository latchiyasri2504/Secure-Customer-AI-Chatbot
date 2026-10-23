
from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Invoice
from app.services.auth_service import get_customer_from_token


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    invoice_date: date
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    payment_status: str = "unpaid"


router = APIRouter(prefix="/invoices", tags=["Invoices"])
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def list_my_invoices(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        customer = get_customer_from_token(
            db, credentials.credentials
        )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token."
        )

    if status and status not in ["paid", "unpaid"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be paid or unpaid."
        )

    query = select(Invoice).where(
        Invoice.customer_id == customer.id
    )

    if status:
        query = query.where(
            Invoice.payment_status == status
        )

    invoices = db.scalars(
        query.order_by(Invoice.id)
    ).all()

    return [
        {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": str(invoice.invoice_date),
            "amount": str(invoice.amount),
            "currency": invoice.currency,
            "payment_status": invoice.payment_status
        }
        for invoice in invoices
    ]


@router.post("/", status_code=201)
def create_invoice(
    data: InvoiceCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        customer = get_customer_from_token(
            db, credentials.credentials
        )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token."
        )

    if data.payment_status not in ["paid", "unpaid"]:
        raise HTTPException(
            status_code=400,
            detail="Payment status must be paid or unpaid."
        )

    existing_invoice = db.scalar(
        select(Invoice).where(
            Invoice.customer_id == customer.id,
            Invoice.invoice_number == data.invoice_number
        )
    )

    if existing_invoice:
        raise HTTPException(
            status_code=409,
            detail="Invoice number already exists."
        )

    invoice = Invoice(
        customer_id=customer.id,
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date,
        amount=data.amount,
        currency=data.currency,
        payment_status=data.payment_status
    )

    db.add(invoice)

    try:
        db.commit()
        db.refresh(invoice)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create invoice."
        )

    return {
        "message": "Invoice created successfully.",
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date),
        "amount": str(invoice.amount),
        "currency": invoice.currency,
        "payment_status": invoice.payment_status
    }
