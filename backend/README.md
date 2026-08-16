# LeadGen backend

Herramienta centralizada de lead-gen para negocios chilenos sin sitio
web. Reemplaza a LeadHunter — misma idea, arrancando de cero porque
ninguno de sus scrapers entregaba datos confiables.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# completar GOOGLE_PLACES_API_KEY en .env
# (Google Cloud Console → habilitar "Places API (New)")

uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000`. Docs interactivas en
`http://localhost:8000/docs`.

## Fuentes disponibles

- **`osm_overpass`** — OpenStreetMap vía Overpass API. **Gratis, sin
  API key.** Punto de partida recomendado para validar el sistema
  sin costo. Cobertura despareja según qué tan mapeada esté la zona
  en OSM — por eso conviene validar una muestra antes de escalar.
- **`google_places`** — Google Places API (New). De pago (tiene
  cuota gratuita mensual en Google Cloud, después cobra por
  request). Cobertura más completa y consistente. Requiere
  `GOOGLE_PLACES_API_KEY` en `.env`.

## Flujo de uso

1. **Crear un preset de búsqueda** — define qué buscar y dónde.
   Con la fuente gratuita (OSM), los parámetros son `rubro_osm`
   (un tag de OpenStreetMap — ver ejemplos en
   [taginfo.openstreetmap.org](https://taginfo.openstreetmap.org),
   ej. `amenity=restaurant`, `shop=hairdresser`, `amenity=cafe`) y
   `comuna`:

   ```bash
   curl -X POST http://localhost:8000/presets -H "Content-Type: application/json" -d '{
     "nombre": "Restaurantes Providencia",
     "fuente": "osm_overpass",
     "parametros": {"rubro_osm": "amenity=restaurant", "comuna": "Providencia"}
   }'
   ```

   Con Places (`fuente: "google_places"`), los parámetros son
   `rubro` (texto libre), `comuna` y opcionalmente `radio_m`.

2. **Ejecutarlo** para capturar leads:

   ```bash
   curl -X POST http://localhost:8000/presets/1/ejecutar
   ```

3. **Consultar leads**, con los filtros que hagan falta:

   ```bash
   curl "http://localhost:8000/leads?comuna=Providencia&tiene_web=false"
   ```

   Importante: la captura **no descarta** los negocios que sí tienen
   web — se guardan todos, con `tiene_web` marcado. Los filtros se
   aplican aquí, al consultar, no en la captura. Así, si el público
   objetivo cambia con el tiempo, el dato ya está — no hay que volver
   a scrapear.

4. **Mover un lead en el pipeline**:

   ```bash
   curl -X PATCH http://localhost:8000/leads/1/estado -H "Content-Type: application/json" \
     -d '{"estado": "contactado", "notas": "Llamé, sin respuesta"}'
   ```

   Estados válidos: `nuevo`, `contactado`, `interesado`, `cliente`,
   `descartado`, `inactivo`.

5. **Refresco periódico** (para que los leads no se queden
   desactualizados): correrlo manualmente vía `POST /refresh`, o
   como cron nocturno:

   ```
   0 3 * * * /ruta/al/venv/bin/python -m app.refresh
   ```

   Cada corrida re-verifica el lote de leads con la
   `ultima_verificacion` más antigua (tamaño de lote configurable con
   `REFRESH_BATCH_SIZE`). Si un lead falla la verificación varias
   veces seguidas (`MAX_VERIFICATION_ATTEMPTS`), se marca `inactivo`
   en vez de seguir reintentando o de borrarse — mantiene el
   historial sin ensuciar la vista de leads activos.

## Cómo agregar una fuente nueva

1. Crear `app/connectors/<fuente>.py` con dos funciones:
   - `buscar(parametros: dict) -> list[dict]` — igual forma de salida
     que `google_places.buscar` (ver `app/connectors/base.py` para el
     contrato exacto).
   - `verificar(source_id: str) -> dict | None` — solo si la fuente
     admite re-consulta puntual; si no, se omite y esos leads
     simplemente no entran al refresco automático.
2. Registrarla en `app/connectors/__init__.py` (`CONECTORES_BUSQUEDA`)
   y, si tiene `verificar`, en `app/refresh.py` (`VERIFICADORES`).
3. Nada más cambia — `crud.py`, `main.py` y el schema son agnósticos
   a la fuente.

No hay una interfaz abstracta forzada a propósito: con una sola
fuente en producción no vale la pena adivinar cómo va a lucir una
segunda. Cuando aparezca, ahí se decide qué realmente conviene
compartir.

## Estructura

```
app/
  config.py           # variables de entorno
  database.py          # conexión SQLite + init desde schema.sql
  schema.sql            # schema completo (leads + search_presets)
  crud.py               # todas las operaciones de DB
  models.py             # schemas Pydantic (request/response)
  refresh.py            # proceso de re-verificación periódica
  main.py               # endpoints FastAPI
  connectors/
    base.py              # contrato que debe cumplir un conector
    google_places.py     # primera fuente implementada
```
