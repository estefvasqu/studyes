# CHECKPOINT — Etapa 5 COMPLETA

**Fecha:** 2026-05-23

## Estado: COMPLETO ✓

---

## Etapas completadas

### Etapa 1 — Estructura + servidor
Carpetas, server.py (estáticos + POST /save + GET /api/material + GET /material-file), start.bat, JSONs.

### Etapa 2 — Pantalla de inicio
index.html: grid de materias con badge de pendientes, progreso SRS, racha.

### Etapa 3 — Dashboard por materia
dashboard.html con 4 tabs (HOY / TEMAS / MATERIAL / AGREGAR). server.py con endpoints de material.

### Etapa 4 — Sesión de flashcards con SRS
flashcards.html: flip card 3D, SM-2, guardar progreso, pantalla de resumen.
srs.js y plan.js: límite 5 cards/día, criterio de selección por antigüedad + repetitions=0.

### Ajustes pre-Etapa 5
- Contador 📅 días al parcial en index.html (color dinámico verde/naranja/rojo)
- Tab GUÍA PRÁCTICA en dashboard (solo micro2): acordeón, ejercicios con check/nota/eliminar, agregar ejercicios
- Progreso de guía en tarjetas de index.html

### Etapa 5 — Pulido final + mapas mentales

**1. Badges en index.html:**
- 🔥 antes del número de días de racha cuando racha > 0
- Progreso de guía práctica ya estaba implementado desde Ajuste 3
- Badges sin caché (ya era el caso; sin service worker)

**2. Mapas Mentales en tab MATERIAL:**
- `server.py`: `.html` agregado a MIME_TYPES como `text/html; charset=utf-8`
- `dashboard.html tipoTag()`: reemplazado con emojis — 📄 PDF, 📝 DOC, 📊 PPT/XLS, 🗺 HTML, 📎 otros
- Archivos HTML de Mapas_Mentales se abren en nueva pestaña (target="_blank" ya estaba)
- `.mat-tipo` CSS reemplazado por `.mat-emoji`

**3. Íconos SVG en tab TEMAS:**
- `temaEstado()` ahora devuelve SVG inline para cada estado:
  - ✓ Dominado: círculo relleno #5C7A5E con check blanco
  - ◐ En progreso: semicírculo izquierdo #8B7355
  - ⚠ Débil: triángulo #B85C38 con ! blanco
  - ○ Sin practicar: círculo vacío #ACBAC4
- Icono ya no hereda color via CSS; color embebido en SVG
- `.tema-icono` CSS actualizado con `display:flex; align-items:center`

**4. Banner de bienvenida en index.html:**
- Aparece si hay cards pendientes Y el usuario no estudió todas las materias hoy
- Texto: "Buenos días Estef — tenés X cards para repasar hoy"
- Fondo #E1D9BC, texto #30364F, Jost 400
- Cierra con click en × (button con aria-label)

**5. Navegación fluida:**
- ← INICIO: href="index.html" ya correcto
- ← DASHBOARD: `dashboard.html?materia=${materiaId}` sin tab param → abre tab HOY
- Volver de flashcards a index recalcula badges automáticamente (no hay cache)
- `renderAgregar()` corregido: usa `easiness_factor` (no `easeFactor`) y `next_review: 0`

**6. Responsive básico:**
- `@media (max-width: 640px)`: tabs nav con overflow-x scroll, tab-btn sin wrap
- `@media (max-width: 480px)`: padding reducido, calificacion-btns en columna, btn-cal más alto, card-scene 300px

---

## Verificación manual recomendada

- [ ] index.html: banner aparece al cargar (sin haber estudiado hoy)
- [ ] index.html: 🔥 aparece en racha > 0 después de una sesión
- [ ] index.html: contador de días al parcial en ambas materias
- [ ] dashboard.html tab TEMAS: SVG icons para cada estado
- [ ] dashboard.html tab MATERIAL: emojis en lugar de badges de texto
- [ ] dashboard.html tab MATERIAL Mapas_Mentales: .html abre en nueva pestaña
- [ ] dashboard.html tab GUÍA PRÁCTICA: agregar ejercicio → check → nota → guardar
- [ ] dashboard.html tab AGREGAR: nueva card aparece en sesión
- [ ] flashcards.html: sesión completa → progreso guarda → racha actualiza
- [ ] mobile: tabs horizontalmente scrolleables, botones de calificación en columna

---

## Mejoras futuras sugeridas

1. **Keyboard shortcuts** — Espacio = flip, 1/3/5 = calificar, ← → = navegar
2. **Animación entre cards** — fade o slide al avanzar a la siguiente card
3. **Historial de sesiones** — gráfico de barras de sesiones recientes en dashboard
4. **Búsqueda de cards** — filtro por tema o texto en tab HOY y TEMAS
5. **Export/import** — backup y restauración de flashcards en JSON
6. **Modo oscuro** — toggle con CSS custom properties
7. **Notificaciones** — recordatorio al abrir si hay cards pendientes (ya existe el banner, pero push notification nativa sería más proactivo)
8. **Múltiples materias en una sola sesión** — sesión global con cards de todas las materias
9. **Estadísticas avanzadas** — curva de retención, easiness factor promedio por tema
10. **Segunda materia con guías** — añadir `tiene_guias: true` a Desarrollo Económico si se agregan guías prácticas
