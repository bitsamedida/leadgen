# LeadGen — Contexto del proyecto

> Propósito de este documento: pegarlo en un chat nuevo (o adjuntar el archivo) para que Claude tenga contexto completo del proyecto sin tener que explicarlo todo de nuevo.

## Qué es esto

Una herramienta centralizada de generación de leads para encontrar negocios chilenos sin sitio web — reemplaza un proyecto anterior ("LeadHunter") cuyos scrapers nunca devolvían datos de forma confiable. Se construyó desde cero en vez de parchado, para no arrastrar los errores del sistema anterior.

**Dueño:** V, desarrollador web freelance en Chile (WordPress/WooCommerce, migraciones de servidor, herramientas a medida). Normalmente recibe clientes de forma entrante; esta herramienta es para generar contacto proactivo y hacer crecer ese flujo.

## Por qué existe

El enfoque original era un scraper directo contra Google Maps, más algunas otras fuentes (Páginas Amarillas, MercadoLibre, Instagram/OSM). Nada funcionaba bien — escaneos incompletos, datos poco confiables, sin forma real de saber si un "lead" era un negocio activo y contactable. En vez de depurar cuatro scrapers rotos, se decidió empezar de nuevo con una sola fuente funcionando de punta a punta antes de sumar más.

## Requisitos de diseño centrales (definieron cada decisión de arquitectura de abajo)

1. **Configurabilidad antes que valores fijos.** Los parámetros de búsqueda y los filtros deben ser fáciles de cambiar — el público objetivo/criterios pueden cambiar con el tiempo, y nada debe quedar fijo en el código de forma que obligue a reescribirlo para ajustarlo.
2. **Nunca perder un lead en silencio.** El filtrado (por estado de sitio web, categoría, etc.) ocurre al consultar, no al capturar. Todo lo que se encuentra se guarda; lo que se *muestra* depende del filtro actual.
3. **Sin acumulación de datos obsoletos.** Los leads deben re-verificarse periódicamente contra su fuente, no capturarse una vez y quedar sin revisión. Los leads que fallan la verificación repetidamente se marcan como inactivos (no se borran — se conserva el historial).
4. **Reutilizar sin sobre-diseñar.** Compartir lógica entre fuentes de datos donde sea simple y evidente (el schema de leads, el pipeline de estados, el mecanismo de refresco). No forzar una abstracción para lógica específica de una fuente (llamadas a API, parseo) hasta que exista una segunda fuente real para comparar.

## Arquitectura

**Stack:** backend FastAPI + SQLite, frontend React (Vite) — mismo stack que el proyecto LeadHunter anterior, mantenido por familiaridad.

### Modelo de datos
- `leads` — schema unificado sin importar la fuente: nombre, categoría (`rubro`), comuna, dirección, teléfono, `tiene_web` (booleano nullable — null significa "aún no determinado", no "no tiene"), URL del sitio, `estado` del pipeline de ventas, timestamps de verificación, `intentos_verificacion` (contador de fallos).
- `search_presets` — búsquedas guardadas y reutilizables. Cada uno tiene una `fuente` (nombre de la fuente) y un campo `parametros` en JSON libre — deliberadamente no son columnas fijas, porque cada fuente necesita una forma distinta de parámetros (Places usa categoría+comuna+radio, OSM usa un tag de OSM+comuna, datos.gob.cl usa una URL de CSV + mapeo de columnas).

### Patrón de conectores
Cada fuente de datos es un módulo independiente con dos funciones:
- `buscar(parametros) -> list[dict]` — ejecuta una búsqueda, devuelve leads en la forma unificada.
- `verificar(source_id) -> dict | None` — re-consulta un lead existente; `None` significa que ya no existe en la fuente.

Las fuentes nuevas se registran en un diccionario (`CONECTORES_BUSQUEDA` en `connectors/__init__.py`, `VERIFICADORES` en `refresh.py`) — nada más del sistema necesita cambiar. No se forzó una clase base abstracta prematuramente; eso se revisa si en algún momento hace falta.

### Pipeline / ciclo de vida
`estado` avanza por: `nuevo → contactado → interesado → cliente` (o `descartado`). Los leads que fallan la re-verificación repetidamente pasan a `inactivo`.

### Mecanismo de refresco
Un proceso por lotes (`app/refresh.py`, ejecutable manualmente vía `POST /refresh` o como cron nocturno) toma los leads con la `ultima_verificacion` más antigua primero, re-consulta su fuente, y los actualiza o incrementa su contador de fallos. Tras `MAX_VERIFICATION_ATTEMPTS` (3 por defecto) fallos seguidos, un lead se marca `inactivo` en vez de borrarse.

### Validación automática de calidad (nueva)
Un módulo (`app/validacion.py`) calcula, al consultar `/leads`, una lista de advertencias por lead (sin teléfono, teléfono con formato inválido, sin dirección, sin determinar si tiene web, nombre sospechosamente corto) y un porcentaje de "completitud". **Importante: esto no confirma que un negocio existe de verdad** — es un filtro automático de primera pasada para priorizar qué revisar a mano, no un reemplazo del criterio humano. Se puede filtrar la lista de leads para ver solo los que tienen advertencias (`solo_con_advertencias=true`), ordenados por menor completitud primero.

## Fuentes de datos implementadas

| Fuente | Estado | Costo | Notas |
|---|---|---|---|
| `osm_overpass` (OpenStreetMap / Overpass API) | **Fuente principal actual** | Gratis, sin API key | Cobertura depende de qué tan mapeada esté la zona en OSM. Resuelve ciudad/comuna → área vía Nominatim; incluye opción de buscar en todo Chile. Tuvo dos bugs ya corregidos: la fórmula del area_id estaba mal calculada, y Nominatim a veces devuelve un punto (node) en vez de un área para nombres de ciudad ambiguos (ej. "Santiago") — ya maneja ambos casos. |
| `google_places` (Google Places API, New) | Construido, disponible, no en uso actualmente | De pago — según investigación reciente del usuario, subió fuertemente de precio en 2026 (tier básico ~$275 USD/mes) | Se dejó de usar como fuente inicial por costo. Sigue en el código como opción futura de verificación puntual, no de barrido masivo. |
| `datos_gob_cl` (portal de datos abiertos de Chile, basado en CKAN) | Construido, requiere configuración manual por dataset | Gratis | Conector genérico para CSVs publicados por organismos chilenos — el usuario debe indicar la URL del recurso y el mapeo de columnas en el preset, porque cada dataset tiene su propio formato. No tiene `verificar()` (es una foto estática). Candidato concreto a configurar: el dataset "Registro de Empresas y Sociedades" (constituciones bajo Ley 20.659), identificado en la investigación del usuario. |

Decisión tomada: **validar con una fuente gratis antes de sumar más o pagar por algo.**

## Investigación adicional del usuario (fuentes evaluadas, no todas implementadas)

El usuario compartió un documento propio de investigación sobre fuentes para Chile. Puntos relevantes para las próximas decisiones:

- **SRE.cl** — API con token gratuito (`token_publico`, reportado ~200 consultas/día) que entrega **RUT**, razón social, giro, dirección por comuna. El RUT importa porque permitiría deduplicación robusta entre fuentes (hoy el dedup es por nombre/dirección normalizados, mucho menos confiable) — es el candidato más fuerte para la próxima fuente a construir. No implementado todavía.
- **API Mercado Público (ChileCompra)** — licitaciones/proveedores del Estado, más orientado a leads B2B. Ya se había descartado antes como fuente de directorio general (no expone perfiles de empresa navegables fácilmente), pero el documento confirma que sigue siendo válida para ese nicho específico.
- **BizData** — proyecto no oficial, sin garantías de continuidad. Marcado como complementario, no crítico, si se llega a usar.
- **Redes sociales (Instagram/Facebook)** — señal fuerte de "sin sitio web propio" en pymes chilenas, pero la Graph API de Meta no permite prospección masiva por ubicación/rubro. Sin plan concreto de implementación.
- **Scoring de sitios "anticuados"** (PageSpeed Insights API + chequeos propios de HTTPS/responsive/tecnología obsoleta) — esto es una **expansión real del objetivo del proyecto**, no una fuente más: hasta ahora el proyecto solo busca negocios *sin* web; esto agrega detectar negocios *con* web pero desactualizada. Discutido, no implementado, no priorizado todavía.
- Nota legal marcada por el usuario para tener en cuenta más adelante: Ley 19.628 de protección de datos personales en Chile aplica al almacenar datos de contacto — revisar antes de escalar el uso comercial de los datos.

**Pendiente de decisión (así quedó la conversación):** el usuario preguntó por dónde seguir entre (a) conector SRE.cl, (b) configurar datos_gob_cl con el dataset de Registro de Empresas, (c) scoring de sitios anticuados, (d) primero validar lo que ya existe — sin responder todavía al momento de escribir este documento.

## Estado de la construcción (a la fecha de este documento)

- ✅ Backend: schema, capa de DB, CRUD (dedup por `source, source_id`), tres conectores (`osm_overpass`, `google_places`, `datos_gob_cl`), lógica de refresco, validación automática de calidad, edición y borrado de presets (con `ON DELETE SET NULL` para no perder leads al borrar un preset) — todo probado contra SQLite real, no solo escrito.
- ✅ Frontend: app básica Vite+React — gestión de presets (crear/ejecutar/pausar/editar/borrar), **plantillas predefinidas** de presets comunes (8 rubros vía OSM) para reducir la fricción de armar uno desde cero, tabla de leads con filtros (comuna, rubro, estado, tiene_web, solo-con-advertencias) y cambios de estado inline. **Explícitamente un placeholder** — funcional pero sin diseño real, eso se planea para después. Se corrigió un bug donde crear/editar un preset fallaba en silencio si la petición fallaba (ahora muestra el error).
- ✅ Español del proyecto (interfaz y mensajes de error) neutralizado — sin modismos chilenos ni voseo.
- ⚠️ Datos ya fluyendo con OSM (el usuario confirmó que está obteniendo resultados), pero **todavía no se hizo la validación manual de una muestra** (el paso "revisar 20-30 leads a mano" del plan original sigue pendiente).
- ⚠️ El frontend nunca se corrió con `npm install` en el entorno de construcción (sin acceso a registries ahí) — escrito con cuidado pero no probado en vivo; en una máquina normal debería andar sin problema.

## Roadmap / próximos objetivos

1. **Validar la fuente OSM con una muestra real** (sigue pendiente pese a que ya hay datos entrando — ver "Pendiente de decisión" arriba).
2. **Conector SRE.cl** — probablemente la próxima fuente a construir, por el valor del RUT para deduplicación.
3. **Configurar `datos_gob_cl`** con el dataset de Registro de Empresas y Sociedades (constituciones nuevas — leads "frescos").
4. **Outreach** — el paso de contacto (definir canal, WhatsApp Business API fue la opción más mencionada, y conectarlo al estado `contactado`) no está construido todavía.
5. **Rediseño del frontend** — se pospuso a propósito hasta validar el flujo completo con datos reales.
6. **Scoring de sitios "anticuados"** (PageSpeed + chequeos propios) — expansión de objetivo, discutida pero no priorizada.
7. **Más largo plazo, sin prioridad aún:** modelo de scoring de leads (el schema ya reserva un campo `score` sin usar), vista tipo kanban del pipeline en el frontend (hoy es un dropdown por fila).

## Decidido explícitamente en contra (para que no se vuelva a discutir)

- Extender el código de LeadHunter — abandonado directamente, no arreglado de a poco.
- Una interfaz de conector genérica/abstracta antes de que existiera una segunda fuente real que la justificara.
- Filtrar negocios "con sitio web" al momento de capturar — todo se guarda, el filtrado es solo al consultar.
- Empezar con varias fuentes a la vez — deliberadamente una por vez, validada antes de la siguiente.
