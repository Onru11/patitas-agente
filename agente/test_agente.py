"""
Pruebas sin gastar API de Claude: un modelo simulado decide usar herramientas y
verificamos que el agente las ejecute contra la API de Patitaspe y cierre la respuesta.

    node ../scripts/api-local.js &      # en otra terminal
    PATITAS_API=http://localhost:8888/api python test_agente.py
"""
import os
import unittest
from types import SimpleNamespace as NS

os.environ.setdefault("PATITAS_API", "http://localhost:8888/api")

import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import herramientas  # noqa: E402
from agente import Agente  # noqa: E402

herramientas.CITAS_LOCAL = Path(tempfile.gettempdir()) / "citas_prueba.jsonl"  # no ensucia las citas reales
herramientas.SUPABASE_URL = ""  # las pruebas no escriben en tu base de datos


class ModeloSimulado:
    """Imita client.messages.create: primero pide herramientas, luego responde texto."""

    def __init__(self, guion):
        self.guion = list(guion)
        self.messages = self
        self.llamadas = []

    def create(self, **kw):
        self.llamadas.append(kw)
        paso = self.guion.pop(0)
        if paso[0] == "tool":
            bloques = [NS(type="tool_use", id=f"t{i}", name=n, input=e) for i, (n, e) in enumerate(paso[1])]
            return NS(stop_reason="tool_use", content=bloques)
        return NS(stop_reason="end_turn", content=[NS(type="text", text=paso[1])])


class PruebasHerramientas(unittest.TestCase):
    def test_precio(self):
        r = herramientas.consultar_precio(servicio="castra", especie="gato", distrito="Surco")
        self.assertTrue(r["ok"]); self.assertEqual(r["items"][0]["min"], 180)

    def test_triaje_rojo(self):
        r = herramientas.evaluar_urgencia(sintomas=["toxico", "convul"], especie="perro")
        self.assertEqual(r["nivel"], "rojo")

    def test_clinicas(self):
        r = herramientas.buscar_clinicas_24h(distrito="Chorrillos")
        self.assertTrue(r["clinicas"])

    def test_verificar_caro(self):
        r = herramientas.verificar_presupuesto(servicio="castra", monto=500, especie="gato", distrito="Surco")
        self.assertEqual(r["veredicto"], "caro")

    def test_cita_sin_calendario_queda_pendiente(self):
        r = herramientas.agendar_cita(nombre_cliente="Prueba", telefono="999", nombre_mascota="Luna",
                                      especie="perro", motivo="Diarrea", fecha_hora="2026-10-23T10:00")
        self.assertEqual(r["estado"], "solicitud_registrada")

    def test_fecha_invalida(self):
        r = herramientas.agendar_cita(nombre_cliente="P", telefono="9", nombre_mascota="L", especie="perro",
                                      motivo="x", fecha_hora="mañana")
        self.assertFalse(r["ok"])


class PruebasAgente(unittest.TestCase):
    def test_emergencia_usa_triaje_y_clinicas(self):
        modelo = ModeloSimulado([
            ("tool", [("evaluar_urgencia", {"sintomas": ["toxico", "convul"], "especie": "perro"})]),
            ("tool", [("buscar_clinicas_24h", {"distrito": "Chorrillos"})]),
            ("text", "Ve ya a Pet Time Chorrillos."),
        ])
        a = Agente(cliente=modelo)
        respuesta = a.responder("mi perro comió chocolate y tiembla, estoy en Chorrillos")
        self.assertIn("Pet Time", respuesta)
        self.assertEqual([t["herramienta"] for t in a.traza], ["evaluar_urgencia", "buscar_clinicas_24h"])
        self.assertTrue(all(t["ok"] for t in a.traza))
        tool_results = [m["content"][0] for m in a.historial
                        if m["role"] == "user" and isinstance(m["content"], list)]
        ultimo = tool_results[-1]
        self.assertEqual(ultimo["type"], "tool_result")
        self.assertIn("Pet Time", ultimo["content"])

    def test_no_entra_en_bucle(self):
        modelo = ModeloSimulado([("tool", [("consultar_precio", {"especie": "perro", "zona": "centro"})])] * 10)
        a = Agente(cliente=modelo)
        self.assertIn("persona", a.responder("precios?"))
        self.assertLessEqual(len(modelo.llamadas), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
