"""
tests/test_router.py
--------------------
Pruebas unitarias del SkillRouter.

Verifica que cada palabra clave definida en config.py
enruta correctamente a la skill correspondiente.

Cobertura:
  - NormalizeSkill: keywords de normalización/carga.
  - ValidateSkill:  keywords de validación.
  - MetricsSkill:   keywords de métricas.
  - SearchSkill:    keywords de búsqueda.
  - ExportSkill:    keywords de exportación.
  - ReportSkill:    keywords de reporte.
  - Sin coincidencia: devuelve None.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agent.router import SkillRouter
from skills.normalize.skill import NormalizeSkill
from skills.validate.skill import ValidateSkill
from skills.metrics.skill import MetricsSkill
from skills.search.skill import SearchSkill
from skills.export.skill import ExportSkill
from skills.report.skill import ReportSkill


# Registro de skills para los tests
_REGISTRY = {
    "NormalizeSkill": NormalizeSkill,
    "ValidateSkill":  ValidateSkill,
    "MetricsSkill":   MetricsSkill,
    "SearchSkill":    SearchSkill,
    "ExportSkill":    ExportSkill,
    "ReportSkill":    ReportSkill,
}


@pytest.fixture
def router() -> SkillRouter:
    """Instancia el router con el registro completo de skills."""
    r = SkillRouter()
    r.register_skills(_REGISTRY)
    return r


# ---------------------------------------------------------------------------
# Tests de enrutamiento por keyword
# ---------------------------------------------------------------------------

class TestRouterNormalizeSkill:

    @pytest.mark.parametrize("solicitud", [
        "normaliza el archivo",
        "carga el archivo JSON",
        "importa data.json",
    ])
    def test_normaliza_keywords(self, router, solicitud):
        assert router.route(solicitud) is NormalizeSkill


class TestRouterValidateSkill:

    @pytest.mark.parametrize("solicitud", [
        "valida las transacciones",
        "verificar los datos",
        "muéstrame las inválidas",
    ])
    def test_valida_keywords(self, router, solicitud):
        assert router.route(solicitud) is ValidateSkill


class TestRouterMetricsSkill:

    @pytest.mark.parametrize("solicitud", [
        "métricas del archivo",
        "estadísticas generales",
        "muéstrame los totales",
        "stats del procesamiento",
    ])
    def test_metricas_keywords(self, router, solicitud):
        assert router.route(solicitud) is MetricsSkill


class TestRouterSearchSkill:

    @pytest.mark.parametrize("solicitud", [
        "buscar TXN-001",
        "busca por moneda USD",
        "filtrar por estado",
        "encontrar la transacción",
    ])
    def test_buscar_keywords(self, router, solicitud):
        assert router.route(solicitud) is SearchSkill


class TestRouterExportSkill:

    @pytest.mark.parametrize("solicitud", [
        "exporta los resultados",
        "guardar los archivos",
        "genera archivos JSON",
    ])
    def test_exporta_keywords(self, router, solicitud):
        assert router.route(solicitud) is ExportSkill


class TestRouterReportSkill:

    @pytest.mark.parametrize("solicitud", [
        "genera un reporte",
        "informe del sistema",
        "resumen ejecutivo en markdown",
    ])
    def test_reporte_keywords(self, router, solicitud):
        assert router.route(solicitud) is ReportSkill


class TestRouterNoMatch:

    def test_solicitud_desconocida(self, router):
        assert router.route("hola mundo") is None

    def test_cadena_vacia(self, router):
        assert router.route("") is None

    def test_numero(self, router):
        assert router.route("12345") is None


class TestRouterAvailableSkills:

    def test_lista_skills_completa(self, router):
        skills = router.available_skills()
        assert len(skills) == 6
        assert "NormalizeSkill" in skills
        assert "ReportSkill" in skills
