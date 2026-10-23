
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.routers.auth import get_db
from app.services.auth_service import get_customer_from_token

router = APIRouter(prefix="/customers", tags=["Customers"])
security = HTTPBearer()


@router.get("/me")
def get_my_details(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        customer = get_customer_from_token(
            db, credentials.credentials
        )
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone
        }
    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error)
        )
