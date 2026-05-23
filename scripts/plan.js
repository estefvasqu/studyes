// Planificación de sesión diaria con límite de cards por materia

const Plan = (() => {
  const LIMITE_DIARIO = 5;

  /**
   * Devuelve hasta `limite` cards pendientes para hoy, ordenadas por:
   *  1. next_review más antigua (más atrasadas primero)
   *  2. Empate → repetitions = 0 primero (nunca vistas)
   */
  function seleccionarHoy(cards, limite = LIMITE_DIARIO) {
    const pendientes = cards.filter(c => SRS.isDue(c));

    pendientes.sort((a, b) => {
      const ra = String(a.srs?.next_review ?? '');
      const rb = String(b.srs?.next_review ?? '');
      if (ra !== rb) return ra < rb ? -1 : 1;
      // empate en fecha: primero las nunca vistas (repetitions = 0)
      return (a.srs?.repetitions ?? 0) - (b.srs?.repetitions ?? 0);
    });

    return pendientes.slice(0, limite);
  }

  return { seleccionarHoy, LIMITE_DIARIO };
})();
