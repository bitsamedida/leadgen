// Sugerencias para el campo de rubro al crear un preset. Son solo
// sugerencias (datalist) — el campo sigue aceptando texto libre para
// cualquier categoría que no esté aquí. Agregar una nueva es sumar
// una línea a la lista que corresponda.

// Tags de OpenStreetMap (formato clave=valor). Ver más en
// https://taginfo.openstreetmap.org — buscá el tipo de negocio y
// consulta qué tag usan otros mappers para esa categoría.
// Ciudades chilenas comunes como sugerencias de ubicación (mejor
// resolución en OpenStreetMap que comunas chicas dentro del Gran
// Santiago). Igual que con los rubros, son solo sugerencias — se
// puede escribir cualquier otra ciudad o comuna.
// Plantillas de preset listas para usar — cubren rubros comunes
// entre los prospectos típicos de un desarrollador freelance
// (negocios locales con poca presencia digital). Elegir una
// pre-llena el formulario, que sigue siendo editable antes de crear
// el preset — no reemplaza la opción de armar uno desde cero.
export const PLANTILLAS_PRESET = [
  { nombre: 'Restaurantes sin web', fuente: 'osm_overpass', rubro: 'amenity=restaurant', comuna: 'Santiago' },
  { nombre: 'Peluquerías y salones de belleza', fuente: 'osm_overpass', rubro: 'shop=hairdresser', comuna: 'Santiago' },
  { nombre: 'Talleres mecánicos', fuente: 'osm_overpass', rubro: 'shop=car_repair', comuna: 'Santiago' },
  { nombre: 'Ferreterías', fuente: 'osm_overpass', rubro: 'shop=hardware', comuna: 'Santiago' },
  { nombre: 'Gimnasios', fuente: 'osm_overpass', rubro: 'leisure=fitness_centre', comuna: 'Santiago' },
  { nombre: 'Veterinarias', fuente: 'osm_overpass', rubro: 'amenity=veterinary', comuna: 'Santiago' },
  { nombre: 'Dentistas', fuente: 'osm_overpass', rubro: 'healthcare=dentist', comuna: 'Santiago' },
  { nombre: 'Abogados y estudios jurídicos', fuente: 'osm_overpass', rubro: 'office=lawyer', comuna: 'Santiago' },
]

export const CIUDADES_CHILE = [
  'Santiago',
  'Valparaíso',
  'Viña del Mar',
  'Concepción',
  'La Serena',
  'Coquimbo',
  'Antofagasta',
  'Temuco',
  'Rancagua',
  'Talca',
  'Arica',
  'Iquique',
  'Puerto Montt',
  'Chillán',
  'Osorno',
  'Punta Arenas',
  'Copiapó',
  'Calama',
  'Los Ángeles',
  'Curicó',
  'Valdivia',
  'Quillota',
  'San Antonio',
  'Ovalle',
]

export const RUBROS_OSM = [
  { tag: 'amenity=restaurant', label: 'Restaurante' },
  { tag: 'amenity=cafe', label: 'Cafetería' },
  { tag: 'amenity=bar', label: 'Bar' },
  { tag: 'amenity=fast_food', label: 'Comida rápida' },
  { tag: 'shop=bakery', label: 'Panadería' },
  { tag: 'shop=hairdresser', label: 'Peluquería' },
  { tag: 'shop=beauty', label: 'Centro de belleza' },
  { tag: 'shop=clothes', label: 'Tienda de ropa' },
  { tag: 'shop=shoes', label: 'Zapatería' },
  { tag: 'shop=furniture', label: 'Mueblería' },
  { tag: 'shop=hardware', label: 'Ferretería' },
  { tag: 'shop=car_repair', label: 'Taller mecánico' },
  { tag: 'shop=electronics', label: 'Tienda de electrónica' },
  { tag: 'shop=florist', label: 'Florería' },
  { tag: 'shop=pet', label: 'Petshop' },
  { tag: 'shop=optician', label: 'Óptica' },
  { tag: 'shop=supermarket', label: 'Minimarket / almacén' },
  { tag: 'craft=carpenter', label: 'Carpintería' },
  { tag: 'healthcare=dentist', label: 'Dentista' },
  { tag: 'healthcare=physiotherapist', label: 'Kinesiólogo' },
  { tag: 'amenity=veterinary', label: 'Veterinaria' },
  { tag: 'leisure=fitness_centre', label: 'Gimnasio' },
  { tag: 'office=lawyer', label: 'Abogado / estudio jurídico' },
  { tag: 'office=accountant', label: 'Contador' },
  { tag: 'office=estate_agent', label: 'Inmobiliaria' },
]

// Texto libre para Google Places (Text Search interpreta lenguaje
// natural, no tags) — misma idea, son sugerencias.
export const RUBROS_PLACES = [
  'restaurante',
  'cafetería',
  'peluquería',
  'gimnasio',
  'ferretería',
  'taller mecánico',
  'dentista',
  'veterinaria',
  'abogado',
  'contador',
  'inmobiliaria',
  'florería',
  'panadería',
]
