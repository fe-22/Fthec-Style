from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer
from app.schemas import CustomerCreate


def normalize_phone(phone: str) -> str:
    return "".join(character for character in phone if character.isdigit())


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.db.get(Customer, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente nao encontrado.",
            )
        return customer

    def get_by_phone(self, phone: str) -> Customer | None:
        normalized_phone = normalize_phone(phone)
        stmt = select(Customer).where(Customer.phone == normalized_phone)
        return self.db.scalar(stmt)

    def create_or_update(self, payload: CustomerCreate) -> Customer:
        normalized_phone = normalize_phone(payload.phone)
        customer = self.get_by_phone(normalized_phone)

        if customer:
            customer.name = payload.name
            customer.email = str(payload.email) if payload.email else None
            customer.style_notes = payload.style_notes
        else:
            customer = Customer(
                name=payload.name,
                phone=normalized_phone,
                email=str(payload.email) if payload.email else None,
                style_notes=payload.style_notes,
            )
            self.db.add(customer)

        self.db.commit()
        self.db.refresh(customer)
        return customer
