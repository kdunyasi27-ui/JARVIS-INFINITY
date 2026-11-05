
import asyncio
import json
from urllib.parse import quote

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import read_session
from app.config import settings


router = APIRouter()

GEMINI_LIVE_URL = (
    "wss://generativelanguage.googleapis.com/ws/"
    "google.ai.generativelanguage.v1beta."
    "GenerativeService.BidiGenerateContent"
)


@router.websocket("/ws/live")
async def live_voice(websocket: WebSocket):
    # Kullanıcı oturumunu doğrula
    session_token = websocket.cookies.get("jarvis_session")

    if not session_token or not read_session(session_token):
        await websocket.close(code=4401)
        return

    # API anahtarını kontrol et
    if not settings.gemini_live_api_key:
        await websocket.close(
            code=1011,
            reason="Gemini Live API anahtarı ayarlanmamış."
        )
        return

    await websocket.accept()

    api_key = quote(settings.gemini_live_api_key, safe="")
    model = settings.gemini_live_model

    url = f"{GEMINI_LIVE_URL}?key={api_key}"

    setup_message = {
        "setup": {
            "model": f"models/{model}",
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Aoede"
                        }
                    }
                }
            },
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "Sen JARVIS INFINITY adlı gelişmiş "
                            "kişisel yapay zekâ asistanısın. "
                            "Kullanıcıyla Türkçe konuş. "
                            "Doğal, anlaşılır ve yardımcı ol. "
                            "Bilmediğin bilgileri uydurma."
                        )
                    }
                ]
            },
            "inputAudioTranscription": {},
            "outputAudioTranscription": {}
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

            # Gemini oturumunu başlat
            await gemini.send(json.dumps(setup_message))

            # Kurulum yanıtını bekle
            first_response = await asyncio.wait_for(
                gemini.recv(),
                timeout=20
            )

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

                    realtime_input = message.get("realtimeInput")

                    if isinstance(realtime_input, dict):
                        await gemini.send(
                            json.dumps({
                                "realtimeInput": realtime_input
                            })
                        )

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
        pass

    except asyncio.CancelledError:
        raise

    except Exception:
        try:
            await websocket.send_json({
                "error": "Canlı ses bağlantısı kesildi."
            })
            await websocket.close(code=1011)
        except Exception:
            pass
