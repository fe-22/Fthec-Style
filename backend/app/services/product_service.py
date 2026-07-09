from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def list_products(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        max_price: Decimal | None = None,
        active_only: bool = True,
        in_stock_only: bool = False,
    ) -> list[Product]:
        stmt = select(Product)

        if active_only:
            stmt = stmt.where(Product.active.is_(True))
        if in_stock_only:
            stmt = stmt.where(Product.stock > 0)
        if category:
            stmt = stmt.where(Product.category.ilike(category.strip()))
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(term),
                    Product.description.ilike(term),
                    Product.category.ilike(term),
                    Product.sku.ilike(term),
                )
            )

        stmt = stmt.order_by(Product.active.desc(), Product.name.asc())
        return list(self.db.scalars(stmt).all())

    def get_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto nao encontrado.",
            )
        return product

    def get_product_by_sku(self, sku: str) -> Product | None:
        stmt: Select[tuple[Product]] = select(Product).where(Product.sku == sku)
        return self.db.scalar(stmt)

    def create_product(self, payload: ProductCreate) -> Product:
        if self.get_product_by_sku(payload.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ja existe um produto com este SKU.",
            )

        product = Product(**payload.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        changes = payload.model_dump(exclude_unset=True)

        for key in ("sizes", "colors", "tags", "style_keywords"):
            if key in changes and changes[key] is not None:
                changes[key] = [
                    item.strip().lower() for item in changes[key] if item.strip()
                ]

        for field, value in changes.items():
            setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product
