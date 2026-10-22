#!/usr/bin/env node
/*
 * Patitaspe: una sola fuente de datos.
 *   data/datos.json  ->  index.html (bloques marcados) y la API (netlify/functions)
 *
 * Uso:
 *   node scripts/sincronizar-datos.js            # copia datos.json dentro de index.html
 *   node scripts/sincronizar-datos.js --extraer  # (una vez) saca los datos de index.html a datos.json
 */
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
const HTML = path.join(raiz, 'index.html');
const JSONF = path.join(raiz, 'data', 'datos.json');
const BLOQUES = ['SERVICES', 'ZONE_FACTOR', 'SYMPTOMS', 'CLINICS'];

function buscarDeclaracion(src, nombre) {
  const marcado = new RegExp('/\\*DATOS:' + nombre + '\\*/[\\s\\S]*?/\\*FIN:' + nombre + '\\*/');
  const m1 = src.match(marcado);
  if (m1) return { inicio: m1.index, fin: m1.index + m1[0].length };
  const re = new RegExp('const ' + nombre + '\\s*=\\s*');
  const m = re.exec(src);
  if (!m) throw new Error('No encontré ' + nombre + ' en index.html');
  let i = m.index + m[0].length, nivel = 0, enStr = null;
  for (; i < src.length; i++) {
    const c = src[i];
    if (enStr) { if (c === '\\') { i++; continue; } if (c === enStr) enStr = null; continue; }
    if (c === "'" || c === '"' || c === '`') { enStr = c; continue; }
    if (c === '[' || c === '{') nivel++;
    else if (c === ']' || c === '}') { nivel--; if (nivel === 0) { i++; break; } }
  }
  if (src[i] === ';') i++;
  return { inicio: m.index, fin: i };
}

function bloque(nombre, valor) {
  return '/*DATOS:' + nombre + '*/const ' + nombre + ' = ' + JSON.stringify(valor, null, 1) + ';/*FIN:' + nombre + '*/';
}

let src = fs.readFileSync(HTML, 'utf8');

if (process.argv.includes('--extraer')) {
  const datos = {};
  for (const n of BLOQUES) {
    const { inicio, fin } = buscarDeclaracion(src, n);
    const decl = src.slice(inicio, fin).replace(/\/\*(DATOS|FIN):\w+\*\//g, '');
    datos[n] = new Function(decl + '; return ' + n + ';')();
  }
  const salida = {
    _info: 'Fuente única de datos de Patitaspe. Edita aquí y corre: node scripts/sincronizar-datos.js',
    actualizado: new Date().toISOString().slice(0, 10),
    servicios: datos.SERVICES,
    factor_zona: datos.ZONE_FACTOR,
    sintomas: datos.SYMPTOMS,
    clinicas_24h: datos.CLINICS
  };
  fs.writeFileSync(JSONF, JSON.stringify(salida, null, 2) + '\n');
  console.log('Escrito data/datos.json');
}

const d = JSON.parse(fs.readFileSync(JSONF, 'utf8'));
const mapa = { SERVICES: d.servicios, ZONE_FACTOR: d.factor_zona, SYMPTOMS: d.sintomas, CLINICS: d.clinicas_24h };
for (const n of BLOQUES) {
  const { inicio, fin } = buscarDeclaracion(src, n);
  src = src.slice(0, inicio) + bloque(n, mapa[n]) + src.slice(fin);
}
fs.writeFileSync(HTML, src);
console.log('index.html actualizado con data/datos.json');
