/* offline-queue.js — Ponto + Gasto offline com GPS */
(function () {
  'use strict';

  const DB_NAME = 'campo-offline-v1';
  const STORE   = 'queue';

  // ── IndexedDB ──────────────────────────────────────────────
  function openDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = ev =>
        ev.target.result.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
      req.onsuccess = ev => resolve(ev.target.result);
      req.onerror   = ev => reject(ev.target.error);
    });
  }

  async function dbAdd(item) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).add(item);
      tx.oncomplete = resolve;
      tx.onerror    = ev => reject(ev.target.error);
    });
  }

  async function dbAll() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx  = db.transaction(STORE, 'readonly');
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () => resolve(req.result);
      req.onerror   = ev => reject(ev.target.error);
    });
  }

  async function dbRemove(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(id);
      tx.oncomplete = resolve;
      tx.onerror    = ev => reject(ev.target.error);
    });
  }

  // ── Serialização de formulário (suporta arquivos) ─────────
  function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload  = ev => resolve(ev.target.result);
      r.onerror = reject;
      r.readAsDataURL(file);
    });
  }

  async function serializeForm(form) {
    const fields = {}, files = {};
    const fd = new FormData(form);
    for (const [k, v] of fd.entries()) {
      if (v instanceof File && v.size > 0) {
        files[k] = { name: v.name, type: v.type, dataURL: await fileToDataURL(v) };
      } else {
        fields[k] = v;
      }
    }
    return { fields, files };
  }

  // ── GPS ───────────────────────────────────────────────────
  let gpsCache = null; // capturado uma vez na carga da página

  function captureGPS() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      pos => { gpsCache = { lat: pos.coords.latitude, lon: pos.coords.longitude }; },
      () => {},
      { timeout: 8000, maximumAge: 120000, enableHighAccuracy: false }
    );
  }

  function injectGPS(form) {
    if (!gpsCache) return;
    ['lat', 'lon'].forEach(k => {
      let el = form.querySelector(`input[name="${k}"]`);
      if (!el) {
        el = document.createElement('input');
        el.type = 'hidden';
        el.name = k;
        form.appendChild(el);
      }
      el.value = gpsCache[k];
    });
  }

  // ── Toast de feedback ─────────────────────────────────────
  function toast(msg) {
    let t = document.getElementById('_oq_toast');
    if (!t) {
      t = document.createElement('div');
      t.id = '_oq_toast';
      t.style.cssText = [
        'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);z-index:99999',
        'background:rgba(16,185,129,.97);color:#fff;border-radius:12px',
        'padding:10px 22px;font-size:12px;font-weight:700;letter-spacing:.04em',
        'font-family:Inter,sans-serif;box-shadow:0 8px 28px rgba(0,0,0,.18)',
        'display:flex;align-items:center;gap:8px;transition:opacity .4s',
      ].join(';');
      document.body.appendChild(t);
    }
    t.innerHTML = '&#10003; ' + msg;
    t.style.opacity = '1';
    clearTimeout(t._t);
    t._t = setTimeout(() => { t.style.opacity = '0'; }, 3200);
  }

  // ── Sincronização da fila ─────────────────────────────────
  async function flushQueue() {
    if (!navigator.onLine) return;
    const items = await dbAll();
    for (const item of items) {
      try {
        const fd = new FormData();
        for (const [k, v] of Object.entries(item.data.fields)) fd.append(k, v);
        for (const [k, f] of Object.entries(item.data.files || {})) {
          const res  = await fetch(f.dataURL);
          const blob = await res.blob();
          fd.append(k, new File([blob], f.name, { type: f.type }));
        }
        const res = await fetch(item.url, { method: 'POST', body: fd, redirect: 'follow' });
        if (res.ok || res.redirected || res.status < 500) {
          await dbRemove(item.id);
        }
      } catch {
        break; // ainda sem internet, tenta depois
      }
    }
  }

  // ── Interceptar formulários de PONTO ──────────────────────
  function interceptPonto() {
    document.querySelectorAll('.ponto-form').forEach(form => {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const horaInput = form.querySelector('input[name="hora"]');
        if (!horaInput || !horaInput.value) return;
        const hora = horaInput.value;

        // Injeta GPS (capturado no carregamento)
        injectGPS(form);

        if (navigator.onLine) {
          // Online: envia normalmente
          form.submit();
          return;
        }

        // Offline: salva na fila
        const data = await serializeForm(form);
        await dbAdd({ url: window.location.href, data, ts: Date.now() });

        // Atualiza UI: mostra hora e trava o campo
        const item = form.closest('.ponto-item');
        if (item) {
          const horaEl = document.createElement('div');
          horaEl.className = 'ponto-hora';
          horaEl.textContent = hora;
          form.replaceWith(horaEl);
          item.classList.add('ponto-ok');
        }

        toast('Ponto registrado');

        // Solicita Background Sync
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.ready.then(sw => {
            if ('sync' in sw) sw.sync.register('flush-queue').catch(() => {});
          }).catch(() => {});
        }
      });
    });
  }

  // ── Interceptar formulário de GASTO ───────────────────────
  function interceptGasto() {
    const form = document.querySelector('[data-offline-gasto]');
    if (!form) return;
    form.addEventListener('submit', async function (e) {
      if (navigator.onLine) return; // online: deixa ir
      e.preventDefault();

      const data = await serializeForm(form);
      await dbAdd({ url: window.location.href, data, ts: Date.now() });
      toast('Gasto salvo — enviando quando online');

      setTimeout(() => window.history.back(), 2200);

      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(sw => {
          if ('sync' in sw) sw.sync.register('flush-queue').catch(() => {});
        }).catch(() => {});
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────
  captureGPS(); // começa a capturar GPS imediatamente

  window.addEventListener('online', flushQueue);

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', ev => {
      if (ev && ev.data && ev.data.type === 'FLUSH') flushQueue();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    interceptPonto();
    interceptGasto();
    flushQueue(); // tenta sincronizar ao carregar
  });

})();