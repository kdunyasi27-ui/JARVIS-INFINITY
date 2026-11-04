from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.db import init_db, save_message, get_history
from app.security import require_token
from app.providers import generate, ModelUnavailable
from app.agents import choose_agent, AGENTS, get_agent
from app.evolution import daily_review


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan
)

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
INDEX_FILE = WEB_DIR / "index.html"

if WEB_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(WEB_DIR)),
        name="static"
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


@app.get("/")
async def home():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))

    return HTMLResponse("<h1>JARVIS INFINITY</h1>")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "name": settings.app_name,
        "version": "0.2.0"
    }


@app.get("/api/agents", dependencies=[Depends(require_token)])
async def agents():
    return [
        {
            "name": agent.name,
            "purpose": agent.purpose
        }
        for agent in AGENTS
    ]


@app.post("/api/chat", dependencies=[Depends(require_token)])
async def chat(body: ChatRequest):
    conversation_id = body.conversation_id or str(uuid4())

    history = get_history(conversation_id)
    agent_name = choose_agent(body.message)
    agent = get_agent(agent_name)

    messages = [{
        "role": "system",
        "content": (
            "Sen JARVIS INFINITY adlı gelişmiş bir yapay zekâ "
            "asistanısın. Kullanıcıya Türkçe ve açık cevap ver. "
            "Bilmediğin bilgileri uydurma. "
            "Güvenlik önlemlerini aşmaya veya izinsiz erişime "
            "yardım etme.\n\n"
            f"Uzman ajan: {agent.name}\n"
            f"Görev: {agent.instructions}"
        )
    }]

    messages.extend(history)
    messages.append({
        "role": "user",
        "content": body.message
    })

    try:
        answer = await generate(messages)

    except ModelUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Yapay zekâ sağlayıcısına ulaşılamadı."
        )

    save_message(conversation_id, "user", body.message)
    save_message(conversation_id, "assistant", answer)

    return {
        "conversation_id": conversation_id,
        "agent": agent_name,
        "answer": answer
    }


@app.post(
    "/api/evolution/daily-review",
    dependencies=[Depends(require_token)]
)
async def run_daily_review():
    return daily_review()
