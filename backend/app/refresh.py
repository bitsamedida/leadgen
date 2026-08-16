"""
Proceso de refresco: re-verifica los leads más antiguos contra su
fuente original, para que la tabla no se llene de datos obsoletos.

Agnóstico a la fuente por diseño: solo sabe que cada `source` tiene
una función `verificar(source_id) -> dict | None` en su conector.
Cuando se agregue una segunda fuente, solo hay que sumar su entrada
aquí — el resto de la lógica no cambia.
"""
from app import crud
from app.config import DB_PATH, MAX_VERIFICATION_ATTEMPTS, REFRESH_BATCH_SIZE
from app.connectors import google_places, osm_overpass
from app.database import get_connection

VERIFICADORES = {
    "google_places": google_places.verificar,
    "osm_overpass": osm_overpass.verificar,
}


def correr_refresco(batch_size: int = REFRESH_BATCH_SIZE) -> dict:
    """Re-verifica el lote de leads más desactualizados. Devuelve un
    resumen (cuántos se actualizaron, cuántos fallaron, cuántos
    quedaron inactivos) para loguear o mostrar en el frontend."""
    resumen = {"revisados": 0, "actualizados": 0, "sin_cambios": 0, "marcados_inactivos": 0, "sin_verificador": 0}

    with get_connection() as conn:
        leads = crud.leads_para_refrescar(conn, limit=batch_size)

    for lead in leads:
        verificar = VERIFICADORES.get(lead["source"])
        if verificar is None:
            resumen["sin_verificador"] += 1
            continue

        resultado = verificar(lead["source_id"])
        resumen["revisados"] += 1

        with get_connection() as conn:
            estaba_activo = lead["estado"] != "inactivo"
            crud.aplicar_resultado_verificacion(
                conn, lead["id"], encontrado=resultado is not None,
                datos_actualizados=resultado, max_intentos=MAX_VERIFICATION_ATTEMPTS,
            )
            if resultado is not None:
                resumen["actualizados"] += 1
            else:
                row = conn.execute("SELECT estado FROM leads WHERE id=?", (lead["id"],)).fetchone()
                if estaba_activo and row["estado"] == "inactivo":
                    resumen["marcados_inactivos"] += 1
                else:
                    resumen["sin_cambios"] += 1

    return resumen


if __name__ == "__main__":
    # Pensado para correr como cron nocturno, ej:
    #   0 3 * * * /path/venv/bin/python -m app.refresh
    print(correr_refresco())
