"""
Herramientas del agente de Patitaspe.

Cada herramienta llama a la API pública de patitaspe.com (misma fuente de datos que la web)
o actúa sobre un sistema externo (Google Calendar, Supabase).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

API = os.environ.get("PATITAS_API", "https://patitaspe.com/api").rstrip("/")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "")
CREDENCIALES_GOOGLE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
ZONA_HORARIA = "America/Lima"
CITAS_LOCAL = Path(__file__).with_name("citas_pendientes.jsonl")


# ---------------------------------------------------------------- definiciones para Claude
DEFINICIONES = [
    {
        "name": "consultar_precio",
        "description": (
            "Devuelve el rango de precio de referencia (en soles) de un servicio veterinario en Lima, "
            "según especie, tamaño del perro y zona o distrito. Úsala SIEMPRE que el cliente pregunte cuánto "
            "cuesta algo; nunca inventes precios. Si no se indica servicio, devuelve todos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "servicio": {"type": "string", "description": "Ej: consulta, vacunas, despar, castra (macho), esteril (hembra), sangre, rayos, eco, hospi, cirugia, dental, emerg"},
                "especie": {"type": "string", "enum": ["perro", "gato"]},
                "tamano": {"type": "string", "enum": ["peq", "med", "gra"], "description": "Solo perros"},
                "distrito": {"type": "string", "description": "Distrito de Lima, ej. Surco, Comas"},
                "zona": {"type": "string", "enum": ["norte", "centro", "sur", "este"]},
            },
            "required": ["especie"],
        },
    },
    {
        "name": "verificar_presupuesto",
        "description": "Compara un monto que le cotizaron al cliente contra el rango normal y dice si es buen precio, justo, en el límite o caro.",
        "input_schema": {
            "type": "object",
            "properties": {
                "servicio": {"type": "string"},
                "monto": {"type": "number", "description": "Monto cotizado en soles"},
                "especie": {"type": "string", "enum": ["perro", "gato"]},
                "tamano": {"type": "string", "enum": ["peq", "med", "gra"]},
                "distrito": {"type": "string"},
                "zona": {"type": "string", "enum": ["norte", "centro", "sur", "este"]},
            },
            "required": ["servicio", "monto", "especie"],
        },
    },
    {
        "name": "evaluar_urgencia",
        "description": (
            "Triaje: clasifica la urgencia (rojo, ámbar, verde) según síntomas. Úsala en cuanto el cliente "
            "describa síntomas, ANTES de hablar de precios o citas. Mapea lo que dice el cliente a estos ids: "
            "convul (convulsiones), respira (le cuesta respirar), encias (encías pálidas/azuladas), "
            "orina (no puede orinar), sangre (vómito o diarrea con sangre), toxico (comió algo tóxico), "
            "barriga (barriga hinchada y dura, arcadas sin vomitar), golpe (atropello o golpe fuerte), "
            "colapso (se desmayó o no se para), sangrado (sangrado que no para), calor (golpe de calor), "
            "vomito (vomitó 2-3 veces sin sangre), nocome (no come hace más de 24h), diarrea (sin sangre), "
            "decaido, cojea, agua (toma u orina mucho más de golpe)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sintomas": {"type": "array", "items": {"type": "string"}},
                "especie": {"type": "string", "enum": ["perro", "gato"]},
            },
            "required": ["sintomas", "especie"],
        },
    },
    {
        "name": "buscar_clinicas_24h",
        "description": "Lista clínicas veterinarias con atención 24 horas en Lima, filtradas por zona o distrito. Úsala ante cualquier urgencia roja.",
        "input_schema": {
            "type": "object",
            "properties": {
                "distrito": {"type": "string"},
                "zona": {"type": "string", "enum": ["norte", "centro", "sur", "este"]},
            },
        },
    },
    {
        "name": "agendar_cita",
        "description": (
            "Agenda una cita en el calendario de la clínica. Úsala SOLO después de confirmar con el cliente "
            "todos los datos y de que diga que sí. Nunca para emergencias rojas (esas van a una clínica 24h ya)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_cliente": {"type": "string"},
                "telefono": {"type": "string"},
                "nombre_mascota": {"type": "string"},
                "especie": {"type": "string", "enum": ["perro", "gato"]},
                "motivo": {"type": "string"},
                "fecha_hora": {"type": "string", "description": "Formato ISO 8601 en hora de Lima, ej. 2026-10-24T10:00"},
                "duracion_min": {"type": "integer", "default": 30},
            },
            "required": ["nombre_cliente", "telefono", "nombre_mascota", "especie", "motivo", "fecha_hora"],
        },
    },
    {
        "name": "derivar_a_humano",
        "description": (
            "Pasa la conversación a una persona del equipo. Úsala si el cliente lo pide, si hay un reclamo, "
            "si pregunta algo fuera de lo que puedes resolver, o si hay una emergencia y no hay clínica en su zona."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {"type": "string"},
                "resumen": {"type": "string", "description": "Resumen de 2-3 líneas para la persona que lo recibe"},
                "urgencia": {"type": "string", "enum": ["alta", "normal"]},
                "telefono": {"type": "string"},
            },
            "required": ["motivo", "resumen", "urgencia"],
        },
    },
]


# ---------------------------------------------------------------- utilidades
def _llamar_api(ruta: str, params: dict) -> dict:
    limpio = {k: (",".join(v) if isinstance(v, list) else v) for k, v in params.items() if v not in (None, "", [])}
    url = f"{API}/{ruta}?{urllib.parse.urlencode(limpio)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "error": f"La API respondió {e.code}"}
    except Exception as e:  # red caída, DNS, etc.
        return {"ok": False, "error": f"No pude conectar con la API de Patitaspe ({e.__class__.__name__})."}


def registrar_evento(tipo: str, datos: dict) -> bool:
    """Guarda una fila en la tabla 'eventos' de Supabase (la misma que usa la web). Insert-only."""
    if not (SUPABASE_URL and SUPABASE_KEY):
        return False
    fila = {
        "tipo": tipo,
        "zona": datos.get("zona") or datos.get("distrito"),
        "mascota": datos.get("especie"),
        "nivel": datos.get("nivel"),
        "veredicto": datos.get("veredicto"),
        "origen": "agente",
        "data": datos,
    }
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/eventos",
        data=json.dumps(fila).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------- herramientas
def consultar_precio(**p) -> dict:
    return _llamar_api("precio", p)


def verificar_presupuesto(**p) -> dict:
    return _llamar_api("verificar", p)


def evaluar_urgencia(**p) -> dict:
    r = _llamar_api("triaje", p)
    if r.get("ok"):
        registrar_evento("triaje", {"especie": p.get("especie"), "nivel": r.get("nivel"), "sintomas": p.get("sintomas")})
    return r


def buscar_clinicas_24h(**p) -> dict:
    return _llamar_api("clinicas", p)


def agendar_cita(**p) -> dict:
    try:
        inicio = datetime.fromisoformat(p["fecha_hora"])
    except (KeyError, ValueError):
        return {"ok": False, "error": "La fecha y hora debe estar en formato ISO, ej. 2026-10-24T10:00."}
    duracion = int(p.get("duracion_min") or 30)
    titulo = f"{p['motivo']} · {p['nombre_mascota']} ({p['especie']})"
    detalle = f"Cliente: {p['nombre_cliente']} · Tel: {p['telefono']}\nAgendado por el agente de Patitaspe."

    if CALENDAR_ID and CREDENCIALES_GOOGLE:
        try:
            from datetime import timedelta

            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            cred = service_account.Credentials.from_service_account_file(
                CREDENCIALES_GOOGLE, scopes=["https://www.googleapis.com/auth/calendar"]
            )
            cal = build("calendar", "v3", credentials=cred, cache_discovery=False)
            fin = inicio + timedelta(minutes=duracion)
            # Revisa que el horario esté libre antes de agendar.
            ocupado = cal.freebusy().query(body={
                "timeMin": inicio.isoformat() + "-05:00", "timeMax": fin.isoformat() + "-05:00",
                "timeZone": ZONA_HORARIA, "items": [{"id": CALENDAR_ID}],
            }).execute()["calendars"][CALENDAR_ID]["busy"]
            if ocupado:
                return {"ok": False, "error": "Ese horario ya está ocupado. Propón otro al cliente."}
            ev = cal.events().insert(calendarId=CALENDAR_ID, body={
                "summary": titulo, "description": detalle,
                "start": {"dateTime": inicio.isoformat(), "timeZone": ZONA_HORARIA},
                "end": {"dateTime": fin.isoformat(), "timeZone": ZONA_HORARIA},
            }).execute()
            registrar_evento("cita", {"especie": p["especie"], "motivo": p["motivo"], "fecha_hora": p["fecha_hora"]})
            return {"ok": True, "estado": "confirmada", "id_evento": ev.get("id"), "fecha_hora": p["fecha_hora"]}
        except Exception as e:
            return {"ok": False, "error": f"No pude agendar en el calendario ({e.__class__.__name__}). Deriva a una persona."}

    # Sin calendario configurado: queda como solicitud pendiente de confirmar por el equipo.
    with CITAS_LOCAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({**p, "registrado": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False) + "\n")
    registrar_evento("cita_solicitada", {"especie": p["especie"], "motivo": p["motivo"], "fecha_hora": p["fecha_hora"]})
    return {
        "ok": True, "estado": "solicitud_registrada",
        "nota": "Calendario no conectado: la solicitud quedó registrada y el equipo la confirmará por WhatsApp.",
    }


def derivar_a_humano(**p) -> dict:
    registrar_evento("derivacion", {"motivo": p.get("motivo"), "resumen": p.get("resumen"), "urgencia": p.get("urgencia")})
    numero = os.environ.get("WHATSAPP_EQUIPO", "")
    return {
        "ok": True, "estado": "derivado",
        "mensaje_para_cliente": "Una persona del equipo continuará la conversación." + (f" WhatsApp: +{numero}" if numero else ""),
    }


EJECUTORES = {
    "consultar_precio": consultar_precio,
    "verificar_presupuesto": verificar_presupuesto,
    "evaluar_urgencia": evaluar_urgencia,
    "buscar_clinicas_24h": buscar_clinicas_24h,
    "agendar_cita": agendar_cita,
    "derivar_a_humano": derivar_a_humano,
}


def ejecutar(nombre: str, entrada: dict) -> dict:
    fn = EJECUTORES.get(nombre)
    if not fn:
        return {"ok": False, "error": f"Herramienta desconocida: {nombre}"}
    try:
        return fn(**entrada)
    except TypeError as e:
        return {"ok": False, "error": f"Faltan o sobran datos para {nombre}: {e}"}
