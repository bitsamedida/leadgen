from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import crud, validacion
from app.connectors import CONECTORES_BUSQUEDA
from app.database import get_connection, init_db
from app.models import LeadEstadoUpdate, LeadOut, PresetCreate, PresetOut, PresetUpdate
from app.refresh import correr_refresco

app = FastAPI(title="LeadGen API")

# El frontend corre en otro puerto durante desarrollo (Vite).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


# ---------------------------------------------------------------
# search_presets
# ---------------------------------------------------------------

@app.post("/presets", response_model=PresetOut)
def crear_preset(preset: PresetCreate):
    if preset.fuente not in CONECTORES_BUSQUEDA:
        raise HTTPException(400, f"Fuente desconocida: {preset.fuente}. Disponibles: {list(CONECTORES_BUSQUEDA)}")
    with get_connection() as conn:
        preset_id = crud.crear_preset(conn, preset.nombre, preset.fuente, preset.parametros)
    with get_connection() as conn:
        return crud.obtener_preset(conn, preset_id)


@app.get("/presets", response_model=list[PresetOut])
def listar_presets(solo_activos: bool = False):
    with get_connection() as conn:
        return crud.listar_presets(conn, solo_activos=solo_activos)


@app.patch("/presets/{preset_id}/activo")
def cambiar_estado_preset(preset_id: int, activo: bool):
    with get_connection() as conn:
        if crud.obtener_preset(conn, preset_id) is None:
            raise HTTPException(404, "Preset no encontrado")
        crud.set_preset_activo(conn, preset_id, activo)
    return {"ok": True}


@app.patch("/presets/{preset_id}", response_model=PresetOut)
def editar_preset(preset_id: int, cambios: PresetUpdate):
    with get_connection() as conn:
        if crud.obtener_preset(conn, preset_id) is None:
            raise HTTPException(404, "Preset no encontrado")
        crud.actualizar_preset(conn, preset_id, nombre=cambios.nombre, parametros=cambios.parametros)
    with get_connection() as conn:
        return crud.obtener_preset(conn, preset_id)


@app.delete("/presets/{preset_id}")
def borrar_preset(preset_id: int):
    with get_connection() as conn:
        borrado = crud.eliminar_preset(conn, preset_id)
    if not borrado:
        raise HTTPException(404, "Preset no encontrado")
    return {"ok": True}


@app.post("/presets/{preset_id}/ejecutar")
def ejecutar_preset(preset_id: int):
    """Corre la búsqueda de un preset contra su fuente y guarda los
    leads (sin filtrar por tiene_web — eso se aplica al consultar)."""
    with get_connection() as conn:
        preset = crud.obtener_preset(conn, preset_id)
    if preset is None:
        raise HTTPException(404, "Preset no encontrado")

    buscar = CONECTORES_BUSQUEDA.get(preset["fuente"])
    if buscar is None:
        raise HTTPException(400, f"No hay conector registrado para la fuente: {preset['fuente']}")

    try:
        leads = buscar(preset["parametros"])
    except Exception as e:
        raise HTTPException(502, f"Error al consultar la fuente: {e}")

    with get_connection() as conn:
        for lead in leads:
            crud.upsert_lead(conn, preset["fuente"], preset_id, lead)
        crud.marcar_preset_ejecutado(conn, preset_id)

    return {"leads_procesados": len(leads)}


# ---------------------------------------------------------------
# leads
# ---------------------------------------------------------------

@app.get("/leads", response_model=list[LeadOut])
def listar_leads(
    comuna: str | None = None,
    rubro: str | None = None,
    estado: str | None = None,
    tiene_web: bool | None = None,
    solo_con_advertencias: bool = False,
    limit: int = 200,
):
    with get_connection() as conn:
        leads = crud.listar_leads(conn, comuna=comuna, rubro=rubro, estado=estado,
                                   tiene_web=tiene_web, limit=limit)
    for lead in leads:
        lead.update(validacion.evaluar_lead(lead))
    if solo_con_advertencias:
        leads = [l for l in leads if l["advertencias"]]
        leads.sort(key=lambda l: l["completitud"])
    return leads


@app.patch("/leads/{lead_id}/estado")
def actualizar_estado(lead_id: int, cambio: LeadEstadoUpdate):
    try:
        with get_connection() as conn:
            actualizado = crud.actualizar_estado_lead(conn, lead_id, cambio.estado, cambio.notas)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not actualizado:
        raise HTTPException(404, "Lead no encontrado")
    return {"ok": True}


# ---------------------------------------------------------------
# refresco
# ---------------------------------------------------------------

@app.post("/refresh")
def refrescar_leads():
    """Dispara manualmente el proceso de re-verificación (también se
    puede correr como cron vía `python -m app.refresh`)."""
    return correr_refresco()
