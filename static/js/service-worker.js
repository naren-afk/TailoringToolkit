// Tailoring Shop Management - Service Worker
const CACHE_NAME = 'tailoring-shop-v1.0.0';
const STATIC_CACHE = 'tailoring-static-v1.0.0';
const DYNAMIC_CACHE = 'tailoring-dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/icons/icon-192.svg',
    '/static/icons/icon-512.svg',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Routes to cache dynamically
const DYNAMIC_ROUTES = [
    '/customers',
    '/orders',
    '/pending-orders',
    '/reports'
];

// API routes that should be cached
const API_CACHE_PATTERNS = [
    /\/api\//,
    /\/customers\/\d+/,
    /\/orders\/\d+/
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Install event');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('Service Worker: Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('Service Worker: Static files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Error caching static files', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activate event');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Cleanup complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension requests
    if (url.protocol === 'chrome-extension:') {
        return;
    }
    
    event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
    const url = new URL(request.url);
    
    try {
        // Strategy 1: Static assets - Cache First
        if (isStaticAsset(url)) {
            return await cacheFirst(request);
        }
        
        // Strategy 2: API calls - Network First with cache fallback
        if (isApiCall(url)) {
            return await networkFirst(request);
        }
        
        // Strategy 3: HTML pages - Stale While Revalidate
        if (isHtmlPage(request)) {
            return await staleWhileRevalidate(request);
        }
        
        // Strategy 4: External resources - Cache First
        if (isExternalResource(url)) {
            return await cacheFirst(request);
        }
        
        // Default: Network First
        return await networkFirst(request);
        
    } catch (error) {
        console.error('Service Worker: Fetch error', error);
        return await handleOffline(request);
    }
}

// Cache Strategies
async function cacheFirst(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('Service Worker: Network failed, serving offline page');
        return await handleOffline(request);
    }
}

async function networkFirst(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('Service Worker: Network failed, trying cache');
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return await handleOffline(request);
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    // Start fetch in background
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => null);
    
    // Return cached version immediately if available
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Otherwise wait for network
    return await fetchPromise || await handleOffline(request);
}

// Helper functions
function isStaticAsset(url) {
    return url.pathname.includes('/static/') || 
           url.pathname.match(/\.(css|js|png|jpg|jpeg|svg|ico|woff|woff2)$/);
}

function isApiCall(url) {
    return url.pathname.startsWith('/api/') || 
           API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isHtmlPage(request) {
    return request.destination === 'document' || 
           request.headers.get('Accept')?.includes('text/html');
}

function isExternalResource(url) {
    return url.origin !== self.location.origin;
}

async function handleOffline(request) {
    const url = new URL(request.url);
    
    // For HTML pages, return offline page
    if (isHtmlPage(request)) {
        return new Response(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Offline - Tailoring Shop</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background-color: #f8f9fa;
                        color: #333;
                    }
                    .offline-container {
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        max-width: 500px;
                    }
                    .offline-icon {
                        font-size: 4rem;
                        margin-bottom: 1rem;
                    }
                    .btn {
                        background-color: #007bff;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 1rem;
                    }
                    .btn:hover {
                        background-color: #0056b3;
                    }
                </style>
            </head>
            <body>
                <div class="offline-container">
                    <div class="offline-icon">📱</div>
                    <h1>You're Offline</h1>
                    <p>It looks like you've lost your internet connection. Don't worry, your tailoring shop data is safely stored locally.</p>
                    <p>When you're back online, everything will sync automatically.</p>
                    <button class="btn" onclick="window.location.reload()">Try Again</button>
                </div>
            </body>
            </html>
        `, {
            status: 200,
            headers: {
                'Content-Type': 'text/html'
            }
        });
    }
    
    // For API calls, return offline response
    if (isApiCall(url)) {
        return new Response(JSON.stringify({
            error: 'offline',
            message: 'This feature is not available offline'
        }), {
            status: 503,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    // For other resources, return empty response
    return new Response('', { status: 503 });
}

// Background sync for form submissions
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync event', event.tag);
    
    if (event.tag === 'background-sync-orders') {
        event.waitUntil(syncOrders());
    }
    
    if (event.tag === 'background-sync-customers') {
        event.waitUntil(syncCustomers());
    }
});

async function syncOrders() {
    try {
        // Get pending orders from IndexedDB
        const pendingOrders = await getPendingOrders();
        
        for (const order of pendingOrders) {
            try {
                const response = await fetch('/orders/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(order)
                });
                
                if (response.ok) {
                    await removePendingOrder(order.id);
                    console.log('Service Worker: Order synced successfully');
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync order', error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Sync orders failed', error);
    }
}

async function syncCustomers() {
    try {
        // Similar implementation for customers
        console.log('Service Worker: Syncing customers...');
    } catch (error) {
        console.error('Service Worker: Sync customers failed', error);
    }
}

// Push notifications
self.addEventListener('push', (event) => {
    console.log('Service Worker: Push event received');
    
    const options = {
        body: event.data ? event.data.text() : 'New notification from Tailoring Shop',
        icon: '/static/icons/icon-192.svg',
        badge: '/static/icons/icon-192.svg',
        vibrate: [200, 100, 200],
        tag: 'tailoring-notification',
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/icons/icon-192.svg'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Tailoring Shop', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('Service Worker: Notification click event');
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            cacheUrls(event.data.urls)
        );
    }
});

async function cacheUrls(urls) {
    const cache = await caches.open(DYNAMIC_CACHE);
    return cache.addAll(urls);
}

// IndexedDB helpers (simplified)
async function getPendingOrders() {
    // Implementation would use IndexedDB to get pending orders
    return [];
}

async function removePendingOrder(orderId) {
    // Implementation would use IndexedDB to remove synced order
    console.log('Removing pending order:', orderId);
}

// Error handling
self.addEventListener('error', (event) => {
    console.error('Service Worker: Error occurred', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker: Unhandled promise rejection', event.reason);
});

console.log('Service Worker: Loaded successfully');
