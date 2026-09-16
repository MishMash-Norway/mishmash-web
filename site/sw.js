---
---
/* Offline reading for mishmash.no (issue #66).
   Pages are fetched from the network first and kept in a cache as a fallback,
   so a page you have read stays readable without coverage. Stylesheets,
   scripts, fonts and images are served from the cache and refreshed in the
   background. Internal and chat pages are never cached. Nothing is sent
   anywhere: the worker only stores responses in this browser. */
var VERSION = 'mishmash-{{ site.github.build_revision | default: site.time | date: "%Y%m%d%H%M" }}';
var PAGES = VERSION + '-pages';
var ASSETS = VERSION + '-assets';
var NEVER = [/^\/internal\//, /^\/no\/internal\//, /^\/chat\//, /^\/search\.json$/, /^\/sw\.js$/];

self.addEventListener('install', function (e) { self.skipWaiting(); });

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf(VERSION) !== 0; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (NEVER.some(function (re) { return re.test(url.pathname); })) return;

  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(function (res) {
      var copy = res.clone();
      caches.open(PAGES).then(function (c) { c.put(req, copy); });
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) { return hit || caches.match('/'); });
    }));
    return;
  }

  if (/\.(css|js|woff2?|svg|png|jpe?g|webp|ico|json)$/.test(url.pathname)) {
    e.respondWith(caches.open(ASSETS).then(function (c) {
      return c.match(req).then(function (hit) {
        var refresh = fetch(req).then(function (res) { if (res.ok) c.put(req, res.clone()); return res; }).catch(function () { return hit; });
        return hit || refresh;
      });
    }));
  }
});
