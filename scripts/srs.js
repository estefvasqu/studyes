// Algoritmo SM-2. next_review se guarda como string YYYY-MM-DD.
// Los JSONs iniciales usan next_review=0 (número); isDue maneja ambos formatos.

const SRS = (() => {

  function isDue(card) {
    const srs = card.srs || {};
    if (!srs.next_review) return true;
    if (typeof srs.next_review === 'number') {
      return srs.next_review === 0 || Date.now() >= srs.next_review;
    }
    // date string YYYY-MM-DD — lexicographic comparison es suficiente
    const today = new Date().toISOString().split('T')[0];
    return srs.next_review <= today;
  }

  // calidad: 1 = no lo sabía, 3 = con dificultad, 5 = lo sabía
  function actualizarSRS(card, calidad) {
    if (!card.srs) card.srs = {};
    const s = card.srs;

    // migrar campo legacy si existe
    if (s.easeFactor !== undefined && s.easiness_factor === undefined) {
      s.easiness_factor = s.easeFactor;
      delete s.easeFactor;
    }
    if (s.easiness_factor === undefined) s.easiness_factor = 2.5;
    if (s.interval      === undefined) s.interval      = 1;
    if (s.repetitions   === undefined) s.repetitions   = 0;

    if (calidad >= 3) {
      if      (s.repetitions === 0) s.interval = 1;
      else if (s.repetitions === 1) s.interval = 6;
      else                          s.interval = Math.round(s.interval * s.easiness_factor);
      s.repetitions += 1;
    } else {
      s.repetitions = 0;
      s.interval    = 1;
    }

    s.easiness_factor = Math.max(
      1.3,
      s.easiness_factor + 0.1 - (5 - calidad) * (0.08 + (5 - calidad) * 0.02)
    );

    const fecha = new Date();
    fecha.setDate(fecha.getDate() + s.interval);
    s.next_review = fecha.toISOString().split('T')[0];

    return card;
  }

  return { isDue, actualizarSRS };
})();
