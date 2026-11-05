
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Response,
    Cookie
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.db import (
    init_db,
    claim_conversation,
    get_user_history,
    save_user_message
)
from app.security import require_token
from app.providers import generate, ModelUnavailable
from app.agents import choose_agent, AGENTS, get_agent
from app.evolution import daily_review
from app.auth import (
    register,
    login,
    create_session,
    read_session
)
from app.workspace import (
    save_memory,
    get_memories,
    delete_memory
)

# Canlı ses bağlantısı
from app.live import router as live_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
    lifespan=lifespan
)

# Gemini Live WebSocket rotasını ekle
app.include_router(live_router)


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


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class MemoryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)


def current_user(
    jarvis_session: str | None = Cookie(default=None)
):
    if not jarvis_session:
        raise HTTPException(
            status_code=401,
            detail="Önce giriş yapmalısın."
        )

    user = read_session(jarvis_session)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Oturum geçersiz veya süresi dolmuş."
        )

    return user


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
        "version": "0.5.0"
    }


@app.post("/api/register")
async def register_user(body: RegisterRequest):
    try:
        user_id = register(body.email, body.password)

        return {
            "success": True,
            "user_id": user_id,
            "message": "Kayıt başarılı. Şimdi giriş yapabilirsin."
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/api/login")
async def login_user(
    body: LoginRequest,
    response: Response
):
    user = login(body.email, body.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="E-posta veya şifre hatalı."
        )

    token = create_session(user["id"])

    response.set_cookie(
        key="jarvis_session",
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=86400,
        path="/"
    )

    return {
        "success": True,
        "email": user["email"]
    }


@app.post("/api/logout")
async def logout_user(response: Response):
    response.delete_cookie(
        key="jarvis_session",
        path="/"
    )

    return {"success": True}


@app.get("/api/me")
async def me(user=Depends(current_user)):
    return {
        "id": user["id"],
        "email": user["email"]
    }


@app.get(
    "/api/agents",
    dependencies=[Depends(require_token)]
)
async def agents():
    return [
        {
            "name": agent.name,
            "purpose": agent.purpose
        }
        for agent in AGENTS
    ]


@app.post("/api/chat")
async def chat(
    body: ChatRequest,
    user=Depends(current_user)
):
    conversation_id = (
        body.conversation_id or str(uuid4())
    )

    if not claim_conversation(
        user["id"],
        conversation_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Bu konuşmaya erişim izniniz yok."
        )

    try:
        history = get_user_history(
            user["id"],
            conversation_id
        )
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Bu konuşmaya erişim izniniz yok."
        )

    agent_name = choose_agent(body.message)
    agent = get_agent(agent_name)

    memory = get_memories(user["id"])

    memory_text = "\n".join(
        f"{item['title']}: {item['content']}"
        for item in memory
    )

    messages = [{
        "role": "system",
        "content": (
            "Sen JARVIS INFINITY adlı yapay zekâ asistanısın. "
            "Türkçe ve açık cevap ver. Bilmediğin bilgileri uydurma. "
            "Güvenlik önlemlerini aşmaya veya izinsiz erişime yardım etme.\n"
            f"Uzman ajan: {agent.name}\n"
            f"Görev: {agent.instructions}\n"
            f"Kullanıcı hafızası:\n{memory_text}"
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

    save_user_message(
        user["id"],
        conversation_id,
        "user",
        body.message
    )

    save_user_message(
        user["id"],
        conversation_id,
        "assistant",
        answer
    )

    return {
        "conversation_id": conversation_id,
        "agent": agent_name,
        "answer": answer
    }


@app.get("/api/memory")
async def memory_list(user=Depends(current_user)):
    return get_memories(user["id"])


@app.post("/api/memory")
async def memory_create(
    body: MemoryRequest,
    user=Depends(current_user)
):
    save_memory(
        user["id"],
        body.title,
        body.content
    )

    return {"success": True}


@app.delete("/api/memory/{memory_id}")
async def memory_remove(
    memory_id: int,
    user=Depends(current_user)
):
    deleted = delete_memory(
        user["id"],
        memory_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Hafıza kaydı bulunamadı."
        )

    return {"success": True}


@app.post(
    "/api/evolution/daily-review",
    dependencies=[Depends(require_token)]
)
async def run_daily_review():
    return daily_review()
