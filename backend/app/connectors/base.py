"""
Contrato mínimo entre un conector de fuente y el resto del sistema.

A propósito NO hay una clase base abstracta ni un framework de
plugins aquí — con una sola fuente en producción, forzar esa
abstracción sería adivinar cómo va a lucir antes de tener un
segundo caso real para comparar. Cuando se agregue la segunda
fuente, se revisa qué patrón realmente se repite entre ambas y
recién ahí se extrae.

Lo único que sí importa fijar ahora es la FORMA de los datos que
un conector entrega, porque de eso depende todo el resto (dedup,
schema de leads, frontend). Un conector es simplemente una función
que:

  - recibe los `parametros` (dict) de un search_preset
  - devuelve una lista de dicts con esta forma:

    {
        "source_id": str,        # id único en la fuente (dedup)
        "nombre": str,
        "rubro": str | None,
        "comuna": str | None,
        "direccion": str | None,
        "telefono": str | None,
        "tiene_web": bool | None,
        "website_url": str | None,
    }

El campo "source" (ej. "google_places") no lo pone el conector —
lo agrega quien lo invoca, para no repetirlo en cada resultado.
"""
from typing import TypedDict


class LeadData(TypedDict, total=False):
    source_id: str
    nombre: str
    rubro: str | None
    comuna: str | None
    direccion: str | None
    telefono: str | None
    tiene_web: bool | None
    website_url: str | None
