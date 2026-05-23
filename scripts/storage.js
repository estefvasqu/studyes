// Capa de persistencia: lee/escribe JSONs via server.py (/save)

const Storage = (() => {
  const SERVER = 'http://localhost:8000';

  async function load(path) {
    const res = await fetch(`${SERVER}/data/${path}`);
    if (!res.ok) throw new Error(`No se pudo cargar: ${path}`);
    return res.json();
  }

  async function save(path, data) {
    const res = await fetch(`${SERVER}/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, data }),
    });
    if (!res.ok) throw new Error(`No se pudo guardar: ${path}`);
    return res.json();
  }

  return { load, save };
})();
