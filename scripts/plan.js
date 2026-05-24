const Plan = (() => {

  function getCardsDeHoy(todasLasCards, cardsPorDia) {
    const hoy = new Date().toISOString().split('T')[0];

    const pendientes = todasLasCards
      .filter(c => {
        const nr = c.srs?.next_review;
        if (!nr || nr === 0) return true;   // card nueva, siempre pendiente
        return String(nr) <= hoy;
      })
      .sort((a, b) => {
        // next_review === 0 o ausente → string vacío → ordena primero
        const ra = (!a.srs?.next_review || a.srs.next_review === 0) ? '' : String(a.srs.next_review);
        const rb = (!b.srs?.next_review || b.srs.next_review === 0) ? '' : String(b.srs.next_review);
        return ra.localeCompare(rb);
      });

    if (cardsPorDia === 'todas' || cardsPorDia === Infinity) {
      return pendientes;
    }
    const n = Number(cardsPorDia);
    return pendientes.slice(0, n > 0 ? n : 8);
  }

  return { getCardsDeHoy };
})();
