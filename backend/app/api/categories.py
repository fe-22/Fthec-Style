from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[str])
def list_categories(db: Session = Depends(get_db)) -> list[str]:
    return CategoryService(db).list_categories()
