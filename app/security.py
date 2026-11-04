import secrets

from fastapi import Header, HTTPException

from app.config import settings


async def require_token(
    authorization: str | None = Header(default=None)
):
    expected = settings.jarvis_api_token

    if not expected or expected == "change-me":
        raise HTTPException(
            status_code=503,
            detail="JARVIS_API_TOKEN ayarlanmamış."
        )

    supplied = ""

    if authorization and authorization.startswith("Bearer "):
        supplied = authorization[7:].strip()

    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Geçersiz API anahtarı."
        )
