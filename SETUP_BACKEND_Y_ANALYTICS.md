# Patitaspe — Setup de backend (Supabase) y analítica (PostHog)

Objetivo: que tu web deje de perder leads en silencio y que tu **lista de contactos
sea un activo que sí puedes consultar**. En el modelo "audiencia primero", esa lista
es el negocio; el resto es tráfico.

Tiempo total: ~30–40 min. No necesitas saber programar; es pegar llaves.

---

## Paso 0 — Verificar si Notion estuvo guardando (5 min, hazlo igual)

Hasta hoy la web enviaba los datos "a ciegas" (no sabía si Notion guardaba o fallaba).
Antes de migrar, confirma si has estado perdiendo data:

1. Abre tu proyecto de Apps Script (script.google.com → el proyecto de Patitaspe).
2. Selecciona la función `testNotion` y dale **Ejecutar**.
3. Abre tu base de Notion "Patitaspe — Datos de la web". ¿Apareció una fila de prueba?
   - **Sí** → la captura funcionaba; igual conviene migrar a Supabase por las razones de abajo.
   - **No / error** → estabas perdiendo leads. Con más razón seguimos.
4. Mira cuántas filas reales tiene esa base. Eso es todo lo que capturaste hasta hoy.

> A partir de ahora la web SÍ confirma cada guardado (verás un aviso en la consola del
> navegador si algo no se guarda), así que este punto ciego desaparece.

---

## Paso 1 — Crear Supabase y el esquema (10 min)

1. Entra a https://supabase.com → **Start your project** → crea cuenta (gratis).
2. **New project**. Ponle nombre (ej. `patitaspe`), elige región **East US** (la más
   cercana/estable para Perú) y guarda la contraseña de la base de datos.
3. Cuando termine de crearse, ve a **SQL Editor** → **New query**.
4. Abre el archivo `supabase_esquema.sql` (está en esta misma carpeta), copia TODO su
   contenido, pégalo y dale **Run**. Debe decir "Success".
5. Ve a **Settings → API** y copia dos cosas:
   - **Project URL** (ej. `https://abcdxyz.supabase.co`)
   - **anon public** key (una cadena larga; la "anon", NO la "service_role").

> Importante: la llave que pones en la web es la **anon public**. Nunca pongas la
> `service_role` en la página (esa es solo para el servidor / tu dashboard).

---

## Paso 2 — Crear PostHog (10 min)

1. Entra a https://posthog.com → **Get started free**.
2. Crea el proyecto. Elige región **US** o **EU** (recuérdala).
3. En **Project Settings** copia la **Project API Key** (empieza con `phc_`).
4. El host es:
   - US → `https://us.i.posthog.com`
   - EU → `https://eu.i.posthog.com`

PostHog reemplaza a Google Analytics. GA se bloquea muchísimo (sobre todo en audiencias
como Reddit), por eso "no funcionaba" bien. PostHog además te muestra el **embudo**:
cuánta gente usó una herramienta y cuánta dejó correo.

---

## Paso 3 — Pegar las llaves en la web (5 min)

Abre `index.html`, busca el bloque `const CONFIG = {` (cerca de la línea 1281) y llena:

```js
const CONFIG = {
  SUPABASE_URL:      'https://abcdxyz.supabase.co',   // <- tu Project URL
  SUPABASE_ANON_KEY: 'eyJhbGciOi...',                 // <- tu anon public key
  POSTHOG_KEY:       'phc_xxxxxxxx',                  // <- tu Project API Key
  POSTHOG_HOST:      'https://us.i.posthog.com',      // us o eu según tu región
  GA_ID:             '',                              // déjalo VACÍO (ya no usamos GA)
  DATA_ENDPOINT:     'https://script.google.com/.../exec', // déjalo: respaldo a Notion
  FORMSPREE_ID:      '',
  DATA_SECRET:       ''
};
```

> Mientras `DATA_ENDPOINT` siga puesto, la web escribe en **Supabase Y Notion** a la vez
> (dual-write). Así no pierdes nada durante la transición. Cuando confirmes que Supabase
> recibe bien (unos días), puedes vaciar `DATA_ENDPOINT` para quedarte solo con Supabase.

Guarda y vuelve a desplegar la página (sube el `index.html` como siempre lo haces).

---

## Paso 4 — Probar que TODO guarda (5 min)

1. Abre la web ya desplegada. Abre la consola del navegador (F12 → Console).
2. Usa la calculadora y **deja tu correo** en "enviarme el estimado".
3. Verifica:
   - **Supabase** → Table Editor → tabla `eventos`: debe aparecer tu fila.
   - **Consola**: si algo falló verás un aviso `[Patitaspe] Supabase NO guardó ...`.
     Si no hay aviso, guardó bien.
   - **PostHog** → Activity / Live events: debe verse tu visita y el evento.

Si la fila aparece en `eventos`, ya tienes captura confiable y consultable. Listo.

---

## Cómo leer tu activo (lo que de verdad importa)

En Supabase → **SQL Editor**, corre:

- `select * from public.contactos;` → tu **lista de correos** deduplicada, con zona,
  mascota, tier de interés y si mostró interés en el plan. Esto es lo que conviertes
  cuando abras la clínica.
- `select * from public.embudo;` → cuántos usaron cada herramienta y **qué % dejó
  correo**. Tu KPI del modelo B no es tráfico, es esta tasa de captura.
- `select zona, count(*) from public.eventos group by zona order by 2 desc;` → dónde se
  concentra el interés. Insumo directo para decidir DÓNDE entrar (Lima general → zona).

En PostHog: arma un **Funnel** visita → usó herramienta → dejó correo. Eso te dice
dónde se cae la gente antes de convertir en contacto.

---

## Notas honestas

- **Spam**: cualquiera puede mandar filas a `eventos` (es el precio de capturar sin
  registro). A bajo volumen no importa. Si crece, se agrega un captcha (Cloudflare
  Turnstile) o se activa `DATA_SECRET`. No lo necesitas hoy.
- **PII / confianza**: estás guardando correos. Las casillas ya dicen "te avisamos
  cuando abramos" — mantén ese mensaje (es tu consentimiento y refuerza tu marca de
  transparencia). No uses esos correos para nada que no prometiste.
- **No confundas audiencia con validación**: estas herramientas miden tráfico y captura.
  La prueba de que el negocio paga sigue siendo del estudio de mercado (la consultora) +
  el due diligence de clínicas. La web es marketing y data, no el gate.
