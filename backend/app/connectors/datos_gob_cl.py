"""
Conector para datasets de datos.gob.cl (portal de datos abiertos de
Chile, basado en CKAN).

A diferencia de OSM/Places, acá no hay una API uniforme de negocios
para consultar en vivo — lo que existe son datasets estáticos
publicados por cada municipalidad (por ejemplo, patentes comerciales
vigentes), cada uno con sus propias columnas. Por eso este conector
no asume un formato fijo: el preset debe indicar la URL del recurso
CSV y el mapeo de columnas.

Cómo encontrar un dataset:
  1. Buscar en https://datos.gob.cl (ej: "patentes comerciales
     Providencia") o usar la API de búsqueda:
     https://datos.gob.cl/api/3/action/package_search?q=patentes+comerciales
  2. Dentro del dataset, copiar la URL de descarga directa del
     recurso CSV (no la página del dataset).
  3. Revisar los nombres de las columnas del CSV (abriéndolo una vez)
     y completarlos en 'columnas'.

Parámetros esperados en el preset (parametros JSON):
    {
        "resource_url": "https://datos.gob.cl/dataset/.../download/patentes.csv",
        "comuna": "Providencia",
        "columnas": {
            "nombre": "RAZON_SOCIAL",     # nombre real de la columna en ESE csv
            "direccion": "DIRECCION",     # opcional
            "rubro": "GIRO",              # opcional
            "telefono": "TELEFONO"        # opcional, muchos datasets municipales no lo traen
        }
    }

Nota: estos datasets casi nunca incluyen si el negocio tiene sitio
web — por diseño acá 'tiene_web' siempre queda en None (no
determinado), no en False. La ventaja de esta fuente no es saber
quién tiene web, sino tener una lista de negocios con patente
vigente (más "oficial" que OSM) para cruzar con las otras fuentes o
revisar manualmente.

Esta fuente no tiene 'verificar()' — es una foto estática del CSV
publicado, no algo que se pueda re-consultar registro por registro.
El proceso de refresco simplemente la salta (queda contabilizada
como 'sin_verificador').
"""
import csv
import io

import httpx


def buscar(parametros: dict) -> list[dict]:
    resource_url = parametros.get("resource_url")
    comuna = parametros.get("comuna")
    columnas = parametros.get("columnas") or {}

    if not resource_url:
        raise ValueError("El preset necesita 'resource_url' (URL de descarga directa del CSV)")
    if not comuna:
        raise ValueError("El preset necesita 'comuna'")
    if not columnas.get("nombre"):
        raise ValueError("El preset necesita 'columnas.nombre' (el nombre de la columna con el nombre del negocio en ESE csv)")

    response = httpx.get(resource_url, timeout=30, follow_redirects=True)
    response.raise_for_status()

    # Los CSV de portales gubernamentales chilenos suelen venir en
    # latin-1 en vez de utf-8 — se intenta utf-8 primero y se cae a
    # latin-1 si falla, en vez de asumir uno solo.
    try:
        texto = response.content.decode("utf-8")
    except UnicodeDecodeError:
        texto = response.content.decode("latin-1")

    lector = csv.DictReader(io.StringIO(texto))

    leads = []
    for i, fila in enumerate(lector):
        nombre = (fila.get(columnas["nombre"]) or "").strip()
        if not nombre:
            continue

        leads.append({
            # No hay un ID único confiable entre datasets distintos,
            # así que se arma uno propio a partir de la fuente +
            # comuna + posición en el archivo. No sirve para dedup
            # entre corridas si el municipio reordena el CSV — es una
            # limitación conocida de esta fuente, no un bug.
            "source_id": f"{comuna}:{i}",
            "nombre": nombre,
            "rubro": fila.get(columnas.get("rubro", "")) if columnas.get("rubro") else None,
            "comuna": comuna,
            "direccion": fila.get(columnas.get("direccion", "")) if columnas.get("direccion") else None,
            "telefono": fila.get(columnas.get("telefono", "")) if columnas.get("telefono") else None,
            "tiene_web": None,  # este tipo de dataset no lo informa
            "website_url": None,
        })
    return leads
