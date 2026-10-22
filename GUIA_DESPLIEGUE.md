# Guía para lanzar Patitaspe hoy

El código ya está 100% listo e instrumentado. Lo que falta es comprar el dominio,
crear 4 cuentas gratis y pegar 3 IDs en un solo lugar del `index.html` (el objeto
`CONFIG`, arriba del todo en el `<script>`). Tiempo estimado: 30–45 minutos.

---

## Paso 1 — Comprar el dominio (lo único que cuesta plata)

- Entra a **punto.pe** (NIC Perú) y registra **patitaspe.com**.
- Costo aprox.: **S/103–130 al año**.
- Es lo único obligatorio para arrancar. Todo lo demás corre gratis al inicio.

## Paso 2 — Crear las cuentas gratis

1. **Hosting — Cloudflare Pages** (recomendado: gratis y permite uso comercial).
   Alternativas: Netlify (igual) o Vercel (su plan gratis es solo "personal";
   para comercial sería plan Pro de pago — por eso recomiendo Cloudflare).
2. **Formspree** (formspree.io) — para recibir los correos. Crea un formulario,
   copia su **ID** (lo que va después de `/f/` en la URL del form).
3. **Google Analytics 4** (analytics.google.com) — crea una propiedad,
   copia el **Measurement ID** (formato `G-XXXXXXXXXX`).
4. **Mailchimp** (mailchimp.com) — gratis hasta ~500 contactos. Es donde
   enviarás el "tarifario" y los recordatorios de la cartilla (manual al inicio).
5. **Base de datos (opcional pero recomendado)** — sigue las instrucciones del
   archivo `base-de-datos-apps-script.gs` para crear el Google Sheet que guarda
   TODO lo que escriben los clientes (incluido el oro: los precios del verificador).

## Paso 3 — Pegar los IDs en el código

Abre `index.html`, busca `const CONFIG` (está arriba en el `<script>`) y llena:

```js
const CONFIG = {
  GA_ID: 'G-XXXXXXXXXX',          // de Google Analytics
  FORMSPREE_ID: 'xxxxxxx',        // lo que va después de /f/ en Formspree
  SHEET_ENDPOINT: 'https://script.google.com/macros/s/.../exec'  // del Apps Script (opcional)
};
```

Con eso, los 6 formularios apuntan solos a tu Formspree, se activa la analítica y
empieza a guardarse cada dato en tu Sheet. No tienes que tocar nada más.

## Paso 4 — Subir la página

Opción más simple (Cloudflare Pages o Netlify):
1. Entra a tu cuenta → "Create / Add site" → "Deploy manually" (drag & drop).
2. Arrastra la **carpeta `patitas-pe` completa** (con `assets/`, `assets/audio/`,
   `robots.txt`, `sitemap.xml`, `index.html`). No subas los `.md` ni el `.gs`.
3. En segundos tienes una URL temporal (ej: `patitas.pages.dev`) con HTTPS.

## Paso 5 — Conectar tu dominio

- En el hosting: "Custom domain" → escribe `patitaspe.com`.
- Te dará unos registros DNS (o nameservers). Cópialos en el panel de punto.pe.
- Espera la propagación (minutos a unas horas). HTTPS se activa solo.

## Paso 6 — Verificar que todo jala (en el dominio ya con HTTPS)

- [ ] Envía un correo de prueba desde cada formulario → llega a Formspree.
- [ ] Abre Analytics → "Tiempo real" → navega la página → te ves ahí.
- [ ] Usa el verificador y la calculadora → aparecen filas en tu Google Sheet.
- [ ] En un celular real: probar audio de la radio y el botón "compartir imagen"
      (este solo funciona en HTTPS, por eso se prueba ya desplegado).

## Paso 7 — Después de lanzar (esta semana)

- [ ] **Google Search Console**: agrega patitaspe.com, verifica y envía el `sitemap.xml`
      para que Google te indexe.
- [ ] **Mailchimp**: arma el correo del "tarifario" y la plantilla de recordatorio
      de vacunas. Exporta los correos de Formspree e impórtalos.
- [ ] **Legal**: que un abogado revise la Política de Privacidad (recolectas datos
      personales — Ley N° 29733) y la estructura del plan prepago.
- [ ] **Directorio de vets**: llamar a las 3 clínicas de confianza media para
      confirmar teléfono antes de fiarte 100% (DR.VET, Pet Time, Maskoteka).

---

## Qué dato vas a poder sacar (tu objetivo de validación)

- **Google Analytics**: cuánta gente entra, de dónde, qué herramienta usa más,
  cuántos dejan correo (tu embudo de conversión = tu métrica de validación).
- **Google Sheet (base de datos)**: fila por fila de cada cálculo, verificación,
  triaje, cartilla y, sobre todo, **disposición a pagar** (tier, monto, distrito).
- **El dataset de precios**: cada verificación guarda servicio + zona + monto que
  le cobraron + veredicto. En unos meses tienes el único mapa real de precios
  veterinarios de Lima. Eso no lo tiene nadie.
- **Formspree**: tu lista de correos (futuros clientes), ya enriquecida con de
  dónde vino cada uno y qué herramientas usó (eso lo hace la capa de atribución).

## Costo total para arrancar

- Dominio: ~S/110/año. Todo lo demás: **gratis** en los planes free.
- Cuando crezca el volumen (>50 correos/mes o >500 contactos): +US$30–50/mes.
