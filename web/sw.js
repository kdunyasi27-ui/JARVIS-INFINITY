const CACHE_NAME = "jarvis-infinity-v1";

const STATIC_FILES = [
    "/",
    "/static/style.css",
    "/static/app.js",
    "/static/manifest.webmanifest"
];

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_FILES);
        })
    );

    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", event => {
    const request = event.request;

    if (request.method !== "GET") return;

    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) return;

    event.respondWith(
        fetch(request)
            .then(response => {
                if (response.ok && url.origin === self.location.origin) {
                    const copy = response.clone();

                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, copy);
                    });
                }

                return response;
            })
            .catch(async () => {
                const cached = await caches.match(request);

                if (cached) return cached;

                if (request.mode === "navigate") {
                    return caches.match("/");
                }

                return new Response("Çevrimdışısın.", {
                    status: 503,
                    headers: {
                        "Content-Type": "text/plain; charset=utf-8"
                    }
                });
            })
    );
});
