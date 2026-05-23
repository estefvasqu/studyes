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

  // ── Guardar via Netlify Function (celu / Netlify) ──────────────
  async function guardarEnNetlify(path, data) {
    const res = await fetch('/netlify-save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: `data/${path}`, data }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(`Error al guardar: ${err.error || res.status}`);
    }
  }

  // ── Guardar: local si hay servidor, Netlify Function si no ─────
  async function save(path, data) {
    if (await hayServidorLocal()) {
      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, data }),
      });
      if (!res.ok) throw new Error(`No se pudo guardar: ${path}`);
      return res.json();
    } else {
      await guardarEnNetlify(path, data);
    }
  }

  return { load, save };
})();
