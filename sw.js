/* Draft Room service worker.
   FIX: the previous version was cache-first for everything, so a deployed
   change never reached an installed app until CACHE was bumped by hand.
   Navigations now go network-first (fresh app when online, cached shell when
   not); static assets stay cache-first because they are content-addressed by
   the cache version. */
const CACHE = 'gridiron-v28';
const SHELL = ['./', './index.html', './manifest.json',
               './mark.png', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .catch(() => {})            // a single 404 must not abort the install
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // never touch cross-origin

  const isDoc = req.mode === 'navigate' ||
                (req.headers.get('accept') || '').includes('text/html');

  if (isDoc) {
    // network-first: newest app when connected, cached shell when not
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  // static assets: cache-first, fill on miss
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.status === 200 && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      }
      return res;
    }).catch(() => hit))
  );
});
