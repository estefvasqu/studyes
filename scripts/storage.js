const Storage = (() => {

  // ── Detección de servidor local ────────────────────────────────
  let _servidorLocal = null;

  async function hayServidorLocal() {
    if (_servidorLocal !== null) return _servidorLocal;
    try {
      const res = await fetch('/ping', { signal: AbortSignal.timeout(500) });
      _servidorLocal = res.ok;
    } catch {
      _servidorLocal = false;
    }
    return _servidorLocal;
  }

  // ── Carga (relativa — funciona en local y en Netlify) ──────────
  async function load(path) {
    const res = await fetch(`/data/${path}`);
    if (!res.ok) throw new Error(`No se pudo cargar: ${path}`);
    return res.json();
  }

  // ── Indicador de sincronización ────────────────────────────────
  let _fadeTimer = null;

  // state: 'syncing' | 'synced' | 'pending'
  // customMsg: texto opcional que reemplaza el default del estado
  // tooltip: texto para el atributo title (solo útil en 'pending')
  function _setStatus(state, customMsg, tooltip) {
    const el = document.getElementById('sync-indicator');
    if (!el) return;
    clearTimeout(_fadeTimer);
    el.dataset.state = state;
    el.title = tooltip || '';
    if (state === 'syncing') {
      el.textContent = customMsg || '⏳ sincronizando…';
    } else if (state === 'pending') {
      el.textContent = customMsg || '⚠ cambios sin sincronizar';
    } else if (state === 'synced') {
      el.textContent = customMsg || '✓ sincronizado';
      _fadeTimer = setTimeout(() => {
        if (el.dataset.state === 'synced') {
          el.dataset.state = '';
          el.textContent = '';
          el.title = '';
        }
      }, 4000);
    }
  }

  // ── SHA por archivo (localStorage) ────────────────────────────
  // Guarda el SHA del último commit conocido para cada path.
  // Evita re-pulls innecesarios al abrir la app tras un save propio.
  const SHA_KEY = 'studyes_sha_';

  function _storeSha(path, sha) {
    if (sha) localStorage.setItem(SHA_KEY + path, sha);
  }

  function _getStoredSha(path) {
    return localStorage.getItem(SHA_KEY + path);
  }

  // ── Cola de reintentos (localStorage) ─────────────────────────
  const QUEUE_KEY = 'studyes_sync_queue';

  function _enqueue(path, data) {
    const q    = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
    const rest = q.filter(item => item.path !== path);
    rest.push({ path, data });
    localStorage.setItem(QUEUE_KEY, JSON.stringify(rest));
  }

  function _dequeue(path) {
    const q = JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
    localStorage.setItem(QUEUE_KEY, JSON.stringify(q.filter(item => item.path !== path)));
  }

  function _getPending() {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
  }

  // ── Sync a GitHub via servidor local (/github-sync) ───────────
  // Devuelve el SHA del commit creado, o null si no lo pudo obtener.
  async function _syncLocal(path, data) {
    const res = await fetch('/github-sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, data }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `github-sync ${res.status}`);
    }
    const json = await res.json();
    return json.sha || null;
  }

  // ── Sync a GitHub via Netlify Function (/netlify-save) ────────
  // Devuelve el SHA del commit creado, o null.
  async function _syncNetlify(path, data) {
    const res = await fetch('/netlify-save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: `data/${path}`, data }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || res.status);
    }
    const json = await res.json();
    return json.sha || null;
  }

  // ── Background sync después del write local ────────────────────
  async function _bgSync(path, data) {
    _setStatus('syncing');
    try {
      const sha = await _syncLocal(path, data);
      _storeSha(path, sha);
      _dequeue(path);
      if (_getPending().length === 0) _setStatus('synced');
    } catch {
      _enqueue(path, data);
      _setStatus('pending');
    }
  }

  // ── Drenar cola de reintentos (llamar al cargar la página) ─────
  async function drainQueue() {
    const pending = _getPending();
    if (pending.length === 0) return;
    if (!(await hayServidorLocal())) return;
    _setStatus('syncing');
    for (const item of pending) {
      try {
        const sha = await _syncLocal(item.path, item.data);
        _storeSha(item.path, sha);
        _dequeue(item.path);
      } catch {
        _setStatus('pending');
        return;
      }
    }
    if (_getPending().length === 0) _setStatus('synced');
  }

  // ── Sincronización desde GitHub al arrancar ────────────────────
  // Solo actúa en modo servidor local. En Netlify el deploy ya es
  // la versión más reciente, así que no hay nada que hacer.
  // Devuelve { updated: true } si descargó una versión nueva del
  // archivo desde GitHub y la escribió en disco.
  async function syncFromGitHub(path) {
    if (!(await hayServidorLocal())) return { updated: false };

    try {
      // 1. Consultar el SHA del último commit que tocó este archivo
      const shaRes = await fetch(
        `/github-latest-sha?path=${encodeURIComponent(path)}`,
        { signal: AbortSignal.timeout(4000) }
      );
      if (!shaRes.ok) throw new Error(`github-latest-sha ${shaRes.status}`);
      const { sha: remoteSha } = await shaRes.json();

      if (!remoteSha) return { updated: false };

      const storedSha = _getStoredSha(path);
      if (remoteSha === storedSha) return { updated: false };

      // 2. SHA distinto → descargar y sobreescribir en disco
      const pullRes = await fetch('/github-pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
        signal: AbortSignal.timeout(8000),
      });
      if (!pullRes.ok) throw new Error(`github-pull ${pullRes.status}`);
      const { sha: newSha } = await pullRes.json();

      _storeSha(path, newSha || remoteSha);
      _setStatus('synced', '✓ Actualizado desde GitHub');
      return { updated: true };

    } catch {
      // No bloquear el arranque — mostrar advertencia pasiva
      _setStatus('pending', '⚠ sin verificar sync',
        'No se pudo verificar sincronización con GitHub');
      return { updated: false };
    }
  }

  // ── save: escribe local (rápido) + sync GitHub (background) ───
  async function save(path, data) {
    if (await hayServidorLocal()) {
      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, data }),
      });
      if (!res.ok) throw new Error(`No se pudo guardar: ${path}`);
      _bgSync(path, data); // disparo sin await
      return res.json();
    } else {
      _setStatus('syncing');
      try {
        const sha = await _syncNetlify(path, data);
        _storeSha(path, sha);
        _setStatus('synced');
      } catch (err) {
        _setStatus('pending');
        throw err;
      }
    }
  }

  return { load, save, drainQueue, syncFromGitHub };
})();
