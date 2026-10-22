"""
Pati, el agente de Patitaspe.

Un agente de IA que atiende a dueños de mascotas en Lima: decide qué herramienta usar
(precios, triaje, clínicas 24h, citas, derivar a una persona), actúa sobre sistemas reales
vía API y sabe cuándo pasarle el caso a un humano.

Uso:
    python agente.py            # chat en la terminal
    python agente.py --ver      # además muestra cada herramienta que usa el agente
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from herramientas import DEFINICIONES, ejecutar, registrar_evento

MODELO = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_PASOS = 8  # tope de llamadas a herramientas por turno, para que nunca entre en bucle


def instrucciones() -> str:
    ahora = datetime.now(ZoneInfo("America/Lima"))
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    hoy = f"{dias[ahora.weekday()]} {ahora:%Y-%m-%d}, {ahora:%H:%M}"
    return f"""Eres Pati, el asistente de Patitaspe (patitaspe.com) para dueños de perros y gatos en Lima, Perú.
Hoy es {hoy} (hora de Lima).

Cómo hablas: español peruano, cálido y directo, mensajes cortos como en WhatsApp. Sin tecnicismos.
Si te preguntan, dices que eres un asistente de IA.

Reglas, en este orden de prioridad:
1. Seguridad primero. Si el cliente describe síntomas, usa evaluar_urgencia antes que nada.
   - Nivel rojo: dile que vaya YA a una clínica 24h, usa buscar_clinicas_24h para su zona y dale nombre,
     dirección y teléfono. No ofrezcas citas ni hables de precios salvo que lo pregunte.
   - Nivel ámbar: recomienda verlo hoy y ofrece agendar una cita.
   - Nunca diagnostiques ni recetes medicamentos o dosis. Eres orientación, no veterinario.
2. Precios: usa siempre consultar_precio o verificar_presupuesto. Nunca inventes montos.
   Aclara que son rangos de referencia en Lima, no el tarifario de una clínica.
   Si falta especie, tamaño (perros) o distrito, pregúntalo en una sola línea.
3. Citas: junta nombre del cliente, teléfono, nombre y especie de la mascota, motivo, día y hora.
   Repite los datos y pide un "sí" antes de usar agendar_cita. Horario de atención: lunes a sábado, 9:00 a 19:00.
4. Deriva a una persona con derivar_a_humano si el cliente lo pide, si hay un reclamo, si es algo que
   no puedes resolver, o si una herramienta falla dos veces.
5. Si una herramienta responde con error, explícalo simple y busca otra forma, sin inventar datos.
"""


class Agente:
    def __init__(self, cliente=None, ver_herramientas: bool = False):
        if cliente is None:
            import anthropic

            cliente = anthropic.Anthropic()
        self.cliente = cliente
        self.historial: list[dict] = []
        self.ver = ver_herramientas
        self.sesion = uuid.uuid4().hex[:8]
        self.traza: list[dict] = []  # herramientas usadas, para la demo y para medir

    def responder(self, mensaje: str) -> str:
        self.historial.append({"role": "user", "content": mensaje})
        for _ in range(MAX_PASOS):
            r = self.cliente.messages.create(
                model=MODELO, max_tokens=1024, system=instrucciones(),
                tools=DEFINICIONES, messages=self.historial,
            )
            self.historial.append({"role": "assistant", "content": r.content})
            if r.stop_reason != "tool_use":
                texto = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()
                registrar_evento("agente", {"sesion": self.sesion, "mensaje": mensaje[:500], "respuesta": texto[:1000],
                                            "herramientas": [t["herramienta"] for t in self.traza]})
                return texto
            resultados = []
            for b in r.content:
                if getattr(b, "type", "") != "tool_use":
                    continue
                salida = ejecutar(b.name, dict(b.input))
                self.traza.append({"herramienta": b.name, "entrada": dict(b.input), "ok": salida.get("ok")})
                if self.ver:
                    print(f"   ⚙️  {b.name}({json.dumps(dict(b.input), ensure_ascii=False)}) → "
                          f"{json.dumps(salida, ensure_ascii=False)[:160]}…")
                resultados.append({"type": "tool_result", "tool_use_id": b.id,
                                   "content": json.dumps(salida, ensure_ascii=False),
                                   "is_error": not salida.get("ok", False)})
            self.historial.append({"role": "user", "content": resultados})
        return "Disculpa, me enredé con tu consulta. Te paso con una persona del equipo."


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Falta ANTHROPIC_API_KEY. Copia .env.example a .env, pon tu clave y corre: set -a; source .env; set +a")
    agente = Agente(ver_herramientas="--ver" in sys.argv)
    print("🐾 Pati de Patitaspe. Escribe tu consulta (o 'salir').\n")
    while True:
        try:
            m = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if m.lower() in {"salir", "exit", "chau"}:
            break
        if m:
            print(f"\nPati: {agente.responder(m)}\n")


if __name__ == "__main__":
    main()
