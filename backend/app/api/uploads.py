from pathlib import Path
import re
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.admin_auth import require_admin_session
from app.core.config import Settings, get_settings
from app.database import get_db
from app.models import Product

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_ERP_REPORT_BYTES = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_ERP_REPORT_EXTENSIONS = {".csv", ".pdf", ".xls", ".xlsx", ".txt"}
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


@router.post("/erp-report", status_code=201)
async def upload_erp_report(
    request: Request,
    filename: str = "relatorio-erp.pdf",
    _admin: None = Depends(require_admin_session),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    body = await request.body()
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio.",
        )
    if len(body) > MAX_ERP_REPORT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Relatorio muito grande. Limite de 100 MB.",
        )

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_ERP_REPORT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Use relatorio PDF, CSV, XLS, XLSX ou TXT.",
        )

    report_upload_dir = Path(settings.upload_root) / "erp-reports"
    report_upload_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = Path(filename).stem[:80].replace(" ", "-")
    report_name = f"{uuid4().hex}-{safe_stem}{suffix}"
    report_path = report_upload_dir / report_name
    report_path.write_bytes(body)

    extracted_text_name = ""
    extracted_text_chars = 0
    imported_products = 0
    updated_products = 0
    if suffix == ".pdf":
        extracted_text = extract_pdf_text(body)
        extracted_text_chars = len(extracted_text)
        extracted_text_name = f"{report_path.stem}.txt"
        (report_upload_dir / extracted_text_name).write_text(
            extracted_text,
            encoding="utf-8",
        )
        product_image_urls = extract_pdf_product_images(body, Path(settings.upload_root) / "products")
        import_result = import_erp_products_from_text(db, extracted_text, product_image_urls)
        imported_products = import_result["created"]
        updated_products = import_result["updated"]
        imported_images = import_result["images"]
    else:
        imported_images = 0

    return {
        "filename": report_name,
        "original_filename": filename,
        "size_bytes": len(body),
        "report_url": f"/uploads/erp-reports/{report_name}",
        "extracted_text_filename": extracted_text_name,
        "extracted_text_chars": extracted_text_chars,
        "imported_products": imported_products,
        "updated_products": updated_products,
        "imported_images": imported_images,
    }


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyMuPDF nao esta instalado. Instale a dependencia PyMuPDF.",
        ) from exc

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            return "\n\n".join(page.get_text().strip() for page in pdf).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel ler o PDF enviado.",
        ) from exc


def extract_pdf_product_images(pdf_bytes: bytes, product_upload_dir: Path) -> list[str]:
    try:
        import fitz
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyMuPDF nao esta instalado. Instale a dependencia PyMuPDF.",
        ) from exc

    product_upload_dir.mkdir(parents=True, exist_ok=True)
    image_urls: list[str] = []

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            for page_number, page in enumerate(pdf, start=1):
                page_images = page.get_images(full=True)
                if not page_images:
                    image_urls.append("")
                    continue

                best_image = max(
                    page_images,
                    key=lambda image: int(image[2] or 0) * int(image[3] or 0),
                )
                image_data = pdf.extract_image(best_image[0])
                image_bytes = image_data.get("image", b"")
                extension = image_data.get("ext", "png").lower()
                if not image_bytes:
                    image_urls.append("")
                    continue

                image_name = f"{uuid4().hex}-erp-page-{page_number}.{extension}"
                image_path = product_upload_dir / image_name
                image_path.write_bytes(image_bytes)
                image_urls.append(f"/uploads/products/{image_name}")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel extrair as fotos do PDF enviado.",
        ) from exc

    return image_urls


def import_erp_products_from_text(
    db: Session,
    text: str,
    image_urls: list[str] | None = None,
) -> dict[str, int]:
    products = parse_erp_products(text, image_urls=image_urls)
    created = 0
    updated = 0
    images = 0

    for product_data in products:
        product = db.query(Product).filter(Product.sku == product_data["sku"]).first()
        image_url = product_data.get("image_url")
        if image_url:
            images += 1

        if product:
            for field, value in product_data.items():
                if field == "sku":
                    continue
                if field == "image_url" and not value:
                    continue
                setattr(product, field, value)
            updated += 1
        else:
            db.add(Product(**product_data))
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "images": images}


def parse_erp_products(text: str, image_urls: list[str] | None = None) -> list[dict]:
    blocks = re.split(r"(?=FTHEC ERP\s+Enterprise)", text)
    products = []

    for block in blocks:
        if "Descricao *" not in block or "Preco de Venda (R$) *" not in block:
            continue

        ean = get_erp_value(block, "Codigo de Barras (EAN)")
        code = get_erp_value(block, "Codigo *")
        name = get_erp_value(block, "Descricao *")
        if not name:
            continue

        sku = normalize_sku(ean or code or name)
        price = parse_brl(get_erp_value(block, "Preco de Venda (R$) *"))
        if not sku or price <= 0:
            continue

        full_description = clean_erp_value(get_erp_value(block, "Descricao Completa"))
        stock = parse_int(get_erp_value(block, "Estoque Atual"))
        category = clean_erp_value(get_erp_value(block, "Categoria *"))
        if not category:
            category = infer_category(name)

        situation = clean_erp_value(get_erp_value(block, "Situacao")).lower()
        colors = extract_colors(
            clean_erp_value(get_erp_value(block, "Cor *")),
            full_description,
        )
        sizes = extract_sizes(
            clean_erp_value(get_erp_value(block, "Tamanho *")),
            full_description,
        )

        product_index = len(products)
        image_url = image_urls[product_index] if image_urls and product_index < len(image_urls) else ""
        products.append(
            {
                "sku": sku,
                "name": name.strip(),
                "description": full_description or name.strip(),
                "category": category,
                "purchase_price": parse_brl(get_erp_value(block, "Preco de Custo (R$) *")),
                "price": price,
                "stock": stock,
                "image_url": image_url,
                "sizes": sizes,
                "colors": colors,
                "tags": ["erp"],
                "style_keywords": [],
                "active": situation != "inativo" and stock > 0,
            }
        )

    return products


def get_erp_value(block: str, label: str) -> str:
    lines = [line.strip() for line in block.splitlines()]
    for index, line in enumerate(lines):
        if line == label:
            for next_line in lines[index + 1 :]:
                if next_line:
                    return next_line
    return ""


def clean_erp_value(value: str) -> str:
    value = value.strip()
    if not value or value.lower() == "nao informado":
        return ""
    return value


def parse_brl(value: str) -> Decimal:
    value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return Decimal(value or "0")
    except InvalidOperation:
        return Decimal("0")


def parse_int(value: str) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


def normalize_sku(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "-", value.strip()).strip("-").upper()[:80]


def infer_category(name: str) -> str:
    normalized = normalize_text(name)
    category_terms = {
        "blazer": "blazer",
        "vestido": "vestido",
        "camisa": "camisa",
        "calca": "calca",
        "blusa": "blusa",
        "casaco": "casaco",
        "conjunto": "conjunto",
        "pijama": "pijama",
        "cashmere": "cashmere",
        "top": "top",
    }
    for term, category in category_terms.items():
        if term in normalized:
            return category
    return "produto"


def normalize_text(value: str) -> str:
    replacements = str.maketrans("áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")
    return value.translate(replacements).lower()


def extract_colors(color_value: str, description: str) -> list[str]:
    candidates: list[str] = []
    if color_value and "grade com" not in color_value.lower():
        candidates.extend(re.split(r"[,/]", color_value))

    for segment in description.split("|"):
        first_part = segment.split(":")[0].strip()
        if "/" in first_part:
            candidates.append(first_part.rsplit("/", 1)[0])

    return unique_clean_terms(candidates, max_items=8)


def extract_sizes(size_value: str, description: str) -> list[str]:
    candidates: list[str] = []
    if size_value and "grade com" not in size_value.lower():
        candidates.extend(re.split(r"[,/]", size_value))

    for segment in description.split("|"):
        size_match = re.search(r"(?:/|\s)(pp|p|m|g|gg|u|unico|único|[0-9]{2})\s*:", segment, re.IGNORECASE)
        if size_match:
            candidates.append(size_match.group(1))
            continue

        start_match = re.match(r"\s*(pp|p|m|g|gg|u|unico|único|[0-9]{2})\s*:", segment, re.IGNORECASE)
        if start_match:
            candidates.append(start_match.group(1))

    return unique_clean_terms(candidates, max_items=12)


def unique_clean_terms(values: list[str], max_items: int) -> list[str]:
    terms = []
    seen = set()
    for value in values:
        term = clean_erp_value(value).strip().lower()
        if not term:
            continue
        term = term.replace("ú", "u")
        if term not in seen:
            terms.append(term)
            seen.add(term)
        if len(terms) >= max_items:
            break
    return terms
