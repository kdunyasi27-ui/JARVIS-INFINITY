
let conversationId = null;
let authMode = "login";
let voiceEnabled = true;
let recognition = null;
let listening = false;

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

function speak(text) {
    if (!voiceEnabled || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "tr-TR";
    utterance.rate = 1;
    utterance.pitch = 1;

    const voices = window.speechSynthesis.getVoices();
    const turkishVoice = voices.find(v => v.lang.toLowerCase().startsWith("tr"));

    if (turkishVoice) utterance.voice = turkishVoice;

    window.speechSynthesis.speak(utterance);
}

function setupVoice() {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    const voiceBar = document.createElement("div");
    voiceBar.className = "voice-controls";
    voiceBar.innerHTML = `
        <button id="mic-btn" type="button">🎙️ Konuş</button>
        <button id="voice-toggle" type="button">🔊 Ses açık</button>
        <span id="voice-status">Sesli asistan hazır</span>
    `;

    chatForm.before(voiceBar);

    $("voice-toggle").addEventListener("click", () => {
        voiceEnabled = !voiceEnabled;
        $("voice-toggle").textContent =
            voiceEnabled ? "🔊 Ses açık" : "🔇 Sessiz";
        if (!voiceEnabled) window.speechSynthesis?.cancel();
    });

    if (!SpeechRecognition) {
        $("mic-btn").disabled = true;
        $("voice-status").textContent =
            "Bu tarayıcı ses tanımayı desteklemiyor. Chrome kullan.";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "tr-TR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        listening = true;
        $("mic-btn").textContent = "⏹️ Dinliyorum...";
        $("voice-status").textContent = "Seni dinliyorum...";
    };

    recognition.onend = () => {
        listening = false;
        $("mic-btn").textContent = "🎙️ Konuş";
        if ($("voice-status")) {
            $("voice-status").textContent = "Sesli asistan hazır";
        }
    };

    recognition.onerror = (event) => {
        $("voice-status").textContent =
            "Mikrofon hatası: " + event.error;
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        $("message-input").value = transcript;
        chatForm.requestSubmit();
    };

    $("mic-btn").addEventListener("click", () => {
        if (listening) {
            recognition.stop();
            return;
        }

        window.speechSynthesis?.cancel();

        try {
            recognition.start();
        } catch (error) {
            $("voice-status").textContent =
                "Mikrofon başlatılamadı. Tekrar dene.";
        }
    });
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

$("login-tab").addEventListener("click", () => setAuthMode("login"));
$("register-tab").addEventListener("click", () => setAuthMode("register"));

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

    if (!$("mic-btn")) setupVoice();

    await loadMemories();
}

$("logout-btn").addEventListener("click", async () => {
    try {
        await api("/api/logout", { method: "POST" });

        window.speechSynthesis?.cancel();
        recognition?.stop();

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
        speak(result.answer);

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
