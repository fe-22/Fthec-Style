from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_categories(self) -> list[str]:
        stmt = (
            select(Product.category)
            .where(Product.active.is_(True))
            .distinct()
            .order_by(Product.category.asc())
        )
        return list(self.db.scalars(stmt).all())
