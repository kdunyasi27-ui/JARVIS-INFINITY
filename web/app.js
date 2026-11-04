let conversationId = null;
let authMode = "login";

const $ = (id) => document.getElementById(id);

const authSection = $("auth-section");
const chatSection = $("chat-section");
const authForm = $("auth-form");
const chatForm = $("chat-form");

function showMessage(element, message, error = false) {
    element.textContent = message;
    element.className = error ? "message error" : "message success";
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Bir hata oluştu.");
    }

    return data;
}

function setAuthMode(mode) {
    authMode = mode;

    $("login-tab").classList.toggle("active", mode === "login");
    $("register-tab").classList.toggle("active", mode === "register");

    $("auth-submit").textContent =
        mode === "login" ? "Giriş Yap" : "Hesap Oluştur";

    $("password").autocomplete =
        mode === "login" ? "current-password" : "new-password";

    $("auth-message").textContent = "";
}

$("login-tab").addEventListener("click", () => {
    setAuthMode("login");
});

$("register-tab").addEventListener("click", () => {
    setAuthMode("register");
});

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = $("auth-submit");
    button.disabled = true;

    const email = $("email").value.trim();
    const password = $("password").value;

    try {
        if (authMode === "register") {
            await api("/api/register", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });

            showMessage(
                $("auth-message"),
                "Kayıt başarılı. Şimdi giriş yapabilirsin."
            );

            setAuthMode("login");
            return;
        }

        await api("/api/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });

        await loadUser();

    } catch (error) {
        showMessage($("auth-message"), error.message, true);
    } finally {
        button.disabled = false;
    }
});

async function loadUser() {
    const user = await api("/api/me");

    authSection.hidden = true;
    chatSection.hidden = false;

    $("user-email").textContent = user.email;

    await loadMemories();
}

$("logout-btn").addEventListener("click", async () => {
    try {
        await api("/api/logout", { method: "POST" });

        conversationId = null;
        chatSection.hidden = true;
        authSection.hidden = false;

        $("chat-messages").innerHTML = "";
        $("auth-form").reset();

        showMessage($("auth-message"), "Çıkış yapıldı.");

    } catch (error) {
        showMessage($("chat-status"), error.message, true);
    }
});

function addMessage(role, content) {
    const message = document.createElement("div");

    message.className =
        role === "user" ? "user-message" : "assistant-message";

    message.textContent = content;

    $("chat-messages").appendChild(message);

    message.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const input = $("message-input");
    const button = $("send-btn");
    const message = input.value.trim();

    if (!message) return;

    input.value = "";
    button.disabled = true;

    addMessage("user", message);
    showMessage($("chat-status"), "JARVIS düşünüyor...");

    try {
        const result = await api("/api/chat", {
            method: "POST",
            body: JSON.stringify({
                message,
                conversation_id: conversationId
            })
        });

        conversationId = result.conversation_id;

        addMessage("assistant", result.answer);

        showMessage(
            $("chat-status"),
            "Uzman ajan: " + result.agent
        );

    } catch (error) {
        addMessage("assistant", "Hata: " + error.message);
        showMessage($("chat-status"), error.message, true);
    } finally {
        button.disabled = false;
        input.focus();
    }
});

async function loadMemories() {
    try {
        const memories = await api("/api/memory");
        const list = $("memory-list");

        list.innerHTML = "";

        memories.forEach((memory) => {
            const item = document.createElement("div");
            item.className = "memory-item";

            const title = document.createElement("strong");
            title.textContent = memory.title;

            const content = document.createElement("p");
            content.textContent = memory.content;

            const remove = document.createElement("button");
            remove.textContent = "Sil";

            remove.addEventListener("click", async () => {
                try {
                    await api("/api/memory/" + memory.id, {
                        method: "DELETE"
                    });

                    await loadMemories();
                } catch (error) {
                    showMessage($("chat-status"), error.message, true);
                }
            });

            item.append(title, content, remove);
            list.appendChild(item);
        });

    } catch (error) {
        showMessage($("chat-status"), error.message, true);
    }
}

$("memory-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = $("memory-title").value.trim();
    const content = $("memory-content").value.trim();

    try {
        await api("/api/memory", {
            method: "POST",
            body: JSON.stringify({ title, content })
        });

        $("memory-form").reset();
        await loadMemories();

        showMessage($("chat-status"), "Hafızaya kaydedildi.");

    } catch (error) {
        showMessage($("chat-status"), error.message, true);
    }
});

async function startApp() {
    try {
        await loadUser();
    } catch {
        authSection.hidden = false;
        chatSection.hidden = true;
    }
}

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/sw.js")
            .catch((error) => console.error("PWA:", error));
    });
}

startApp();
