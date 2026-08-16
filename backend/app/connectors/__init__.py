"""
Registro central de conectores. Sumar una fuente nueva es agregar
una línea aquí — nada más del sistema necesita saber que existe.
"""
from app.connectors import datos_gob_cl, google_places, osm_overpass

CONECTORES_BUSQUEDA = {
    "google_places": google_places.buscar,
    "osm_overpass": osm_overpass.buscar,
    "datos_gob_cl": datos_gob_cl.buscar,
}
