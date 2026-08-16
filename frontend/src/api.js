const BASE_URL = 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  listarPresets: () => request('/presets'),
  crearPreset: (preset) =>
    request('/presets', { method: 'POST', body: JSON.stringify(preset) }),
  ejecutarPreset: (id) => request(`/presets/${id}/ejecutar`, { method: 'POST' }),
  setPresetActivo: (id, activo) =>
    request(`/presets/${id}/activo?activo=${activo}`, { method: 'PATCH' }),
  editarPreset: (id, cambios) =>
    request(`/presets/${id}`, { method: 'PATCH', body: JSON.stringify(cambios) }),
  borrarPreset: (id) => request(`/presets/${id}`, { method: 'DELETE' }),

  listarLeads: (filtros = {}) => {
    const params = new URLSearchParams()
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== '' && v !== null && v !== undefined) params.set(k, v)
    })
    const qs = params.toString()
    return request(`/leads${qs ? `?${qs}` : ''}`)
  },
  actualizarEstadoLead: (id, estado, notas) =>
    request(`/leads/${id}/estado`, {
      method: 'PATCH',
      body: JSON.stringify({ estado, notas: notas ?? null }),
    }),

  refrescarLeads: () => request('/refresh', { method: 'POST' }),
}
