from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OrderCreate, OrderRead
from app.services.order_service import OrderService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderRead:
    return OrderService(db).create_order(payload, WhatsAppService())


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> OrderRead:
    return OrderService(db).get_order(order_id)
