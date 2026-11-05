
(() => {
    let socket = null;
    let audioContext = null;
    let mediaStream = null;
    let processor = null;
    let silentGain = null;
    let running = false;
    let nextPlayTime = 0;
    let audioSources = [];

    const status = (message) => {
        const element = document.getElementById("voice-status");
        if (element) element.textContent = message;
    };

    function base64ToBytes(base64) {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);

        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }

        return bytes;
    }

    function bytesToBase64(bytes) {
        let binary = "";

        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }

        return btoa(binary);
    }

    function stopPlayback() {
        for (const source of audioSources) {
            try {
                source.stop();
            } catch (_) {}
        }

        audioSources = [];

        if (audioContext) {
            nextPlayTime = audioContext.currentTime;
        }
    }

    function resampleTo16k(input, inputRate) {
        const ratio = inputRate / 16000;
        const length = Math.floor(input.length / ratio);
        const output = new Int16Array(length);

        for (let i = 0; i < length; i++) {
            const position = i * ratio;
            const index = Math.floor(position);
            const fraction = position - index;

            const a = input[index] || 0;
            const b = input[index + 1] || a;

            let sample = a + (b - a) * fraction;

            sample = Math.max(-1, Math.min(1, sample));

            output[i] = sample < 0
                ? sample * 32768
                : sample * 32767;
        }

        return output;
    }

    function sendAudio(input) {
        if (!running || !socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }

        const pcm = resampleTo16k(
            input,
            audioContext.sampleRate
        );

        if (!pcm.length) return;

        const bytes = new Uint8Array(pcm.buffer);

        socket.send(JSON.stringify({
            realtimeInput: {
                audio: {
                    mimeType: "audio/pcm;rate=16000",
                    data: bytesToBase64(bytes)
                }
            }
        }));
    }

    function playAudio(base64) {
        if (!audioContext || !running) return;

        const bytes = base64ToBytes(base64);

        if (bytes.length < 2) return;

        const pcm = new Int16Array(
            bytes.buffer,
            bytes.byteOffset,
            Math.floor(bytes.byteLength / 2)
        );

        const audioBuffer = audioContext.createBuffer(
            1,
            pcm.length,
            24000
        );

        const channel = audioBuffer.getChannelData(0);

        for (let i = 0; i < pcm.length; i++) {
            channel[i] = pcm[i] / 32768;
        }

        const source = audioContext.createBufferSource();

        source.buffer = audioBuffer;
        source.connect(audioContext.destination);

        source.onended = () => {
            audioSources = audioSources.filter(
                item => item !== source
            );
        };

        const startAt = Math.max(
            audioContext.currentTime,
            nextPlayTime
        );

        source.start(startAt);

        nextPlayTime = startAt + audioBuffer.duration;

        audioSources.push(source);
    }

    function handleMessage(event) {
        let message;

        try {
            message = JSON.parse(event.data);
        } catch (_) {
            return;
        }

        if (message.error) {
            status(message.error);
            return;
        }

        if (message.setupComplete) {
            status("JARVIS canlı bağlantıya hazır.");
            return;
        }

        const content = message.serverContent;

        if (!content) return;

        if (content.interrupted) {
            stopPlayback();
            status("Konuşmanı dinliyorum...");
            return;
        }

        if (content.inputTranscription?.text) {
            status(
                "Sen: " + content.inputTranscription.text
            );
        }

        if (content.modelTurn?.parts) {
            for (const part of content.modelTurn.parts) {
                if (
                    part.inlineData?.data &&
                    part.inlineData.mimeType?.startsWith("audio/")
                ) {
                    playAudio(part.inlineData.data);
                }
            }
        }

        if (content.turnComplete) {
            status("JARVIS hazır. Konuşabilirsin.");
        }
    }

    async function startLive(button) {
        if (running) return;

        if (!navigator.mediaDevices?.getUserMedia) {
            status("Mikrofon için HTTPS bağlantısı gerekli.");
            return;
        }

        button.disabled = true;
        status("Mikrofon hazırlanıyor...");

        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            audioContext = new AudioContext();

            await audioContext.resume();

            const protocol =
                location.protocol === "https:" ? "wss:" : "ws:";

            socket = new WebSocket(
                protocol + "//" + location.host + "/ws/live"
            );

            socket.onmessage = handleMessage;

            socket.onerror = () => {
                status("Canlı bağlantı hatası.");
            };

            socket.onclose = (event) => {
                if (running) {
                    status(
                        "Bağlantı kapandı. Kod: " + event.code
                    );
                    stopLive();
                }
            };

            socket.onopen = () => {
                running = true;

                const source = audioContext.createMediaStreamSource(
                    mediaStream
                );

                processor = audioContext.createScriptProcessor(
                    4096,
                    1,
                    1
                );

                silentGain = audioContext.createGain();
                silentGain.gain.value = 0;

                processor.onaudioprocess = (event) => {
                    sendAudio(event.inputBuffer.getChannelData(0));
                };

                source.connect(processor);
                processor.connect(silentGain);
                silentGain.connect(audioContext.destination);

                button.textContent = "⏹ Canlı konuşmayı bitir";
                button.disabled = false;

                status("JARVIS seni dinliyor...");
            };

        } catch (error) {
            status("Başlatılamadı: " + error.message);
            stopLive();
            button.disabled = false;
        }
    }

    function stopLive() {
        running = false;

        stopPlayback();

        if (socket) {
            const oldSocket = socket;
            socket = null;

            if (
                oldSocket.readyState === WebSocket.OPEN ||
                oldSocket.readyState === WebSocket.CONNECTING
            ) {
                oldSocket.close();
            }
        }

        if (processor) {
            processor.disconnect();
            processor = null;
        }

        if (silentGain) {
            silentGain.disconnect();
            silentGain = null;
        }

        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }

        if (audioContext) {
            audioContext.close().catch(() => {});
            audioContext = null;
        }

        const button = document.getElementById("live-btn");

        if (button) {
            button.textContent = "🎙 Canlı konuş";
            button.disabled = false;
        }

        status("Canlı ses kapatıldı.");
    }

    function addButton() {
        const voiceBar = document.querySelector(".voice-controls");

        if (!voiceBar || document.getElementById("live-btn")) {
            return;
        }

        const button = document.createElement("button");

        button.id = "live-btn";
        button.type = "button";
        button.textContent = "🎙 Canlı konuş";

        button.addEventListener("click", () => {
            if (running) {
                stopLive();
            } else {
                startLive(button);
            }
        });

        voiceBar.appendChild(button);
    }

    const observer = new MutationObserver(addButton);

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    addButton();
})();
