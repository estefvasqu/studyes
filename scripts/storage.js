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

  // ── Guardar via GitHub API (celu / Netlify) ────────────────────
  async function guardarEnGitHub(rutaArchivo, contenido) {
    const config = await fetch('/config/settings.json').then(r => r.json());
    const url = `https://api.github.com/repos/${config.github_user}/${config.github_repo}/contents/data/${rutaArchivo}`;

    const actual = await fetch(url, {
      headers: { 'Authorization': `token ${config.github_token}` },
    }).then(r => r.json());

    const body = JSON.stringify({
      message: `StudyES: actualizar ${rutaArchivo}`,
      content: btoa(unescape(encodeURIComponent(
        JSON.stringify(contenido, null, 2)
      ))),
      sha: actual.sha,
      branch: config.github_branch || 'main',
    });

    const res = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${config.github_token}`,
        'Content-Type': 'application/json',
      },
      body,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(`GitHub API error: ${err.message || res.status}`);
    }
  }

  // ── Guardar: local si hay servidor, GitHub si no ──────────────
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
      await guardarEnGitHub(path, data);
    }
  }

  return { load, save };
})();
