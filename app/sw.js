/* Offline-Hülle für das Trading-Journal: App-Datei wird gecacht und im Hintergrund aktualisiert. Daten laufen nie über den Cache. */
const CACHE = 'journal-shell-v16';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-180.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async c => {
    try { const r = await fetch(e.request, {cache: 'no-cache'}); if (r && r.ok) c.put(e.request, r.clone()); return r; }
    catch (err) { return (await c.match(e.request, {ignoreSearch: true})) || new Response('Offline', {status: 503}); }
  }));
});
