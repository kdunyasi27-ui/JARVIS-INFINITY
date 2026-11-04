import secrets

from fastapi import Header, HTTPException

from app.config import settings


async def require_token(authorization: str | None = Header(default=None)):
    expected = settings.jarvis_api_token

    if not expected or expected == "change-me":
        raise HTTPException(status_code=503, detail="Önce güçlü bir JARVIS_API_TOKEN ayarlamalısın.")

    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""

    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Kimlik doğrulaması gerekli.")
