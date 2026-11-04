import httpx

from app.config import settings


class ModelUnavailable(RuntimeError):
    pass


async def generate(messages: list[dict[str, str]]) -> str:
    if not (settings.model_base_url and settings.model_api_key and settings.model_name):
        raise ModelUnavailable("Henüz yapay zekâ modeli bağlanmadı. Model sağlayıcısı ayarlarını yapılandırmalısın.")

    url = settings.model_base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.model_api_key}"}
    payload = {"model": settings.model_name, "messages": messages, "temperature": 0.4}

    async with httpx.AsyncClient(timeout=settings.model_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelUnavailable("Yapay zekâ sağlayıcısından geçerli cevap alınamadı.") from exc
