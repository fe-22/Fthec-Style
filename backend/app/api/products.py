from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.admin_auth import is_admin_session_valid, require_admin_session
from app.core.config import Settings, get_settings
from app.database import get_db
from app.schemas import ProductAdminRead, ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    request: Request,
    search: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = None,
    active_only: bool = True,
    in_stock_only: bool = False,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[ProductRead]:
    if not active_only and not is_admin_session_valid(request, settings):
        require_admin_session(request, settings)

    return ProductService(db).list_products(
        search=search,
        category=category,
        max_price=max_price,
        active_only=active_only,
        in_stock_only=in_stock_only,
    )


@router.get("/admin", response_model=list[ProductAdminRead])
def list_products_admin(
    search: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = None,
    active_only: bool = False,
    in_stock_only: bool = False,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin_session),
) -> list[ProductAdminRead]:
    return ProductService(db).list_products(
        search=search,
        category=category,
        max_price=max_price,
        active_only=active_only,
        in_stock_only=in_stock_only,
    )


@router.post("", response_model=ProductAdminRead, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin_session),
) -> ProductAdminRead:
    return ProductService(db).create_product(payload)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProductRead:
    product = ProductService(db).get_product(product_id)
    if not product.active and not is_admin_session_valid(request, settings):
        require_admin_session(request, settings)

    return product


@router.patch("/{product_id}", response_model=ProductAdminRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin_session),
) -> ProductAdminRead:
    return ProductService(db).update_product(product_id, payload)
