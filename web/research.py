import httpx

from app.config import settings


class ResearchUnavailable(RuntimeError):
    pass


async def search_web(query: str):
    query = query.strip()

    if not query:
        raise ValueError("Arama sorgusu boş olamaz.")

    if not settings.search_api_url or not settings.search_api_key:
        raise ResearchUnavailable(
            "Araştırma servisi henüz yapılandırılmadı."
        )

    headers = {
        "Authorization": f"Bearer {settings.search_api_key}"
    }

    params = {
        "q": query
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                settings.search_api_url,
                headers=headers,
                params=params
            )

            response.raise_for_status()
            data = response.json()

        return data

    except httpx.HTTPError as exc:
        raise ResearchUnavailable(
            "Araştırma servisine ulaşılamadı."
        ) from exc
