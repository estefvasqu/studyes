// Planificación de sesión diaria con límite de cards por materia

const Plan = (() => {
  const LIMITE_DIARIO = 8;

  /**
   * Devuelve hasta `limitePorDia` cards pendientes para hoy.
   * Si limitePorDia === 'todas', no aplica límite.
   * Ordena: temas prioritarios primero, luego next_review más antiguo, luego repetitions=0.
   */
  function seleccionarHoy(cards, limitePorDia, prioridades) {
    const prios  = prioridades || [];
    const limite = limitePorDia === 'todas' ? Infinity
                 : (Number(limitePorDia) > 0) ? Number(limitePorDia)
                 :                              LIMITE_DIARIO;

    const pendientes = cards.filter(c => SRS.isDue(c));

    pendientes.sort((a, b) => {
      const aPrio = prios.includes(a.tema) ? 0 : 1;
      const bPrio = prios.includes(b.tema) ? 0 : 1;
      if (aPrio !== bPrio) return aPrio - bPrio;
      const ra = String(a.srs?.next_review ?? '');
      const rb = String(b.srs?.next_review ?? '');
      if (ra !== rb) return ra < rb ? -1 : 1;
      return (a.srs?.repetitions ?? 0) - (b.srs?.repetitions ?? 0);
    });

    return pendientes.slice(0, limite);
  }

  return { seleccionarHoy, LIMITE_DIARIO };
})();
