
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.auth_service import request_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str


@router.post("/request-otp")
def send_otp(data: OTPRequest, db: Session = Depends(get_db)):
    try:
        message = request_otp(db, data.phone)
        return {"message": message}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/verify-otp")
def check_otp(data: OTPVerify, db: Session = Depends(get_db)):
    try:
        token = verify_otp(db, data.phone, data.otp)
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
