/* Garda 2026: service worker (generuojamas build.py). Versija: 264f500938 */
'use strict';
var CACHE = 'garda-264f500938';
var PRECACHE = ["./", "index.html", "manifest.webmanifest", "fonts/hanken-grotesk.woff", "fonts/bodoni-moda.woff", "fonts/bodoni-moda-italic.woff", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(PRECACHE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k.indexOf('garda-') === 0 && k !== CACHE; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function timeout(ms) {
  return new Promise(function (_, rej) { setTimeout(function () { rej(new Error('timeout')); }, ms); });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;           // Wikipedia ir kt.: tiesiai į tinklą

  if (req.mode === 'navigate') {                              // puslapis: pirma tinklas, jei lėtas ar nėra ryšio: talpykla
    e.respondWith(
      Promise.race([fetch(req), timeout(5000)]).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put('index.html', copy); });
        }
        return res;
      }).catch(function () {
        return caches.match('index.html').then(function (r) { return r || fetch(req); });
      })
    );
    return;
  }

  e.respondWith(                                              // šriftai, ikonos: pirma talpykla
    caches.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
