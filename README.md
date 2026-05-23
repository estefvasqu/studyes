# StudyES — FCE UBA

App web local de estudio con repetición espaciada.

## Arrancar

```
start.bat
```

O manualmente:
```
python server.py
```
Abrir http://localhost:8000

## Estructura

| Archivo/Carpeta | Descripción |
|---|---|
| `server.py` | Servidor estático + endpoint POST `/save` |
| `data/materias.json` | Lista de materias |
| `data/flashcards/` | Tarjetas por materia |
| `data/progreso/` | Estado SRS por materia |
| `scripts/srs.js` | Algoritmo SM-2 |
| `scripts/storage.js` | Lectura/escritura via servidor |
| `scripts/plan.js` | Planificación de repaso |
