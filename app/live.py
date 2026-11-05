
import asyncio
import json
import logging
from urllib.parse import quote

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import read_session
from app.config import settings

router = APIRouter()
logger = logging.getLogger("jarvis.live")

GEMINI_LIVE_URL = (
    "wss://generativelanguage.googleapis.com/ws/"
    "google.ai.generativelanguage.v1beta."
    "GenerativeService.BidiGenerateContent"
)


@router.websocket("/ws/live")
async def live_voice(websocket: WebSocket):

    session_token = websocket.cookies.get("jarvis_session")

    if not session_token or not read_session(session_token):
        await websocket.close(code=4401)
        return

    if not settings.gemini_live_api_key:
        await websocket.close(
            code=1011,
            reason="GEMINI_LIVE_API_KEY ayarlanmamış."
        )
        return

    await websocket.accept()

    model = settings.gemini_live_model or "gemini-3.1-flash-live-preview"
    api_key = quote(settings.gemini_live_api_key, safe="")
    url = f"{GEMINI_LIVE_URL}?key={api_key}"

    setup_message = {
        "setup": {
            "model": f"models/{model}",
            "responseModalities": ["AUDIO"],
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "Sen JARVIS INFINITY adlı gelişmiş kişisel "
                        "yapay zekâ asistanısın. Türkçe konuş. "
                        "Doğal, anlaşılır ve yardımcı ol. "
                        "Bilmediğin bilgileri uydurma."
                    )
                }]
            },
            "inputAudioTranscription": {},
            "outputAudioTranscription": {},
            "generationConfig": {
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Aoede"
                        }
                    }
                }
            }
        }
    }

    try:
        async with websockets.connect(
            url,
            open_timeout=20,
            ping_interval=20,
            ping_timeout=20,
            max_size=10 * 1024 * 1024
        ) as gemini:

            logger.info("Gemini Live WebSocket bağlantısı kuruldu.")

            await gemini.send(json.dumps(setup_message))

            first_response = await asyncio.wait_for(
                gemini.recv(),
                timeout=30
            )

            response_data = json.loads(first_response)

            if "setupComplete" not in response_data:
                logger.error(
                    "Gemini kurulum yanıtı başarısız: %s",
                    json.dumps(response_data, ensure_ascii=False)[:1500]
                )

                await websocket.send_json({
                    "error": "Gemini bağlantı kurulumu başarısız. "
                             "Render Logs kayıtlarını kontrol edin."
                })
                await websocket.close(code=1011)
                return

            logger.info("Gemini Live kurulumu başarılı.")

            await websocket.send_text(first_response)

            async def browser_to_gemini():
                while True:
                    raw = await websocket.receive_text()

                    try:
                        message = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if not isinstance(message, dict):
                        continue

                    if isinstance(message.get("realtimeInput"), dict):
                        await gemini.send(json.dumps({
                            "realtimeInput": message["realtimeInput"]
                        }))

            async def gemini_to_browser():
                async for message in gemini:
                    await websocket.send_text(message)

            tasks = [
                asyncio.create_task(browser_to_gemini()),
                asyncio.create_task(gemini_to_browser())
            ]

            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            await asyncio.gather(
                *pending,
                return_exceptions=True
            )

            for task in done:
                if not task.cancelled():
                    error = task.exception()
                    if error:
                        raise error

    except WebSocketDisconnect:
        logger.info("Tarayıcı canlı bağlantıyı kapattı.")

    except asyncio.CancelledError:
        raise

    except Exception as exc:
        status = getattr(
            getattr(exc, "response", None),
            "status_code",
            None
        )

        received = getattr(exc, "rcvd", None)
        sent = getattr(exc, "sent", None)

        logger.error(
            "Gemini Live hata: %s | HTTP: %s | "
            "Gelen kapatma kodu: %s | Gelen neden: %s | "
            "Gönderilen kapatma: %s",
            type(exc).__name__,
            status,
            getattr(received, "code", None),
            getattr(received, "reason", None),
            getattr(sent, "code", None)
        )

        try:
            await websocket.send_json({
                "error": "Canlı bağlantı hatası: "
                         + type(exc).__name__
            })
            await websocket.close(code=1011)
        except Exception:
            pass
