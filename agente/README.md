# Pati — agente de IA de Patitaspe

Pati atiende a dueños de perros y gatos en Lima por chat. No solo conversa: **decide qué herramienta
usar y actúa sobre sistemas reales**, con reglas de seguridad claras y derivación a una persona.

```
Cliente ──► Pati (Claude + tool use) ──► API de patitaspe.com ──► data/datos.json (misma fuente que la web)
                    │                 └► Google Calendar (citas)
                    └► Supabase (registro de cada conversación, triaje, cita y derivación)
```

## Qué puede hacer

| Herramienta | Qué hace | Sistema |
|---|---|---|
| `evaluar_urgencia` | Triaje rojo / ámbar / verde con 17 señales de alarma | API Patitaspe |
| `buscar_clinicas_24h` | Clínicas 24h por zona o distrito | API Patitaspe |
| `consultar_precio` | Rango de precio por servicio, especie, tamaño y distrito | API Patitaspe |
| `verificar_presupuesto` | Dice si una cotización es justa o cara | API Patitaspe |
| `agendar_cita` | Revisa disponibilidad y agenda (o deja la solicitud pendiente) | Google Calendar |
| `derivar_a_humano` | Pasa el caso al equipo con un resumen | Supabase / WhatsApp |

## Decisiones de diseño

- **Seguridad antes que venta:** ante síntomas, el agente hace triaje primero; si es rojo, manda a una clínica 24h y no ofrece citas.
- **Cero precios inventados:** los montos salen siempre de la API, que lee el mismo `datos.json` que la calculadora de la web.
- **Confirmación antes de actuar:** repite los datos de la cita y pide un "sí" antes de agendar.
- **Sabe cuándo parar:** máximo 8 pasos por turno y derivación si una herramienta falla dos veces.
- **Medible:** cada conversación, triaje, cita y derivación queda en Supabase (`origen = agente`).

## Probarlo

```bash
cd agente
pip install -r requirements.txt
cp .env.example .env          # pon tu ANTHROPIC_API_KEY (y Supabase si quieres registrar)
set -a; source .env; set +a

# Si la API aún no está publicada en patitaspe.com, levántala en tu compu:
node ../scripts/api-local.js &           # y en .env: PATITAS_API=http://localhost:8888/api

python agente.py --ver        # chat en la terminal, mostrando qué herramienta usa
python demo.py                # 3 casos: precio, emergencia de noche, cita
python test_agente.py         # pruebas (no gastan API de Claude)
```

## Siguiente paso

Conectarlo a WhatsApp (Twilio o la API de WhatsApp Business): el mismo `Agente.responder()` sirve como backend del webhook.
