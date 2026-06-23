/* Service Worker — Campo v4 */
const CACHE = 'campo-v4';

const STATIC_URLS = [
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/offline-queue.js',
  '/static/logo.png',
];

// ── Install: pré-cache de assets estáticos ─────────────────
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC_URLS).catch(() => {}))
  );
});

// ── Activate: limpa caches antigos ────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch ─────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return; // POST: deixa o JS gerenciar

  const url = e.request.url;

  // Assets estáticos: cache-first
  if (url.includes('/static/')) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(res => {
          if (res && res.status === 200) {
            caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          }
          return res;
        }).catch(() => new Response('', { status: 503 }));
      })
    );
    return;
  }

  // Páginas HTML: network-first, fallback para cache
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res && res.status === 200) {
          caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});

// ── Background Sync: avisa os clientes para sincronizar ───
self.addEventListener('sync', e => {
  if (e.tag === 'flush-queue') {
    e.waitUntil(
      self.clients.matchAll().then(clients =>
        clients.forEach(c => c.postMessage({ type: 'FLUSH' }))
      )
    );
  }
});