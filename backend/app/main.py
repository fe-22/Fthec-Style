from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import categories, customers, orders, products, stylist, uploads, whatsapp
from app.core.admin_auth import (
    ADMIN_SESSION_MAX_AGE_SECONDS,
    create_admin_session,
    is_admin_session_valid,
    verify_admin_password,
)
from app.core.config import get_settings
from app.database import SessionLocal, init_database
from app.seed import seed_demo_products


settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = Path(settings.upload_root)


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


def frontend_file(filename: str) -> FileResponse:
    response = FileResponse(FRONTEND_DIR / filename)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_products(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix=settings.api_prefix)
app.include_router(categories.router, prefix=settings.api_prefix)
app.include_router(customers.router, prefix=settings.api_prefix)
app.include_router(orders.router, prefix=settings.api_prefix)
app.include_router(whatsapp.router, prefix=settings.api_prefix)
app.include_router(stylist.router, prefix=settings.api_prefix)
app.include_router(uploads.router, prefix=settings.api_prefix)

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", NoCacheStaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/", include_in_schema=False)
def storefront() -> FileResponse:
    return frontend_file("index.html")


@app.get("/admin", include_in_schema=False)
def admin_panel(request: Request) -> FileResponse:
    if not is_admin_session_valid(request, settings):
        return frontend_file("admin-login.html")

    return frontend_file("admin.html")


@app.post("/admin/login", include_in_schema=False)
async def admin_login(request: Request) -> RedirectResponse:
    body = await request.body()
    form = parse_qs(body.decode("utf-8"))
    password = form.get("password", [""])[0]

    if not verify_admin_password(password, settings):
        return RedirectResponse(
            "/admin?error=1",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    response = RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.admin_session_cookie_name,
        value=create_admin_session(settings),
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/admin/logout", include_in_schema=False)
def admin_logout() -> RedirectResponse:
    response = RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.admin_session_cookie_name)
    return response
