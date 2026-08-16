"""
Conector de Google Places API (Text Search + Place Details).

Reemplaza al scraper directo de Maps que nunca funcionó bien:
usa la API oficial, así que no hay bloqueos ni resultados
incompletos por rate-limiting silencioso.

Parámetros esperados en el preset (parametros JSON):
    {
        "rubro": "restaurante",       # obligatorio — el tipo de negocio a buscar
        "comuna": "Providencia",      # obligatorio — se concatena a la query
        "radio_m": 3000               # opcional, default 3000
    }
"""
import httpx

from app.config import GOOGLE_PLACES_API_KEY

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Solo pedimos los campos que realmente usamos — Places API cobra
# distinto según qué campos se piden (Field Masking), así que esto
# no es un detalle menor, es lo que mantiene el costo bajo.
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.primaryTypeDisplayName",
])


def buscar(parametros: dict) -> list[dict]:
    """Ejecuta una búsqueda contra Places API y devuelve leads en el
    formato unificado (ver connectors/base.py). No filtra por
    tiene_web aquí — eso se decide en la capa de consulta, no en la
    captura (para no perder leads si cambia el público objetivo).

    Nota: Text Search devuelve como máximo ~60 resultados (3 páginas
    de 20), sin importar cuán grande sea el área. Con 'todo_chile' la
    query es más amplia pero el techo de resultados es el mismo — no
    es una forma de traer todos los negocios del país, solo de no
    tener que elegir una ciudad. Si hace falta más cobertura a nivel
    país, conviene correr el mismo preset por ciudad en vez de una
    sola vez con todo_chile."""
    if not GOOGLE_PLACES_API_KEY:
        raise RuntimeError(
            "Falta GOOGLE_PLACES_API_KEY — configurala en el archivo .env "
            "(ver .env.example)"
        )

    rubro = parametros.get("rubro")
    comuna = parametros.get("comuna")
    todo_chile = parametros.get("todo_chile", False)

    if not rubro:
        raise ValueError("El preset necesita al menos 'rubro'")
    if not todo_chile and not comuna:
        raise ValueError("El preset necesita 'comuna' (o 'todo_chile': true)")

    query = f"{rubro} en Chile" if todo_chile else f"{rubro} en {comuna}, Chile"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "languageCode": "es"}

    response = httpx.post(TEXT_SEARCH_URL, json=body, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()

    leads = []
    for place in data.get("places", []):
        website_url = place.get("websiteUri")
        leads.append({
            "source_id": place["id"],
            "nombre": place.get("displayName", {}).get("text", ""),
            "rubro": place.get("primaryTypeDisplayName", {}).get("text") or rubro,
            "comuna": comuna,
            "direccion": place.get("formattedAddress"),
            "telefono": place.get("nationalPhoneNumber"),
            "tiene_web": bool(website_url) if website_url is not None else None,
            "website_url": website_url,
        })
    return leads


def verificar(source_id: str) -> dict | None:
    """Re-consulta un lugar puntual por su place_id, para el proceso
    de refresco. Devuelve None si el lugar ya no existe en Places
    (negocio cerrado, por ejemplo) — quien llama decide qué hacer
    con eso (incrementar intentos_verificacion)."""
    if not GOOGLE_PLACES_API_KEY:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY")

    url = f"https://places.googleapis.com/v1/places/{source_id}"
    headers = {
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK.replace("places.", ""),
    }
    response = httpx.get(url, headers=headers, timeout=15)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    place = response.json()

    website_url = place.get("websiteUri")
    return {
        "source_id": source_id,
        "nombre": place.get("displayName", {}).get("text", ""),
        "direccion": place.get("formattedAddress"),
        "telefono": place.get("nationalPhoneNumber"),
        "tiene_web": bool(website_url) if website_url is not None else None,
        "website_url": website_url,
    }
