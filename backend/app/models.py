from pydantic import BaseModel


class PresetCreate(BaseModel):
    nombre: str
    fuente: str
    parametros: dict


class PresetUpdate(BaseModel):
    nombre: str | None = None
    parametros: dict | None = None


class PresetOut(BaseModel):
    id: int
    nombre: str
    fuente: str
    parametros: dict
    activo: bool
    fecha_creacion: str
    ultima_ejecucion: str | None = None


class LeadOut(BaseModel):
    id: int
    source: str
    source_id: str | None = None
    preset_id: int | None = None
    nombre: str
    rubro: str | None = None
    comuna: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    tiene_web: bool | None = None
    website_url: str | None = None
    estado: str
    score: int | None = None
    notas: str | None = None
    fecha_captura: str
    ultima_verificacion: str
    intentos_verificacion: int
    advertencias: list[str] = []
    completitud: int = 100


class LeadEstadoUpdate(BaseModel):
    estado: str
    notas: str | None = None
