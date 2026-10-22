"""
Demo de 3 casos para grabar en video. Muestra cada herramienta que el agente decide usar.

    python demo.py
"""
from agente import Agente

CASOS = [
    ("1. Consulta de precio", [
        "hola! cuánto me cuesta castrar a mi gato en Surco?",
        "y si en una vet me cobran 500 soles, es mucho?",
    ]),
    ("2. Emergencia de noche", [
        "mi perro se comió una barra de chocolate y está temblando mucho, qué hago?? estoy en Chorrillos",
    ]),
    ("3. Agendar una cita", [
        "mi perrita Luna tiene diarrea desde ayer pero está comiendo normal",
        "sí, quiero una cita para mañana a las 10am. Soy Eduardo, mi cel es 987 569 409",
        "sí, confirma",
    ]),
]

if __name__ == "__main__":
    for titulo, mensajes in CASOS:
        print("\n" + "═" * 70 + f"\n{titulo}\n" + "═" * 70)
        agente = Agente(ver_herramientas=True)
        for m in mensajes:
            print(f"\n👤 Cliente: {m}")
            print(f"\n🐾 Pati: {agente.responder(m)}")
