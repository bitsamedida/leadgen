"""
Conector de OpenStreetMap vía Overpass API.

Gratuito y sin API key — alternativa a google_places.py mientras se
valida el sistema sin costo. Cobertura de negocios en Chile es más
despareja que Places (depende de qué tan mapeada esté la zona), por
eso es justamente la primera fuente a validar con una muestra chica
antes de escalar.

Parámetros esperados en el preset (parametros JSON):
    {
        "rubro_osm": "amenity=restaurant",   # tag OSM del rubro (ver overpass docs / taginfo.openstreetmap.org)
        "comuna": "Providencia",             # se resuelve a un área vía Nominatim
    }
"""
import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim pide un User-Agent identificable — es requisito de su
# política de uso, no opcional.
HEADERS = {"User-Agent": "leadgen-tool/1.0 (uso personal, freelance CL)"}


def _area_id_comuna(ubicacion: str) -> int:
    """Resuelve un nombre de ciudad/comuna (o 'Chile' para el país
    completo) a un area_id de Overpass.

    Overpass calcula el area_id sumando una constante fija al ID de
    OSM, distinta según el tipo de elemento:
      - relation: area_id = relation_id + 3600000000
      - way:      area_id = way_id      + 2400000000
    (nodos no forman áreas). Una comuna/ciudad chilena, o el país
    completo, normalmente resuelve a una 'relation' (límite
    administrativo)."""
    query = ubicacion if ubicacion.strip().lower() == "chile" else f"{ubicacion}, Chile"
    # Se pide más de un resultado porque para nombres ambiguos (como
    # "Santiago") Nominatim a veces devuelve como primer resultado un
    # punto (node) en vez de la relación que define el área de la
    # ciudad — un node no puede formar un área en Overpass.
    params = {"q": query, "format": "json", "limit": 5, "countrycodes": "cl"}
    resp = httpx.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resultados = resp.json()
    if not resultados:
        raise ValueError(f"No se encontró '{ubicacion}' en OpenStreetMap")

    for resultado in resultados:
        osm_id = int(resultado["osm_id"])
        osm_type = resultado["osm_type"]
        if osm_type == "relation":
            return osm_id + 3600000000
        elif osm_type == "way":
            return osm_id + 2400000000

    raise ValueError(
        f"'{ubicacion}' solo resolvió a puntos (nodes) en OpenStreetMap, que no pueden "
        "formar un área. Prueba con el nombre exacto de la ciudad o comuna."
    )


def buscar(parametros: dict) -> list[dict]:
    rubro_osm = parametros.get("rubro_osm")
    comuna = parametros.get("comuna")
    todo_chile = parametros.get("todo_chile", False)

    if not rubro_osm:
        raise ValueError("El preset necesita 'rubro_osm' (ej: 'amenity=restaurant')")
    if not todo_chile and not comuna:
        raise ValueError("El preset necesita 'comuna' (o 'todo_chile': true)")

    # A nivel país el área a cubrir es mucho más grande, así que se le
    # da más tiempo a Overpass antes de que corte la consulta.
    timeout = 180 if todo_chile else 25
    area_query = "Chile" if todo_chile else comuna
    area_id = _area_id_comuna(area_query)
    key, _, value = rubro_osm.partition("=")

    query = f"""
    [out:json][timeout:{timeout}];
    area({area_id})->.searchArea;
    (
      node["{key}"="{value}"](area.searchArea);
      way["{key}"="{value}"](area.searchArea);
    );
    out center tags;
    """
    resp = httpx.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=timeout + 10)
    resp.raise_for_status()
    data = resp.json()

    leads = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        nombre = tags.get("name")
        if not nombre:
            continue  # sin nombre no es un lead usable

        website = tags.get("website") or tags.get("contact:website")
        telefono = tags.get("phone") or tags.get("contact:phone")
        direccion = ", ".join(filter(None, [
            tags.get("addr:street"), tags.get("addr:housenumber"),
        ])) or None

        leads.append({
            "source_id": f"{el['type']}/{el['id']}",  # ej: "node/123456"
            "nombre": nombre,
            "rubro": value,
            "comuna": comuna if not todo_chile else (tags.get("addr:city") or "Chile"),
            "direccion": direccion,
            "telefono": telefono,
            "tiene_web": bool(website),
            "website_url": website,
        })
    return leads


def verificar(source_id: str) -> dict | None:
    """Re-consulta un elemento puntual por su source_id ('node/123'
    o 'way/123'), para el proceso de refresco."""
    tipo, _, elem_id = source_id.partition("/")
    if tipo not in ("node", "way"):
        return None

    query = f"[out:json][timeout:25]; {tipo}({elem_id}); out tags;"
    resp = httpx.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    elementos = resp.json().get("elements", [])
    if not elementos:
        return None  # ya no existe en OSM

    tags = elementos[0].get("tags", {})
    nombre = tags.get("name")
    if not nombre:
        return None

    website = tags.get("website") or tags.get("contact:website")
    return {
        "source_id": source_id,
        "nombre": nombre,
        "direccion": ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber")])) or None,
        "telefono": tags.get("phone") or tags.get("contact:phone"),
        "tiene_web": bool(website),
        "website_url": website,
    }
