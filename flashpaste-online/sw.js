const CACHE_NAME = 'flashpaste-v2';
const ASSETS = [
  '',
  'index.php',
  'style.css',
  'script.js'
];

self.addEventListener('install', (event) => {
  self.skipWaiting(); 
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Using cache.addAll but catching errors so one missing file doesn't kill the PWA
      return Promise.allSettled(ASSETS.map(url => cache.add(url)));
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim()); 
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});