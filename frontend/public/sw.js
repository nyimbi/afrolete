const CACHE_NAME = "afrolete-shell-v1";
const PREFETCH_CACHE_NAME = "afrolete-prefetch-v1";
const SHELL_URLS = ["/", "/emergency", "/family", "/player", "/sponsors", "/developers", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => ![CACHE_NAME, PREFETCH_CACHE_NAME].includes(key))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  const message = event.data || {};
  if (message.type !== "AFROLETE_PREFETCH_URLS" || !Array.isArray(message.urls)) {
    return;
  }
  const port = event.ports?.[0];
  event.waitUntil(
    prefetchUrls(message.urls)
      .then((results) => {
        port?.postMessage({ type: "AFROLETE_PREFETCH_COMPLETE", requestId: message.requestId, results });
      })
      .catch((error) => {
        port?.postMessage({
          type: "AFROLETE_PREFETCH_COMPLETE",
          requestId: message.requestId,
          error: error instanceof Error ? error.message : "Prefetch failed"
        });
      })
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") {
    return;
  }
  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isTravelManifestArtifact = url.pathname.includes("/api/v1/events/travel-manifests/");
  if (!isSameOrigin && !isTravelManifestArtifact) {
    return;
  }
  if (isTravelManifestArtifact) {
    event.respondWith(networkFirst(request, PREFETCH_CACHE_NAME));
    return;
  }
  if (url.pathname.startsWith("/_next/static/") || SHELL_URLS.includes(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  event.respondWith(networkFirst(request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  const cache = await caches.open(CACHE_NAME);
  cache.put(request, response.clone());
  return response;
}

async function networkFirst(request, cacheName = CACHE_NAME) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return (await caches.match(request)) || (await caches.match("/")) || Response.error();
  }
}

async function prefetchUrls(urls) {
  const cache = await caches.open(PREFETCH_CACHE_NAME);
  return Promise.all(
    urls.map(async (url) => {
      try {
        const request = new Request(url, { method: "GET", credentials: "omit", mode: "cors" });
        const response = await fetch(request);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        await cache.put(request, response.clone());
        return {
          url,
          ok: true,
          status: response.status,
          contentType: response.headers.get("content-type"),
          cachedAt: new Date().toISOString()
        };
      } catch (error) {
        return {
          url,
          ok: false,
          status: 0,
          error: error instanceof Error ? error.message : "Prefetch failed",
          cachedAt: new Date().toISOString()
        };
      }
    })
  );
}
