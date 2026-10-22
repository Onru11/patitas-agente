/*
 * Lógica de negocio de Patitaspe, compartida por la API (Netlify) y el servidor local.
 * Los datos vienen SIEMPRE de data/datos.json (misma fuente que usa la web).
 */
const datos = require('../../data/datos.json');

const ZONAS = { norte: 'Lima Norte', centro: 'Lima Centro', sur: 'Lima Sur', este: 'Lima Este' };
const TAMANOS = { peq: 'pequeño', med: 'mediano', gra: 'grande' };

function normalizar(t) {
  return String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
}

function zonaDe({ zona, distrito }) {
  const z = normalizar(zona);
  if (ZONAS[z]) return z;
  for (const [k, v] of Object.entries(ZONAS)) if (normalizar(v) === z) return k;
  const d = normalizar(distrito || zona);
  if (d) {
    for (const k of Object.keys(ZONAS)) {
      if ((datos.distritos[k] || []).some((x) => normalizar(x) === d || normalizar(x).includes(d) && d.length > 3)) return k;
    }
  }
  return null;
}

function especieDe(e) {
  const x = normalizar(e);
  if (['gato', 'gata', 'gatos', 'felino'].includes(x)) return 'gato';
  if (['perro', 'perra', 'perros', 'canino', ''].includes(x)) return 'perro';
  return null;
}

function tamanoDe(t) {
  const x = normalizar(t);
  if (['peq', 'pequeno', 'pequena', 'chico', 'chica', 'mini', 'toy'].includes(x)) return 'peq';
  if (['gra', 'grande', 'gigante'].includes(x)) return 'gra';
  return 'med';
}

function servicioDe(s) {
  const x = normalizar(s);
  if (!x) return null;
  const alias = {
    castracion: 'castra', castrar: 'castra', esterilizacion: 'esteril', esterilizar: 'esteril',
    vacuna: 'vacunas', vacunacion: 'vacunas', desparasitacion: 'despar', desparasitar: 'despar',
    radiografia: 'rayos', placa: 'rayos', ecografia: 'eco', hospitalizacion: 'hospi',
    operacion: 'cirugia', cirugia: 'cirugia', limpieza: 'dental', dientes: 'dental',
    emergencia: 'emerg', analisis: 'sangre', hemograma: 'sangre'
  };
  const id = alias[x] || x;
  return datos.servicios.find((s) => s.id === id || normalizar(s.nm).startsWith(x)) || null;
}

function rango(servicio, especie, tamano, zona) {
  const base = especie === 'gato' ? servicio.gato : servicio.perro[tamano];
  const f = datos.factor_zona[zona];
  return [Math.round(base[0] * f), Math.round(base[1] * f)];
}

function error(mensaje, extra) {
  return { ok: false, error: mensaje, ...extra };
}

function opcionesServicios() {
  return datos.servicios.map((s) => ({ id: s.id, nombre: s.nm }));
}

/* GET /api/precio?servicio=castra&especie=gato&tamano=med&zona=centro (o distrito=Surco) */
function precio(q) {
  const especie = especieDe(q.especie);
  if (!especie) return error('Por ahora solo cubrimos perros y gatos.');
  const zona = zonaDe(q);
  if (!zona) return error('No reconozco la zona o distrito. Usa norte, centro, sur o este, o un distrito de Lima.', { zonas: ZONAS });
  const tamano = tamanoDe(q.tamano);
  const lista = q.servicio ? [servicioDe(q.servicio)] : datos.servicios;
  if (!lista[0]) return error('No reconozco ese servicio.', { servicios: opcionesServicios() });
  const items = lista.map((s) => {
    const [min, max] = rango(s, especie, tamano, zona);
    return { id: s.id, servicio: s.nm, min, max, moneda: 'PEN' };
  });
  return {
    ok: true, especie, tamano: especie === 'perro' ? TAMANOS[tamano] : null, zona: ZONAS[zona],
    items, nota: 'Rangos de referencia de clínicas privadas en Lima; no son el tarifario de una clínica específica.',
    actualizado: datos.actualizado
  };
}

/* GET /api/verificar?servicio=consulta&monto=180&especie=perro&zona=centro */
function verificar(q) {
  const p = precio({ ...q });
  if (!p.ok) return p;
  if (p.items.length !== 1) return error('Indica qué servicio te cotizaron.', { servicios: opcionesServicios() });
  const monto = Number(q.monto);
  if (!monto || monto <= 0) return error('Indica el monto que te cotizaron, en soles.');
  const { min, max, servicio } = p.items[0];
  const exceso = Math.round(((monto - max) / max) * 100);
  let veredicto, detalle;
  if (monto < min) { veredicto = 'buen_precio'; detalle = 'Por debajo del rango normal.'; }
  else if (monto <= max) { veredicto = 'precio_justo'; detalle = 'Dentro del rango normal.'; }
  else if (monto <= Math.round(max * 1.25)) { veredicto = 'en_el_limite'; detalle = `Un ${exceso}% por encima del techo: pregunta qué incluye antes de pagar.`; }
  else { veredicto = 'caro'; detalle = `Un ${exceso}% por encima del techo: pide el detalle por escrito y busca una segunda opinión.`; }
  return { ok: true, servicio, monto, rango: [min, max], zona: p.zona, veredicto, detalle };
}

/* GET /api/triaje?sintomas=vomito,respira&especie=gato */
function triaje(q) {
  const especie = especieDe(q.especie) || 'perro';
  const pedidos = (Array.isArray(q.sintomas) ? q.sintomas : String(q.sintomas || '').split(','))
    .map((s) => normalizar(s)).filter(Boolean);
  if (!pedidos.length) {
    return error('Indica al menos un síntoma.', { sintomas: datos.sintomas.map((s) => ({ id: s.id, descripcion: s.t, nivel: s.lvl })) });
  }
  const encontrados = datos.sintomas.filter((s) => pedidos.includes(s.id) || pedidos.includes(normalizar(s.t)));
  const desconocidos = pedidos.filter((p) => !encontrados.some((s) => s.id === p || normalizar(s.t) === p));
  const rojos = encontrados.filter((s) => s.lvl === 'red');
  const ambar = encontrados.filter((s) => s.lvl === 'amber');
  const nivel = rojos.length ? 'rojo' : ambar.length ? 'ambar' : 'verde';
  const acciones = {
    rojo: 'Emergencia: llamar ahora a una clínica 24h e ir de inmediato. No esperar a mañana.',
    ambar: 'No parece de vida o muerte, pero hay que llamar hoy al veterinario y vigilar de cerca.',
    verde: 'Sin señales de alarma marcadas. Vigilar las próximas horas; si aparece una señal roja, ir a emergencia.'
  };
  let extra = '';
  if (especie === 'gato' && encontrados.some((s) => s.id === 'orina')) {
    extra = 'En gatos machos, no poder orinar es de vida o muerte en pocas horas.';
  }
  return {
    ok: true, especie, nivel, accion: acciones[nivel], aviso_especial: extra || null,
    sintomas_rojos: rojos.map((s) => s.t), sintomas_ambar: ambar.map((s) => s.t),
    no_reconocidos: desconocidos,
    descargo: 'Orientación general, no reemplaza la evaluación de un veterinario.'
  };
}

/* GET /api/clinicas?zona=sur  (o distrito=Chorrillos; sin filtro = todas) */
function clinicas(q) {
  const zona = (q.zona || q.distrito) ? zonaDe(q) : null;
  if ((q.zona || q.distrito) && !zona) return error('No reconozco la zona o distrito.', { zonas: ZONAS });
  const lista = datos.clinicas_24h
    .filter((c) => !zona || c.z === zona)
    .map((c) => ({ nombre: c.n, zona: ZONAS[c.z], direccion: c.dir, telefono: c.telDisp, whatsapp: c.wa || null, verificacion: c.conf || null }));
  return { ok: true, zona: zona ? ZONAS[zona] : 'Toda Lima', clinicas: lista, nota: 'Llama antes de ir para confirmar que atienden en ese momento.' };
}

function servicios() {
  return { ok: true, servicios: opcionesServicios(), zonas: ZONAS, distritos: datos.distritos };
}

const RUTAS = { precio, verificar, triaje, clinicas, servicios };

module.exports = { RUTAS, precio, verificar, triaje, clinicas, servicios };
