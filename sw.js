/**
 * NIEd Service Worker — long-lived browser cache for static assets.
 *
 * GitHub Pages sends `Cache-Control: max-age=600` for every file, so without
 * this a returning student re-downloads fonts, images and JS every 10 minutes.
 * Strategy (same-origin GET only):
 *   - /assets/fonts/*            → cache-first (font files never change)
 *   - images, /assets/css/*, *.js → stale-while-revalidate (instant from cache,
 *                                   refreshed in the background for next visit)
 *   - HTML, JSON, PDF, everything else → not touched (always from network)
 *
 * To force every browser to drop old cached assets, bump VERSION.
 * Emergency kill switch: replace this file's contents with
 *   self.addEventListener('install',()=>self.skipWaiting());
 *   self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(k=>Promise.all(k.map(c=>caches.delete(c)))).then(()=>self.registration.unregister())));
 */
var VERSION = 'v1';
var FONT_CACHE = 'nied-fonts-' + VERSION;
var ASSET_CACHE = 'nied-assets-' + VERSION;
var MAX_ASSETS = 200;

self.addEventListener('install', function() {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(k) {
        return k.indexOf('nied-') === 0 && k !== FONT_CACHE && k !== ASSET_CACHE;
      }).map(function(k) { return caches.delete(k); }));
    }).then(function() { return self.clients.claim(); })
  );
});

function trimCache(name, max) {
  caches.open(name).then(function(cache) {
    cache.keys().then(function(keys) {
      if (keys.length > max) {
        Promise.all(keys.slice(0, keys.length - max).map(function(k) { return cache.delete(k); }));
      }
    });
  });
}

function cacheFirst(request) {
  return caches.open(FONT_CACHE).then(function(cache) {
    return cache.match(request).then(function(hit) {
      return hit || fetch(request).then(function(res) {
        if (res.ok) cache.put(request, res.clone());
        return res;
      });
    });
  });
}

function staleWhileRevalidate(event) {
  var request = event.request;
  return caches.open(ASSET_CACHE).then(function(cache) {
    return cache.match(request).then(function(hit) {
      var update = fetch(request).then(function(res) {
        if (res.ok && res.type === 'basic') {
          cache.put(request, res.clone());
          trimCache(ASSET_CACHE, MAX_ASSETS);
        }
        return res;
      });
      if (hit) {
        event.waitUntil(update.catch(function() {}));
        return hit;
      }
      return update;
    });
  });
}

self.addEventListener('fetch', function(event) {
  var request = event.request;
  if (request.method !== 'GET') return;
  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.search) return; // ?v=… / ?popup=1 style requests go straight to network

  var path = url.pathname;
  if (path.indexOf('/assets/fonts/') === 0 && /\.woff2$/.test(path)) {
    event.respondWith(cacheFirst(request));
  } else if (/\.(png|jpe?g|webp|gif|svg|ico|css|js)$/i.test(path) && path !== '/sw.js') {
    event.respondWith(staleWhileRevalidate(event));
  }
});
