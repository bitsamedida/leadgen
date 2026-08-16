# LeadGen frontend (básico)

Interfaz mínima para gestionar presets y revisar leads — pensada para
usar el backend, no para ser el diseño final (eso se rehace después).
Reusa la estética terminal de tus otros proyectos (fondo oscuro,
monospace, sin Tailwind) solo para que sea usable mientras tanto.

## Setup

Con el backend corriendo en `http://localhost:8000` (ver
`../backend/README.md`):

```bash
npm install
npm run dev
```

Abre en `http://localhost:5173`.

## Qué hace

- **Panel izquierdo**: crear presets, ejecutarlos (dispara la
  captura contra la fuente elegida), pausar/activar, y un botón para
  disparar el refresco manual de leads antiguos.
- **Panel principal**: tabla de leads con filtros por comuna, rubro,
  estado y si tiene web. Cambiar el estado de un lead es un select
  inline en cada fila.

## Qué falta (a propósito, para cuando se rediseñe)

- Sin paginación — trae hasta 200 leads por consulta.
- Sin vista de detalle por lead (notas, historial).
- Sin loading states prolijos ni manejo de errores más allá de un
  mensaje de texto simple.
- Sin vista tipo kanban del pipeline (por ahora es un select por
  fila).
