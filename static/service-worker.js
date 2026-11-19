const CACHE_NAME = "zenvix-public-assets-v1";
const PUBLIC_ASSET_PATHS = new Set([
    "/static/manifest.webmanifest",
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/icons/icon-maskable-512.png",
    "/static/icons/apple-touch-icon.png",
]);

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(Array.from(PUBLIC_ASSET_PATHS)))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => Promise.all(
                cacheNames
                    .filter((cacheName) =>
                        cacheName.startsWith("zenvix-public-assets-")
                        && cacheName !== CACHE_NAME
                    )
                    .map((cacheName) => caches.delete(cacheName))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    const requestUrl = new URL(event.request.url);
    if (
        event.request.method !== "GET"
        || requestUrl.origin !== self.location.origin
        || !PUBLIC_ASSET_PATHS.has(requestUrl.pathname)
    ) {
        return;
    }

    event.respondWith(
        caches.open(CACHE_NAME).then(async (cache) => {
            const cachedResponse = await cache.match(requestUrl.pathname);
            if (cachedResponse) {
                return cachedResponse;
            }

            const response = await fetch(event.request);
            if (response.ok && response.type === "basic") {
                await cache.put(requestUrl.pathname, response.clone());
            }
            return response;
        })
    );
});
