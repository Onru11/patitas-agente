# Patitaspe — Hub para dueños de mascotas en Lima

Sitio estático de una sola página que funciona como **instrumento de medición de disposición a pagar (WTP)** para validar la red de clínicas preventivas con cobertura en Lima Norte — no solo como folleto. Trae al público correcto con utilidades gratis (calculadora de costos por zona, verificador "¿te metieron la rata?", triaje de emergencia, directorio 24h, radio para mascotas, cartilla digital, guías y FAQ con schema SEO) y los mide con la sección **Cobertura** (`#planes`): qué plan contratarían, cuánto pagarían al mes y si reservarían su cupo de miembro fundador.

Además, **cada lead llega etiquetado con su origen** (de dónde vino y qué herramientas usó), para distinguir el tráfico viral del calificado y no ensuciar la lectura del gate.

Construido en HTML + CSS + JS vanilla, sin build step, sin dependencias. Un solo archivo (`index.html`). Todo el contenido está en HTML estático — se ve aunque falle el JavaScript y Google lo indexa completo.

## Archivos

```
patitas-pe/
├── index.html      ← toda la app (HTML + CSS + JS inline)
├── og-image.png    ← imagen para compartir en redes (1200×630)
├── assets/
│   ├── hero.jpg    ← foto del hero (generada con IA, optimizada 116KB)
│   └── radio.jpg   ← foto de la sección radio (generada con IA, 128KB)
└── README.md       ← este archivo
```

## Paso 1: Conectar tu Formspree (captura de emails)

El sitio tiene **6 formularios** que envían a Formspree: calculadora, **cobertura/WTP** (el más importante), verificador, triaje, cartilla y footer.

1. Crea una cuenta gratis en [formspree.io](https://formspree.io) (el plan free aguanta 50 envíos/mes, suficiente para arrancar la validación).
2. Crea un formulario. Formspree te da un ID con forma `xxxxxxxx` y una URL `https://formspree.io/f/xxxxxxxx`.
3. Abre `index.html` y reemplaza **las 6 apariciones** de `FORMSPREE_ID` por tu ID real (están comentadas con `<!-- IMPORTANTE: reemplaza FORMSPREE_ID -->`). Para reemplazar todas de una: buscar y reemplazar `FORMSPREE_ID` en el archivo.
4. Guarda. Cada `_subject` ya identifica de qué herramienta vino el lead, así que aunque uses un solo ID los distingues en la bandeja.

> Recomendado para medir mejor: crea **un ID aparte para el formulario de cobertura/WTP** (`formWtp`) y déjalo separado de los demás, así los datos del gate no se mezclan con los leads de utilidades gratis.

## Cómo leer los leads — mapeo al tracker de Notion

El formulario de **Cobertura** (`#planes`) es el que produce la data del gate. Cada envío trae estos campos, listos para volcar a tu tracker "Respuestas de validación":

| Campo del lead | Columna en Notion |
|---|---|
| `tier_interes` | Interés cobertura |
| `monto_dispuesto` | Monto dispuesto |
| `senal_fundador` | Pagaría membresía |
| `distrito` | Distrito |
| `mascota` | Tiene mascota |
| `estimado_calculadora` | Cita/nota (contexto) |
| `origen`, `medio`, `campana` | Canal |
| `primera_interaccion`, `herramientas_usadas` | Señal (qué tan calificado) |

Estos tres últimos van en **todos** los formularios, no solo el de cobertura: `origen` (meta, whatsapp, tiktok, buscador, directo…), `primera_interaccion` (qué tocó primero) y `herramientas_usadas`. Con eso mides la conversión a WTP por canal y separas al que vino por la radio del que vino con dolor de precio.

Para campañas, agrega UTMs al link que difundas: `https://patitas.pe/?utm_source=meta&utm_campaign=lima_norte_jun`. El sitio los lee solo y los adjunta a cada lead.

## Paso 2: Deploy en Vercel

**Opción A — arrastrar la carpeta (lo más rápido):**
1. Entra a [vercel.com](https://vercel.com) y crea cuenta.
2. New Project → arrastra la carpeta `patitas-pe`.
3. Vercel detecta que es un sitio estático. Deploy. En segundos tienes una URL pública.

**Opción B — desde GitHub:**
1. Sube la carpeta `patitas-pe` a un repo de GitHub.
2. En Vercel, New Project → importa el repo → Deploy.
3. Cada push actualiza el sitio solo.

No necesita configuración de build: framework "Other", output directory la raíz.

## Paso 3 (opcional): Dominio propio

Si compras `patitas.pe`, conéctalo en Vercel → Settings → Domains. Las metaetiquetas ya apuntan a `https://patitas.pe`; si usas otro dominio, actualiza el `<link rel="canonical">` y las `og:url` / `og:image` en el `<head>` de `index.html`.

## La radio (audio local)

Los cuatro canales reproducen archivos MP3 propios en `assets/audio/` con el reproductor nativo de HTML5 (controles, bucle y autoplay) — sin depender de YouTube ni de embeds externos. Los canales están en el array `CHANNELS` dentro de `index.html`:

```js
const CHANNELS=[
  {id:'relax',  ... audio:'assets/audio/relax.mp3'},   // música clásica / relajación
  {id:'natura', ... audio:'assets/audio/natura.mp3'},  // sonidos de naturaleza
  {id:'trueno', ... audio:'assets/audio/trueno.mp3'},  // truenos (desensibilización)
  {id:'gato',   ... audio:'assets/audio/gato.mp3'}     // música para gatos
];
```

Para cambiar una pista, reemplaza el MP3 correspondiente en `assets/audio/` (mismo nombre) o edita la ruta `audio:` en el array. El botón "Ya que pasaste por aquí" debajo del reproductor empuja al visitante hacia la calculadora, para que la viralidad de la radio alimente la medición.

> Ojo: algunos previews sandboxeados bloquean el autoplay de audio. Pruébalo en un navegador normal — Chrome, Safari o el celular.

## Editar los precios de la calculadora

Los precios están en el array `SERVICES` dentro de `index.html`, en soles `[mínimo, máximo]` antes del ajuste por zona. El ajuste por zona está en `ZONE_FACTOR` (Lima Norte y Sur 0.85× sobre Centro/Este). Edita esos valores y se actualiza todo solo.

## Notas

- Todo el texto, incluidos los mensajes de error de los formularios, está en español peruano.
- Los precios llevan disclaimer visible: son de referencia, no cotización.
- El sitio es mobile-first (probado a 375px, 768px y 1440px).
- Sin cookies, sin tracking, sin backend.


## Datos y API (oct-2026)

- **Fuente única de datos:** `data/datos.json` (servicios y precios, factor por zona, síntomas del triaje, clínicas 24h y distritos).
  Para cambiar un precio: edita `datos.json` y corre `node scripts/sincronizar-datos.js` (lo copia dentro de `index.html`).
- **API pública** (Netlify Function, `netlify/functions/api.js`):
  - `/api/precio?servicio=castra&especie=gato&distrito=Surco`
  - `/api/verificar?servicio=consulta&monto=180&especie=perro&zona=centro`
  - `/api/triaje?sintomas=vomito,respira&especie=perro`
  - `/api/clinicas?distrito=Chorrillos`
  - `/api/servicios`
- **Probar en local, sin instalar nada:** `node scripts/api-local.js` → `http://localhost:8888/api/...`
- **Publicar con la API:** las funciones no se suben con "arrastrar carpeta". Usa la CLI de Netlify:
  `npm i -g netlify-cli && netlify login && netlify link && netlify deploy --build --prod`
  (`netlify.toml` arma `dist/` solo con lo público: no se suben los .md, .gs ni respaldos).
- **Agente de IA:** ver `agente/README.md`.
