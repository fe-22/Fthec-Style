from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.admin_auth import require_admin_session
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_IMAGE_BYTES = 6 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@router.post("/products", status_code=201)
async def upload_product_image(
    request: Request,
    filename: str = "product.png",
    _admin: None = Depends(require_admin_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    body = await request.body()
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio.",
        )
    if len(body) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Imagem muito grande. Limite de 6 MB.",
        )

    content_type = request.headers.get("content-type", "").split(";")[0].lower()
    suffix = Path(filename).suffix.lower()
    if content_type in CONTENT_TYPE_EXTENSIONS:
        suffix = CONTENT_TYPE_EXTENSIONS[content_type]
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Use imagem JPG, PNG ou WebP.",
        )

    product_upload_dir = Path(settings.upload_root) / "products"
    product_upload_dir.mkdir(parents=True, exist_ok=True)
    image_name = f"{uuid4().hex}{suffix}"
    image_path = product_upload_dir / image_name
    image_path.write_bytes(body)

    return {"image_url": f"/uploads/products/{image_name}"}
