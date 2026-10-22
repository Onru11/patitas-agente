#!/usr/bin/env node
/* Servidor local de la API, sin dependencias: node scripts/api-local.js  ->  http://localhost:8888/api/... */
const http = require('http');
const { handler } = require('../netlify/functions/api.js');
const PUERTO = process.env.PORT || 8888;
http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  let body = '';
  req.on('data', (c) => (body += c));
  req.on('end', async () => {
    const r = await handler({ httpMethod: req.method, path: url.pathname, queryStringParameters: Object.fromEntries(url.searchParams), body });
    res.writeHead(r.statusCode, r.headers); res.end(r.body);
  });
}).listen(PUERTO, () => console.log(`API de Patitaspe en http://localhost:${PUERTO}/api/precio?servicio=consulta&zona=centro`));
