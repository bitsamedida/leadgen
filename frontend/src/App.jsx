import { useEffect, useState } from 'react'
import { api } from './api.js'
import { RUBROS_OSM, RUBROS_PLACES, CIUDADES_CHILE, PLANTILLAS_PRESET } from './categorias.js'

const ESTADOS = ['nuevo', 'contactado', 'interesado', 'cliente', 'descartado', 'inactivo']
const FUENTES = ['osm_overpass', 'google_places', 'datos_gob_cl']

export default function App() {
  const [presets, setPresets] = useState([])
  const [leads, setLeads] = useState([])
  const [filtros, setFiltros] = useState({ comuna: '', rubro: '', estado: '', tiene_web: '', solo_con_advertencias: false })
  const [cargando, setCargando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const cargarPresets = () => api.listarPresets().then(setPresets).catch((e) => setMensaje(e.message))
  const cargarLeads = () => api.listarLeads(filtros).then(setLeads).catch((e) => setMensaje(e.message))

  useEffect(() => {
    cargarPresets()
  }, [])

  useEffect(() => {
    cargarLeads()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros])

  async function ejecutarPreset(id) {
    setCargando(true)
    setMensaje('Ejecutando búsqueda…')
    try {
      const res = await api.ejecutarPreset(id)
      setMensaje(`Listo — ${res.leads_procesados} leads procesados.`)
      cargarLeads()
      cargarPresets()
    } catch (e) {
      setMensaje(`Error: ${e.message}`)
    } finally {
      setCargando(false)
    }
  }

  async function refrescar() {
    setCargando(true)
    setMensaje('Refrescando leads existentes…')
    try {
      const res = await api.refrescarLeads()
      setMensaje(
        `Refresco listo — ${res.revisados} revisados, ${res.actualizados} actualizados, ${res.marcados_inactivos} marcados inactivos.`,
      )
      cargarLeads()
    } catch (e) {
      setMensaje(`Error: ${e.message}`)
    } finally {
      setCargando(false)
    }
  }

  async function cambiarEstado(leadId, estado) {
    try {
      await api.actualizarEstadoLead(leadId, estado)
      setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, estado } : l)))
    } catch (e) {
      setMensaje(`Error: ${e.message}`)
    }
  }

  return (
    <div className="app">
      <datalist id="ciudades-sugeridas">
        {CIUDADES_CHILE.map((c) => (
          <option key={c} value={c} />
        ))}
      </datalist>
      <aside className="sidebar">
        <h1>leadgen</h1>
        <NuevoPreset onCreado={cargarPresets} />
        <div className="presets-list">
          <h2>presets</h2>
          {presets.length === 0 && <p className="muted">sin presets todavía</p>}
          {presets.map((p) => (
            <PresetCard
              key={p.id}
              preset={p}
              cargando={cargando}
              onEjecutar={() => ejecutarPreset(p.id)}
              onToggleActivo={() => api.setPresetActivo(p.id, !p.activo).then(cargarPresets)}
              onEditado={cargarPresets}
              onBorrado={cargarPresets}
            />
          ))}
        </div>
        <button className="refresh-btn" disabled={cargando} onClick={refrescar}>
          refrescar leads antiguos
        </button>
        {mensaje && <p className="mensaje">{mensaje}</p>}
      </aside>

      <main className="main">
        <div className="filtros">
          <input
            list="ciudades-sugeridas"
            placeholder="comuna"
            value={filtros.comuna}
            onChange={(e) => setFiltros({ ...filtros, comuna: e.target.value })}
          />
          <input
            placeholder="rubro"
            value={filtros.rubro}
            onChange={(e) => setFiltros({ ...filtros, rubro: e.target.value })}
          />
          <select
            value={filtros.estado}
            onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })}
          >
            <option value="">estado: todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
          <select
            value={filtros.tiene_web}
            onChange={(e) => setFiltros({ ...filtros, tiene_web: e.target.value })}
          >
            <option value="">web: todos</option>
            <option value="false">sin web</option>
            <option value="true">con web</option>
          </select>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filtros.solo_con_advertencias}
              onChange={(e) => setFiltros({ ...filtros, solo_con_advertencias: e.target.checked })}
            />
            solo con advertencias
          </label>
        </div>

        <table className="leads-table">
          <thead>
            <tr>
              <th>nombre</th>
              <th>rubro</th>
              <th>comuna</th>
              <th>teléfono</th>
              <th>web</th>
              <th>estado</th>
              <th>calidad</th>
              <th>última verif.</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr key={l.id}>
                <td>{l.nombre}</td>
                <td>{l.rubro || '—'}</td>
                <td>{l.comuna || '—'}</td>
                <td>{l.telefono || '—'}</td>
                <td>
                  {l.tiene_web === true && <span className="tag tag-si">sí</span>}
                  {l.tiene_web === false && <span className="tag tag-no">no</span>}
                  {l.tiene_web === null && <span className="muted">?</span>}
                </td>
                <td>
                  <select value={l.estado} onChange={(e) => cambiarEstado(l.id, e.target.value)}>
                    {ESTADOS.map((e) => (
                      <option key={e} value={e}>
                        {e}
                      </option>
                    ))}
                  </select>
                </td>
                <td title={l.advertencias.join(', ')}>
                  {l.advertencias.length === 0 ? (
                    <span className="tag tag-si">ok</span>
                  ) : (
                    <span className="tag tag-no">⚠ {l.advertencias.length}</span>
                  )}
                </td>
                <td className="muted small">{new Date(l.ultima_verificacion).toLocaleDateString('es-CL')}</td>
              </tr>
            ))}
            {leads.length === 0 && (
              <tr>
                <td colSpan={8} className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                  sin leads todavía — ejecuta un preset desde el panel izquierdo
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </main>
    </div>
  )
}

function PresetCard({ preset, cargando, onEjecutar, onToggleActivo, onEditado, onBorrado }) {
  const [editando, setEditando] = useState(false)
  const [nombre, setNombre] = useState(preset.nombre)
  const [rubro, setRubro] = useState(
    preset.fuente === 'osm_overpass' ? preset.parametros.rubro_osm ?? '' : preset.parametros.rubro ?? '',
  )
  const [comuna, setComuna] = useState(preset.parametros.comuna ?? '')
  const [todoChile, setTodoChile] = useState(Boolean(preset.parametros.todo_chile))
  const [resourceUrl, setResourceUrl] = useState(preset.parametros.resource_url ?? '')
  const [colNombre, setColNombre] = useState(preset.parametros.columnas?.nombre ?? '')
  const [colDireccion, setColDireccion] = useState(preset.parametros.columnas?.direccion ?? '')
  const [colRubro, setColRubro] = useState(preset.parametros.columnas?.rubro ?? '')
  const [colTelefono, setColTelefono] = useState(preset.parametros.columnas?.telefono ?? '')
  const [error, setError] = useState('')

  async function guardar(e) {
    e.preventDefault()
    setError('')
    let parametros
    if (preset.fuente === 'datos_gob_cl') {
      parametros = {
        resource_url: resourceUrl,
        comuna,
        columnas: {
          nombre: colNombre,
          ...(colDireccion && { direccion: colDireccion }),
          ...(colRubro && { rubro: colRubro }),
          ...(colTelefono && { telefono: colTelefono }),
        },
      }
    } else {
      const ubicacion = todoChile ? { todo_chile: true } : { comuna }
      parametros =
        preset.fuente === 'osm_overpass' ? { rubro_osm: rubro, ...ubicacion } : { rubro, ...ubicacion }
    }
    try {
      await api.editarPreset(preset.id, { nombre, parametros })
      setEditando(false)
      onEditado()
    } catch (err) {
      setError(err.message)
    }
  }

  async function borrar() {
    if (!confirm(`¿Borrar el preset "${preset.nombre}"? Los leads que ya capturó no se pierden.`)) return
    await api.borrarPreset(preset.id)
    onBorrado()
  }

  if (editando) {
    return (
      <form className="new-preset-form" onSubmit={guardar}>
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
        <div className="muted small">{preset.fuente} (no editable)</div>

        {preset.fuente === 'datos_gob_cl' ? (
          <>
            <input value={resourceUrl} onChange={(e) => setResourceUrl(e.target.value)} required />
            <input
              list="ciudades-sugeridas"
              value={comuna}
              onChange={(e) => setComuna(e.target.value)}
              required
            />
            <p className="muted small">nombres de columnas tal cual aparecen en ese CSV:</p>
            <input
              placeholder="columna con el nombre del negocio"
              value={colNombre}
              onChange={(e) => setColNombre(e.target.value)}
              required
            />
            <input
              placeholder="columna dirección (opcional)"
              value={colDireccion}
              onChange={(e) => setColDireccion(e.target.value)}
            />
            <input
              placeholder="columna rubro/giro (opcional)"
              value={colRubro}
              onChange={(e) => setColRubro(e.target.value)}
            />
            <input
              placeholder="columna teléfono (opcional)"
              value={colTelefono}
              onChange={(e) => setColTelefono(e.target.value)}
            />
          </>
        ) : (
          <>
            <input
              list="rubros-sugeridos"
              value={rubro}
              onChange={(e) => setRubro(e.target.value)}
              required
            />
            {!todoChile && (
              <input
                list="ciudades-sugeridas"
                value={comuna}
                onChange={(e) => setComuna(e.target.value)}
                required={!todoChile}
              />
            )}
            <label className="checkbox-label">
              <input type="checkbox" checked={todoChile} onChange={(e) => setTodoChile(e.target.checked)} />
              buscar en todo Chile
            </label>
          </>
        )}
        {error && <p className="mensaje error">{error}</p>}
        <div className="preset-actions">
          <button type="submit">guardar</button>
          <button type="button" className="secondary" onClick={() => setEditando(false)}>
            cancelar
          </button>
        </div>
      </form>
    )
  }

  return (
    <div className="preset-card">
      <div className="preset-header">
        <strong>{preset.nombre}</strong>
        <span className={`badge ${preset.activo ? 'badge-on' : 'badge-off'}`}>
          {preset.activo ? 'activo' : 'pausado'}
        </span>
      </div>
      <div className="muted small">{preset.fuente}</div>
      <div className="preset-actions">
        <button disabled={cargando} onClick={onEjecutar}>
          ejecutar
        </button>
        <button className="secondary" onClick={onToggleActivo}>
          {preset.activo ? 'pausar' : 'activar'}
        </button>
      </div>
      <div className="preset-actions">
        <button className="secondary" onClick={() => setEditando(true)}>
          editar
        </button>
        <button className="secondary danger" onClick={borrar}>
          borrar
        </button>
      </div>
    </div>
  )
}

function NuevoPreset({ onCreado }) {
  const [abierto, setAbierto] = useState(false)
  const [modo, setModo] = useState('elegir') // 'elegir' | 'formulario'
  const [nombre, setNombre] = useState('')
  const [fuente, setFuente] = useState(FUENTES[0])
  const [rubro, setRubro] = useState('')
  const [comuna, setComuna] = useState('')
  const [todoChile, setTodoChile] = useState(false)
  const [resourceUrl, setResourceUrl] = useState('')
  const [colNombre, setColNombre] = useState('')
  const [colDireccion, setColDireccion] = useState('')
  const [colRubro, setColRubro] = useState('')
  const [colTelefono, setColTelefono] = useState('')

  const [error, setError] = useState('')

  function limpiar() {
    setNombre('')
    setFuente(FUENTES[0])
    setRubro('')
    setComuna('')
    setTodoChile(false)
    setResourceUrl('')
    setColNombre('')
    setColDireccion('')
    setColRubro('')
    setColTelefono('')
    setModo('elegir')
    setError('')
    setAbierto(false)
  }

  function aplicarPlantilla(plantilla) {
    setNombre(`${plantilla.nombre} — ${plantilla.comuna}`)
    setFuente(plantilla.fuente)
    setRubro(plantilla.rubro)
    setComuna(plantilla.comuna)
    setTodoChile(false)
    setModo('formulario')
  }

  function empezarEnBlanco() {
    setModo('formulario')
  }

  async function crear(e) {
    e.preventDefault()
    setError('')
    let parametros
    if (fuente === 'datos_gob_cl') {
      parametros = {
        resource_url: resourceUrl,
        comuna,
        columnas: {
          nombre: colNombre,
          ...(colDireccion && { direccion: colDireccion }),
          ...(colRubro && { rubro: colRubro }),
          ...(colTelefono && { telefono: colTelefono }),
        },
      }
    } else {
      const ubicacion = todoChile ? { todo_chile: true } : { comuna }
      parametros = fuente === 'osm_overpass' ? { rubro_osm: rubro, ...ubicacion } : { rubro, ...ubicacion }
    }
    try {
      await api.crearPreset({ nombre, fuente, parametros })
      limpiar()
      onCreado()
    } catch (err) {
      setError(err.message)
    }
  }

  if (!abierto) {
    return (
      <button className="new-preset-btn" onClick={() => setAbierto(true)}>
        + nuevo preset
      </button>
    )
  }

  if (modo === 'elegir') {
    return (
      <div className="plantillas-picker">
        <p className="muted small">elegir un punto de partida:</p>
        {PLANTILLAS_PRESET.map((p) => (
          <button key={p.nombre} className="plantilla-btn" onClick={() => aplicarPlantilla(p)}>
            {p.nombre}
          </button>
        ))}
        <div className="preset-actions">
          <button className="secondary" onClick={empezarEnBlanco}>
            empezar en blanco
          </button>
          <button className="secondary" onClick={() => setAbierto(false)}>
            cancelar
          </button>
        </div>
      </div>
    )
  }

  return (
    <form className="new-preset-form" onSubmit={crear}>
      <input placeholder="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      <select value={fuente} onChange={(e) => setFuente(e.target.value)}>
        {FUENTES.map((f) => (
          <option key={f} value={f}>
            {f}
          </option>
        ))}
      </select>

      {fuente === 'datos_gob_cl' ? (
        <>
          <input
            placeholder="URL de descarga directa del CSV"
            value={resourceUrl}
            onChange={(e) => setResourceUrl(e.target.value)}
            required
          />
          <input
            list="ciudades-sugeridas"
            placeholder="ciudad o comuna"
            value={comuna}
            onChange={(e) => setComuna(e.target.value)}
            required
          />
          <p className="muted small">nombres de columnas tal cual aparecen en ese CSV:</p>
          <input
            placeholder="columna con el nombre del negocio"
            value={colNombre}
            onChange={(e) => setColNombre(e.target.value)}
            required
          />
          <input
            placeholder="columna dirección (opcional)"
            value={colDireccion}
            onChange={(e) => setColDireccion(e.target.value)}
          />
          <input
            placeholder="columna rubro/giro (opcional)"
            value={colRubro}
            onChange={(e) => setColRubro(e.target.value)}
          />
          <input
            placeholder="columna teléfono (opcional)"
            value={colTelefono}
            onChange={(e) => setColTelefono(e.target.value)}
          />
        </>
      ) : (
        <>
          <input
            list="rubros-sugeridos"
            placeholder={fuente === 'osm_overpass' ? 'rubro (elige o escribe un tag OSM)' : 'rubro (elige o escribe uno)'}
            value={rubro}
            onChange={(e) => setRubro(e.target.value)}
            required
          />
          <datalist id="rubros-sugeridos">
            {(fuente === 'osm_overpass' ? RUBROS_OSM : RUBROS_PLACES.map((r) => ({ tag: r, label: r }))).map(
              (r) => (
                <option key={r.tag} value={r.tag}>
                  {r.label}
                </option>
              ),
            )}
          </datalist>
          {!todoChile && (
            <input
              list="ciudades-sugeridas"
              placeholder="ciudad o comuna"
              value={comuna}
              onChange={(e) => setComuna(e.target.value)}
              required={!todoChile}
            />
          )}
          <label className="checkbox-label">
            <input type="checkbox" checked={todoChile} onChange={(e) => setTodoChile(e.target.checked)} />
            buscar en todo Chile
          </label>
          {todoChile && (
            <p className="muted small">
              ⚠️ una búsqueda a nivel país puede tardar bastante y traer muchos resultados — prueba primero acotado a
              una ciudad si puedes
            </p>
          )}
        </>
      )}
      {error && <p className="mensaje error">{error}</p>}
      <div className="preset-actions">
        <button type="submit">crear</button>
        <button type="button" className="secondary" onClick={limpiar}>
          cancelar
        </button>
      </div>
    </form>
  )
}
