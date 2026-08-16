"""
Operaciones de base de datos. Todo lo que toca la tabla `leads` o
`search_presets` pasa por aquí — nada de SQL suelto en main.py.
"""
import json
import sqlite3
from datetime import datetime, timezone

ESTADOS_VALIDOS = {"nuevo", "contactado", "interesado", "cliente", "descartado", "inactivo"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------
# search_presets
# ---------------------------------------------------------------

def crear_preset(conn: sqlite3.Connection, nombre: str, fuente: str, parametros: dict) -> int:
    cur = conn.execute(
        "INSERT INTO search_presets (nombre, fuente, parametros) VALUES (?, ?, ?)",
        (nombre, fuente, json.dumps(parametros)),
    )
    return cur.lastrowid


def listar_presets(conn: sqlite3.Connection, solo_activos: bool = False) -> list[dict]:
    query = "SELECT * FROM search_presets"
    if solo_activos:
        query += " WHERE activo = 1"
    rows = conn.execute(query).fetchall()
    presets = []
    for row in rows:
        p = dict(row)
        p["parametros"] = json.loads(p["parametros"])
        presets.append(p)
    return presets


def obtener_preset(conn: sqlite3.Connection, preset_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM search_presets WHERE id = ?", (preset_id,)).fetchone()
    if row is None:
        return None
    p = dict(row)
    p["parametros"] = json.loads(p["parametros"])
    return p


def marcar_preset_ejecutado(conn: sqlite3.Connection, preset_id: int) -> None:
    conn.execute(
        "UPDATE search_presets SET ultima_ejecucion = ? WHERE id = ?",
        (_now(), preset_id),
    )


def set_preset_activo(conn: sqlite3.Connection, preset_id: int, activo: bool) -> None:
    conn.execute(
        "UPDATE search_presets SET activo = ? WHERE id = ?",
        (1 if activo else 0, preset_id),
    )


def actualizar_preset(
    conn: sqlite3.Connection, preset_id: int,
    nombre: str | None = None, parametros: dict | None = None,
) -> bool:
    """Edición parcial — solo toca los campos que vienen con valor.
    No permite cambiar la 'fuente' de un preset ya creado: mezclaría
    leads capturados con una fuente bajo un preset que ahora apunta a
    otra. Para cambiar de fuente, conviene crear un preset nuevo."""
    campos, valores = [], []
    if nombre is not None:
        campos.append("nombre = ?")
        valores.append(nombre)
    if parametros is not None:
        campos.append("parametros = ?")
        valores.append(json.dumps(parametros))
    if not campos:
        return False
    valores.append(preset_id)
    cur = conn.execute(f"UPDATE search_presets SET {', '.join(campos)} WHERE id = ?", valores)
    return cur.rowcount > 0


def eliminar_preset(conn: sqlite3.Connection, preset_id: int) -> bool:
    """Borra el preset. Los leads que capturó no se borran — su
    preset_id queda en NULL (ver ON DELETE SET NULL en el schema),
    conservan su 'source' y 'source_id' así que siguen siendo
    identificables y refrescables igual."""
    cur = conn.execute("DELETE FROM search_presets WHERE id = ?", (preset_id,))
    return cur.rowcount > 0


# ---------------------------------------------------------------
# leads
# ---------------------------------------------------------------

def upsert_lead(conn: sqlite3.Connection, source: str, preset_id: int, lead: dict) -> None:
    """Inserta un lead nuevo, o actualiza los campos de negocio si ya
    existe (mismo source + source_id) — sin tocar su `estado` (eso lo
    controla el usuario en el pipeline, no una re-captura)."""
    existing = conn.execute(
        "SELECT id FROM leads WHERE source = ? AND source_id = ?",
        (source, lead["source_id"]),
    ).fetchone()

    if existing:
        conn.execute(
            """UPDATE leads SET nombre=?, rubro=?, comuna=?, direccion=?, telefono=?,
                                 tiene_web=?, website_url=?, ultima_verificacion=?
               WHERE id=?""",
            (lead.get("nombre"), lead.get("rubro"), lead.get("comuna"),
             lead.get("direccion"), lead.get("telefono"), lead.get("tiene_web"),
             lead.get("website_url"), _now(), existing["id"]),
        )
    else:
        conn.execute(
            """INSERT INTO leads (source, source_id, preset_id, nombre, rubro, comuna,
                                   direccion, telefono, tiene_web, website_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, lead["source_id"], preset_id, lead.get("nombre"), lead.get("rubro"),
             lead.get("comuna"), lead.get("direccion"), lead.get("telefono"),
             lead.get("tiene_web"), lead.get("website_url")),
        )


def listar_leads(
    conn: sqlite3.Connection,
    comuna: str | None = None,
    rubro: str | None = None,
    estado: str | None = None,
    tiene_web: bool | None = None,
    limit: int = 200,
) -> list[dict]:
    """Filtros aplicados en la consulta, no en la captura — la data
    completa siempre está guardada, esto solo decide qué mostrar."""
    query = "SELECT * FROM leads WHERE 1=1"
    params: list = []
    if comuna:
        query += " AND comuna = ?"
        params.append(comuna)
    if rubro:
        query += " AND rubro = ?"
        params.append(rubro)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if tiene_web is not None:
        query += " AND tiene_web = ?"
        params.append(1 if tiene_web else 0)
    query += " ORDER BY fecha_captura DESC LIMIT ?"
    params.append(limit)

    return [dict(row) for row in conn.execute(query, params).fetchall()]


def actualizar_estado_lead(conn: sqlite3.Connection, lead_id: int, estado: str, notas: str | None = None) -> bool:
    if estado not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {estado}. Válidos: {ESTADOS_VALIDOS}")
    cur = conn.execute(
        "UPDATE leads SET estado = ?, notas = COALESCE(?, notas) WHERE id = ?",
        (estado, notas, lead_id),
    )
    return cur.rowcount > 0


def leads_para_refrescar(conn: sqlite3.Connection, limit: int) -> list[dict]:
    """Los leads activos con la verificación más antigua primero —
    esto es lo que evita que se acumulen entradas viejas sin revisar."""
    rows = conn.execute(
        """SELECT * FROM leads WHERE estado != 'inactivo'
           ORDER BY ultima_verificacion ASC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def aplicar_resultado_verificacion(
    conn: sqlite3.Connection, lead_id: int, encontrado: bool,
    datos_actualizados: dict | None = None, max_intentos: int = 3,
) -> None:
    """Aplica el resultado de re-consultar un lead contra su fuente.
    Si ya no aparece, cuenta como intento fallido; tras `max_intentos`
    seguidos se marca inactivo en vez de seguir reintentando."""
    if encontrado and datos_actualizados:
        conn.execute(
            """UPDATE leads SET nombre=?, direccion=?, telefono=?, tiene_web=?,
                                 website_url=?, ultima_verificacion=?, intentos_verificacion=0
               WHERE id=?""",
            (datos_actualizados.get("nombre"), datos_actualizados.get("direccion"),
             datos_actualizados.get("telefono"), datos_actualizados.get("tiene_web"),
             datos_actualizados.get("website_url"), _now(), lead_id),
        )
    else:
        row = conn.execute("SELECT intentos_verificacion FROM leads WHERE id=?", (lead_id,)).fetchone()
        intentos = (row["intentos_verificacion"] if row else 0) + 1
        nuevo_estado_sql = ", estado = 'inactivo'" if intentos >= max_intentos else ""
        conn.execute(
            f"UPDATE leads SET intentos_verificacion=?, ultima_verificacion=?{nuevo_estado_sql} WHERE id=?",
            (intentos, _now(), lead_id),
        )
