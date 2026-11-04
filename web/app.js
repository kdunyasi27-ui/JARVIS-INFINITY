"use strict";

const messages = document.getElementById("messages");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const systemStatus = document.getElementById("system-status");
const statusDot = document.querySelector(".status-dot");

let conversationId = null;
let sending = false;

function getToken() {
    let token = localStorage.getItem("jarvis_token");

    if (!token) {
        token = prompt("JARVIS API anahtarını gir:");

        if (token && token.trim()) {
            token = token.trim();
            localStorage.setItem("jarvis_token", token);
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
            throw new Error("Sunucu yanıt vermiyor.");
        }

        const data = await response.json();

        systemStatus.textContent = `${data.name} çevrimiçi`;
        statusDot.classList.add("online");

    } catch (error) {
        systemStatus.textContent = "Bağlantı bekleniyor";
        statusDot.classList.remove("online");
    }
}

async function sendMessage() {
    const message = input.value.trim();

    if (!message || sending) return;

    const token = getToken();

    if (!token) {
        addMessage("API anahtarı girilmedi.", "assistant");
        return;
    }

    addMessage(message, "user");
    input.value = "";

    sending = true;
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
            if (response.status === 401) {
                localStorage.removeItem("jarvis_token");
            }

            throw new Error(
                data.detail || "Bir hata oluştu."
            );
        }

        conversationId = data.conversation_id;

        addMessage(
            `[${data.agent}] ${data.answer}`,
            "assistant"
        );

    } catch (error) {
        addMessage(
            "Hata: " + error.message,
            "assistant"
        );

    } finally {
        sending = false;
        sendButton.disabled = false;
        sendButton.textContent = "Gönder";
        input.focus();
    }
}

sendButton.addEventListener("click", sendMessage);

input.addEventListener("keydown", function(event) {
    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {
        event.preventDefault();
        sendMessage();
    }
});

// PWA çevrimdışı dosya desteği
if ("serviceWorker" in navigator) {
    window.addEventListener("load", function() {
        navigator.serviceWorker
            .register("/static/sw.js")
            .catch(function(error) {
                console.error(
                    "PWA kaydı başarısız:",
                    error
                );
            });
    });
}

// Sistem kontrolü
checkSystem();
setInterval(checkSystem, 30000);
