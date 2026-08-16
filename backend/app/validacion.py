"""
Validación automática de calidad de datos.

Importante: esto NO confirma que un negocio existe de verdad — eso
requiere criterio humano o una fuente paga de verificación. Lo que
sí hace es detectar automáticamente los datos con más probabilidad
de estar mal, para que la revisión manual se enfoque en esos casos
en vez de en la lista completa.
"""
import re

# Números chilenos: desde 2018 todos tienen 9 dígitos después del
# código de país (+56), sin excepción de largo por tipo. Se acepta
# con o sin '+56'/'56' adelante, y con espacios/guiones que se
# ignoran al validar.
_TELEFONO_VALIDO = re.compile(r"^(?:\+?56)?9?\d{8,9}$")


def _normalizar_telefono(telefono: str) -> str:
    return re.sub(r"[\s\-()]", "", telefono)


def evaluar_lead(lead: dict) -> dict:
    """Devuelve {'advertencias': [...], 'completitud': 0-100} para un
    lead. Las advertencias son pistas de datos posiblemente
    incorrectos o incompletos, no una confirmación de que el lead es
    malo — la palabra final la tiene la revisión manual."""
    advertencias = []
    campos_clave = 0
    campos_completos = 0

    # Teléfono
    campos_clave += 1
    telefono = lead.get("telefono")
    if not telefono:
        advertencias.append("sin teléfono")
    else:
        campos_completos += 1
        if not _TELEFONO_VALIDO.match(_normalizar_telefono(telefono)):
            advertencias.append("teléfono con formato inválido")

    # Dirección
    campos_clave += 1
    if not lead.get("direccion"):
        advertencias.append("sin dirección")
    else:
        campos_completos += 1

    # Determinación de sitio web
    campos_clave += 1
    if lead.get("tiene_web") is None:
        advertencias.append("no se pudo determinar si tiene sitio web")
    else:
        campos_completos += 1

    # Nombre sospechosamente corto (posible dato corrupto o genérico)
    nombre = lead.get("nombre") or ""
    if len(nombre.strip()) < 3:
        advertencias.append("nombre demasiado corto o vacío")

    completitud = round(100 * campos_completos / campos_clave) if campos_clave else 0
    return {"advertencias": advertencias, "completitud": completitud}
