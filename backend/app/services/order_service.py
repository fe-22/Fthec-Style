from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Customer, Order, OrderItem, Product
from app.schemas import OrderCreate
from app.services.customer_service import CustomerService
from app.services.whatsapp_service import WhatsAppService


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_service = CustomerService(db)

    def create_order(
        self,
        payload: OrderCreate,
        whatsapp_service: WhatsAppService,
    ) -> Order:
        customer = self._resolve_customer(payload)
        order = Order(customer_id=customer.id if customer else None)
        self.db.add(order)
        self.db.flush()

        subtotal = Decimal("0.00")
        order_items: list[OrderItem] = []

        for item_payload in payload.items:
            product = self._get_available_product(item_payload.product_id)
            self._validate_variant(product, item_payload.size, item_payload.color)

            line_total = product.price * item_payload.quantity
            subtotal += line_total

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_payload.quantity,
                unit_price=product.price,
                size=item_payload.size,
                color=item_payload.color,
            )
            order_item.product = product
            order_items.append(order_item)
            self.db.add(order_item)

        order.subtotal = subtotal
        order.items = order_items
        order.whatsapp_message = whatsapp_service.build_checkout_message(
            order=order,
            customer=customer,
            notes=payload.notes,
        )

        self.db.commit()
        return self.get_order(order.id)

    def get_order(self, order_id: int) -> Order:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )
        order = self.db.scalar(stmt)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido nao encontrado.",
            )
        return order

    def _resolve_customer(self, payload: OrderCreate) -> Customer | None:
        if payload.customer_id:
            return self.customer_service.get_customer(payload.customer_id)
        if payload.customer:
            return self.customer_service.create_or_update(payload.customer)
        return None

    def _get_available_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product or not product.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto {product_id} nao encontrado ou inativo.",
            )
        if product.stock <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Produto {product.name} esta sem estoque.",
            )
        return product

    def _validate_variant(
        self,
        product: Product,
        size: str | None,
        color: str | None,
    ) -> None:
        if size and product.sizes and size.strip().lower() not in product.sizes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tamanho {size} indisponivel para {product.name}.",
            )
        if color and product.colors and color.strip().lower() not in product.colors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cor {color} indisponivel para {product.name}.",
            )
