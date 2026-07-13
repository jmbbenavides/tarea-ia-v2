"""
tests/test_agent.py
-------------------
Pruebas de integración del TransactionAgent.

Verifica que:
  - El agente selecciona la skill correcta para cada solicitud.
  - El pipeline batch completo funciona de extremo a extremo.
  - El agente devuelve mensajes apropiados para solicitudes no reconocidas.
  - El contexto se mantiene entre ejecuciones de skills.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agent.agent import TransactionAgent

SAMPLE_FILE = Path(__file__).parent.parent / "data" / "sample_transactions.json"


@pytest.fixture
def agent() -> TransactionAgent:
    """Instancia un nuevo agente por test."""
    return TransactionAgent()


# ---------------------------------------------------------------------------
# Tests de selección de skill
# ---------------------------------------------------------------------------

class TestAgentSkillSelection:

    def test_normaliza_solicitud(self, agent):
        """El agente debe seleccionar NormalizeSkill para 'normaliza'."""
        result = agent.run("normaliza", filepath=SAMPLE_FILE)
        # La respuesta debe indicar éxito (✔) si el archivo existe
        if SAMPLE_FILE.exists():
            assert "✔" in result
        else:
            pytest.skip("sample_transactions.json no disponible")

    def test_solicitud_desconocida(self, agent):
        """El agente debe devolver mensaje de error para solicitudes no reconocidas."""
        result = agent.run("hola mundo, esto no tiene sentido")
        assert "No se pudo determinar" in result or "Skills disponibles" in result

    def test_metricas_sin_datos(self, agent):
        """MetricsSkill sin datos cargados debe devolver advertencia."""
        result = agent.run("estadísticas del sistema")
        assert "No hay transacciones" in result or "[Agente]" in result


# ---------------------------------------------------------------------------
# Tests de pipeline completo
# ---------------------------------------------------------------------------

class TestAgentPipeline:

    def test_pipeline_batch_completo(self, agent):
        """El pipeline batch debe ejecutar las 4 fases y generar resultados."""
        if not SAMPLE_FILE.exists():
            pytest.skip("sample_transactions.json no disponible")

        result = agent.run_pipeline(SAMPLE_FILE)

        # Debe haber resultado de al menos la normalización
        assert result is not None
        assert len(result) > 0

    def test_contexto_persiste_entre_skills(self, agent):
        """El contexto debe mantenerse entre ejecuciones consecutivas."""
        if not SAMPLE_FILE.exists():
            pytest.skip("sample_transactions.json no disponible")

        # Paso 1: normalizar
        agent.run("normaliza", filepath=SAMPLE_FILE)
        assert agent.context.is_loaded()
        n_transactions = len(agent.context.transactions)

        # Paso 2: validar (usa el contexto del paso 1)
        agent.run("valida las transacciones")
        assert len(agent.context.valid) + len(agent.context.invalid) == n_transactions

        # Paso 3: métricas
        agent.run("estadísticas del sistema")
        assert agent.context.metrics is not None
        assert agent.context.metrics["total_processed"] == n_transactions


# ---------------------------------------------------------------------------
# Tests de log del agente
# ---------------------------------------------------------------------------

class TestAgentLogging:

    def test_session_log_registra_solicitudes(self, agent):
        """Cada solicitud debe registrarse en el log de sesión."""
        agent.run("hola solicitud de prueba")
        assert len(agent.context.session_log) >= 1

    def test_pipeline_registra_multiples_entradas(self, agent):
        """El pipeline batch debe generar múltiples entradas en el log."""
        if not SAMPLE_FILE.exists():
            pytest.skip("sample_transactions.json no disponible")
        agent.run_pipeline(SAMPLE_FILE)
        assert len(agent.context.session_log) >= 4
