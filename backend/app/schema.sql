-- ============================================================
-- Schema inicial: herramienta de lead-gen centralizada
-- Diseño: agnóstico a fuente, con presets reutilizables y
-- soporte para re-verificación periódica de leads existentes.
-- ============================================================

-- Búsquedas guardadas (search presets).
-- 'parametros' es JSON libre a propósito: cada fuente tiene su
-- propia forma de parámetros (Places usa rubro+comuna+radio,
-- un dataset de patentes puede usar solo comuna+categoría).
-- Esto evita forzar un schema común artificial entre fuentes
-- distintas, respetando "no abstraer antes de tiempo".
CREATE TABLE search_presets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT NOT NULL,              -- ej: "Restaurantes Providencia"
    fuente              TEXT NOT NULL,               -- ej: "google_places"
    parametros          TEXT NOT NULL,               -- JSON: {"rubro": "...", "comuna": "...", "radio_m": 3000}
    activo              INTEGER NOT NULL DEFAULT 1,  -- 0/1 (pausar sin borrar)
    fecha_creacion      TEXT NOT NULL DEFAULT (datetime('now')),
    ultima_ejecucion    TEXT                         -- última vez que este preset corrió (captura o refresco)
);

-- Leads: schema unificado, independiente de la fuente que los originó.
CREATE TABLE leads (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificación de origen
    source                  TEXT NOT NULL,           -- ej: "google_places"
    source_id               TEXT,                    -- id externo (place_id de Google, etc.) — usado para dedup
    preset_id               INTEGER REFERENCES search_presets(id) ON DELETE SET NULL,

    -- Datos del negocio
    nombre                  TEXT NOT NULL,
    rubro                   TEXT,
    comuna                  TEXT,
    direccion               TEXT,
    telefono                TEXT,
    tiene_web               INTEGER,                 -- 0/1/NULL (NULL = no determinado aún)
    website_url             TEXT,

    -- Pipeline de ventas
    estado                  TEXT NOT NULL DEFAULT 'nuevo',
                             -- nuevo | contactado | interesado | cliente | descartado | inactivo
    score                   INTEGER,                 -- reservado para cuando se reactive el scoring
    notas                   TEXT,

    -- Ciclo de vida / refresco (para que no se acumulen entradas viejas sin revisar)
    fecha_captura           TEXT NOT NULL DEFAULT (datetime('now')),
    ultima_verificacion     TEXT NOT NULL DEFAULT (datetime('now')),
    intentos_verificacion   INTEGER NOT NULL DEFAULT 0,  -- se incrementa cuando el negocio no aparece más en la fuente

    UNIQUE (source, source_id)  -- evita duplicados dentro de una misma fuente
);

-- Acelera la query del proceso de refresco: "traer los N leads
-- activos con la verificación más antigua primero".
CREATE INDEX idx_leads_refresco
    ON leads (estado, ultima_verificacion)
    WHERE estado != 'inactivo';

-- Filtros típicos de la vista principal (por comuna/rubro/estado).
CREATE INDEX idx_leads_filtros
    ON leads (comuna, rubro, estado);
