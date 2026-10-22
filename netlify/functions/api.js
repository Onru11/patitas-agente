/*
 * API pública de Patitaspe (Netlify Function).
 *   /api/precio  /api/verificar  /api/triaje  /api/clinicas  /api/servicios
 */
const { RUTAS } = require('../lib/patitas.js');

const CABECERAS = {
  'Content-Type': 'application/json; charset=utf-8',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Cache-Control': 'public, max-age=300'
};

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return { statusCode: 204, headers: CABECERAS, body: '' };
  const ruta = (event.path || '').split('/').filter(Boolean).pop();
  const fn = RUTAS[ruta];
  if (!fn) {
    return { statusCode: 404, headers: CABECERAS, body: JSON.stringify({ ok: false, error: 'Ruta no encontrada', rutas: Object.keys(RUTAS) }) };
  }
  let q = { ...(event.queryStringParameters || {}) };
  if (event.httpMethod === 'POST' && event.body) {
    try { q = { ...q, ...JSON.parse(event.body) }; } catch (e) {
      return { statusCode: 400, headers: CABECERAS, body: JSON.stringify({ ok: false, error: 'JSON inválido' }) };
    }
  }
  const r = fn(q);
  return { statusCode: r.ok ? 200 : 400, headers: CABECERAS, body: JSON.stringify(r) };
};
