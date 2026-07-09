from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CustomerCreate, CustomerRead
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_or_update_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
) -> CustomerRead:
    return CustomerService(db).create_or_update(payload)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
) -> CustomerRead:
    return CustomerService(db).get_customer(customer_id)
