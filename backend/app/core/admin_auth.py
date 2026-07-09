import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings


ADMIN_SESSION_MAX_AGE_SECONDS = 8 * 60 * 60


def _sign(value: str, settings: Settings) -> str:
    secret = settings.admin_session_secret or settings.admin_password
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_admin_session(settings: Settings) -> str:
    issued_at = int(time.time())
    nonce = secrets.token_urlsafe(24)
    payload = f"{issued_at}:{nonce}"
    return f"{payload}:{_sign(payload, settings)}"


def verify_admin_password(password: str, settings: Settings) -> bool:
    if not settings.admin_password:
        return False
    return hmac.compare_digest(password, settings.admin_password)


def is_admin_session_valid(request: Request, settings: Settings) -> bool:
    if not settings.admin_password:
        return False

    token = request.cookies.get(settings.admin_session_cookie_name)
    if not token:
        return False

    try:
        issued_at_text, nonce, signature = token.split(":", 2)
        issued_at = int(issued_at_text)
    except ValueError:
        return False

    if time.time() - issued_at > ADMIN_SESSION_MAX_AGE_SECONDS:
        return False

    payload = f"{issued_at}:{nonce}"
    expected_signature = _sign(payload, settings)
    return hmac.compare_digest(signature, expected_signature)


def require_admin_session(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    if is_admin_session_valid(request, settings):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acesso administrativo nao autorizado.",
    )
