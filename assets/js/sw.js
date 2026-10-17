const VERSION = "{{ now.Unix }}";
const PAGES = `pages-${VERSION}`;
const ASSETS = "assets-v1";
const START_URL = "{{ .Site.Home.RelPermalink }}";
const MAX_ASSETS = 600;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(PAGES).then((cache) => cache.add(START_URL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== PAGES && k !== ASSETS).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function trim(cache) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - MAX_ASSETS; i++) {
    await cache.delete(keys[i]);
  }
}

async function networkFirst(request) {
  const cache = await caches.open(PAGES);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return (await cache.match(request)) || (await cache.match(START_URL)) || Response.error();
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(ASSETS);
  const cached = await cache.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  if (response.ok) {
    await cache.put(request, response.clone());
    trim(cache);
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }
  const url = new URL(request.url);
  const sameOrigin = url.origin === self.location.origin;

  if (request.mode === "navigate" || (sameOrigin && /\.(json|xml)$/.test(url.pathname))) {
    event.respondWith(networkFirst(request));
  } else if (sameOrigin && ["image", "style", "script", "font"].includes(request.destination)) {
    event.respondWith(cacheFirst(request));
  }
});
