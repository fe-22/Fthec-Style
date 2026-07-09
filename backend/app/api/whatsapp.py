from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OrderCreate, WhatsAppCheckoutResponse
from app.services.order_service import OrderService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/checkout", response_model=WhatsAppCheckoutResponse, status_code=201)
def create_whatsapp_checkout(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> WhatsAppCheckoutResponse:
    whatsapp_service = WhatsAppService()
    order = OrderService(db).create_order(payload, whatsapp_service)
    return WhatsAppCheckoutResponse(
        order=order,
        message=order.whatsapp_message,
        wa_me_url=whatsapp_service.build_checkout_url(order.whatsapp_message),
    )
