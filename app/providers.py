import httpx

from app.config import settings


class ModelUnavailable(RuntimeError):
    pass


def get_model_providers():
    providers = []

    if settings.model_base_url and settings.model_api_key and settings.model_name:
        providers.append({
            "url": settings.model_base_url,
            "key": settings.model_api_key,
            "model": settings.model_name,
        })

    for item in settings.model_fallbacks.split(";"):
        parts = item.strip().split("|")

        if len(parts) == 3 and all(parts):
            providers.append({
                "url": parts[0],
                "key": parts[1],
                "model": parts[2],
            })

    return providers


async def generate(messages: list[dict[str, str]]) -> str:
    providers = get_model_providers()

    if not providers:
        raise ModelUnavailable(
            "Yapay zekâ modeli yapılandırılmamış."
        )

    errors = []

    async with httpx.AsyncClient(
        timeout=settings.model_timeout_seconds
    ) as client:

        for provider in providers:
            url = provider["url"].rstrip("/")

            if not url.endswith("/chat/completions"):
                url += "/chat/completions"

            headers = {
                "Authorization": f"Bearer {provider['key']}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": provider["model"],
                "messages": messages,
                "temperature": 0.4,
            }

            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

                answer = data["choices"][0]["message"]["content"]

                if isinstance(answer, str) and answer.strip():
                    return answer

                raise ValueError("Boş model cevabı")

            except Exception as exc:
                errors.append(
                    f"{provider['model']}: {type(exc).__name__}"
                )

    raise ModelUnavailable(
        "Tüm yapay zekâ modelleri başarısız oldu: "
        + "; ".join(errors)
    )
