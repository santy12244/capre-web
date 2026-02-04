// CAPRE - Service Worker para PWA
const CACHE_NAME = 'capre-cache-v2';
const STATIC_CACHE = 'capre-static-v2';

// Archivos estaticos a cachear (cache-first)
// Rutas relativas al scope del SW (se resuelven dinamicamente)
const STATIC_ASSETS = [
    '../css/style.css',
    '../img/logo_small.png',
    '../img/logo_vaca.png',
    '../img/vaca_hero.jpg',
    '../manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'
];

// Rutas API (network-first)
const API_ROUTES = [
    '/principal/api/',
    '/principal/ordenos/auto-guardar'
];

// Rutas que no se deben cachear
const NO_CACHE_ROUTES = [
    '/upload',
    '/principal/exportar'
];

// Instalar service worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('CAPRE SW: Cacheando archivos estaticos');
                return cache.addAll(STATIC_ASSETS.filter(url => !url.startsWith('http')));
            })
            .then(() => self.skipWaiting())
    );
});

// Activar y limpiar caches antiguos
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(name => name !== CACHE_NAME && name !== STATIC_CACHE)
                        .map(name => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Interceptar fetch requests
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // No cachear rutas excluidas
    if (NO_CACHE_ROUTES.some(route => url.pathname.includes(route))) {
        return;
    }

    // Network-first para APIs
    if (API_ROUTES.some(route => url.pathname.includes(route))) {
        event.respondWith(networkFirst(event.request));
        return;
    }

    // Cache-first para archivos estaticos
    if (event.request.destination === 'style' ||
        event.request.destination === 'script' ||
        event.request.destination === 'image' ||
        url.pathname.includes('/static/')) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    // Stale-while-revalidate para paginas HTML
    if (event.request.mode === 'navigate' ||
        event.request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(staleWhileRevalidate(event.request));
        return;
    }

    // Default: network con fallback a cache
    event.respondWith(networkFirst(event.request));
});

// Estrategia: Cache primero
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('CAPRE SW: Error en cache-first', error);
        return new Response('Offline', { status: 503 });
    }
}

// Estrategia: Network primero
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        return new Response('Offline', { status: 503 });
    }
}

// Estrategia: Stale mientras revalida
async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    const fetchPromise = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => cached);

    return cached || fetchPromise;
}

// Escuchar mensajes para limpiar cache
self.addEventListener('message', event => {
    if (event.data === 'CLEAR_CACHE') {
        caches.keys().then(names => {
            names.forEach(name => caches.delete(name));
        });
    }
});
