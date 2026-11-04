const messages = document.getElementById("messages");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const systemStatus = document.getElementById("system-status");
const statusDot = document.querySelector(".status-dot");

let conversationId = null;

function getToken() {
    let token = localStorage.getItem("jarvis_token");

    if (!token) {
        token = prompt("JARVIS API anahtarını gir:");
        if (token) {
            localStorage.setItem("jarvis_token", token.trim());
        }
    }

    return token;
}

function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}

async function checkSystem() {
    try {
        const response = await fetch("/api/health");

        if (!response.ok) {
            throw new Error("Sistem yanıt vermiyor");
        }

        const data = await response.json();

        systemStatus.textContent = "Sistem çevrimiçi";
        statusDot.classList.add("online");
    } catch (error) {
        systemStatus.textContent = "Bağlantı bekleniyor";
        statusDot.classList.remove("online");
    }
}

async function sendMessage() {
    const message = input.value.trim();

    if (!message || sendButton.disabled) {
        return;
    }

    const token = getToken();

    if (!token) {
        addMessage("API anahtarı girilmedi.", "assistant");
        return;
    }

    addMessage(message, "user");
    input.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Düşünüyor...";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("jarvis_token");
            }

            throw new Error(data.detail || "Bir hata oluştu.");
        }

        conversationId = data.conversation_id;

        addMessage(data.answer, "assistant");

    } catch (error) {
        addMessage("Hata: " + error.message, "assistant");
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Gönder";
        input.focus();
    }
}

sendButton.addEventListener("click", sendMessage);

input.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

checkSystem();
setInterval(checkSystem, 30000);
