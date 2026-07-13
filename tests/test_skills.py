"""
tests/test_skills.py
--------------------
Pruebas unitarias de las skills individuales.

Verifica que cada skill:
  - Se inicializa correctamente con un AgentContext.
  - Devuelve mensajes de error apropiados cuando el contexto está vacío.
  - Ejecuta correctamente su lógica cuando hay datos en el contexto.

Nota: NormalizeSkill se prueba con el archivo sample_transactions.json
real del proyecto. El resto de skills usan un contexto pre-cargado.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agent.context import AgentContext
from models.transaction import Transaction, TransactionStatus
from skills.normalize.skill import NormalizeSkill
from skills.validate.skill import ValidateSkill
from skills.metrics.skill import MetricsSkill
from skills.search.skill import SearchSkill
from skills.export.skill import ExportSkill
from skills.report.skill import ReportSkill

# Ruta al archivo de muestra del proyecto
SAMPLE_FILE = Path(__file__).parent.parent / "data" / "sample_transactions.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_transaction(
    tx_id="TXN-TEST",
    amount=500.0,
    currency="USD",
    timestamp="2024-01-15T10:30:00Z",
    status=TransactionStatus.SUCCESS,
    is_valid=True,
    errors=None,
) -> Transaction:
    """Crea una Transaction de prueba."""
    tx = Transaction(
        id=tx_id,
        amount=amount,
        currency=currency,
        timestamp=timestamp,
        status=status,
        source="FormatA",
        is_valid=is_valid,
        validation_errors=errors or [],
    )
    return tx


@pytest.fixture
def empty_ctx() -> AgentContext:
    """Contexto vacío (sin transacciones)."""
    return AgentContext()


@pytest.fixture
def loaded_ctx() -> AgentContext:
    """Contexto pre-cargado con transacciones de prueba."""
    ctx = AgentContext()
    ctx.transactions = [
        _make_transaction("TXN-001", 1500.00, "USD", status=TransactionStatus.SUCCESS),
        _make_transaction("TXN-002", 800.00, "EUR", status=TransactionStatus.PENDING),
        _make_transaction("TXN-003", 0.0, "USD", is_valid=False, errors=["Monto inválido"]),
        _make_transaction("TXN-004", 200.00, "MXN", status=TransactionStatus.FAILED),
    ]
    ctx.valid = [tx for tx in ctx.transactions if tx.is_valid]
    ctx.invalid = [tx for tx in ctx.transactions if not tx.is_valid]
    ctx.last_file = SAMPLE_FILE
    return ctx


# ---------------------------------------------------------------------------
# NormalizeSkill
# ---------------------------------------------------------------------------

class TestNormalizeSkill:

    def test_normaliza_archivo_muestra(self, empty_ctx):
        """Debe cargar y normalizar el archivo de muestra correctamente."""
        if not SAMPLE_FILE.exists():
            pytest.skip("sample_transactions.json no encontrado")

        skill = NormalizeSkill(context=empty_ctx)
        result = skill.execute("normaliza", filepath=SAMPLE_FILE)

        assert "✔" in result
        assert len(empty_ctx.transactions) > 0

    def test_archivo_no_encontrado(self, empty_ctx):
        """Debe devolver error si el archivo no existe."""
        skill = NormalizeSkill(context=empty_ctx)
        result = skill.execute("normaliza", filepath=Path("/no/existe.json"))
        assert "✘" in result or "Error" in result

    def test_contexto_vacio_antes_de_normalizar(self, empty_ctx):
        """El contexto empieza vacío."""
        assert not empty_ctx.is_loaded()


# ---------------------------------------------------------------------------
# ValidateSkill
# ---------------------------------------------------------------------------

class TestValidateSkill:

    def test_valida_con_datos(self, loaded_ctx):
        """Debe actualizar is_valid y separar válidas e inválidas."""
        skill = ValidateSkill(context=loaded_ctx)
        result = skill.execute("valida las transacciones")

        assert "✔" in result
        assert "Válidas:" in result
        assert "Inválidas:" in result

    def test_sin_datos_devuelve_advertencia(self, empty_ctx):
        """Sin datos cargados debe devolver mensaje de advertencia."""
        skill = ValidateSkill(context=empty_ctx)
        result = skill.execute("valida")
        assert "No hay transacciones" in result or "[Agente]" in result


# ---------------------------------------------------------------------------
# MetricsSkill
# ---------------------------------------------------------------------------

class TestMetricsSkill:

    def test_calcula_metricas(self, loaded_ctx):
        """Debe calcular métricas y actualizar el contexto."""
        skill = MetricsSkill(context=loaded_ctx)
        result = skill.execute("métricas")

        assert "MÉTRICAS" in result
        assert loaded_ctx.metrics is not None
        assert loaded_ctx.metrics["total_processed"] == len(loaded_ctx.transactions)

    def test_sin_datos_devuelve_advertencia(self, empty_ctx):
        """Sin datos debe devolver advertencia."""
        skill = MetricsSkill(context=empty_ctx)
        result = skill.execute("métricas")
        assert "No hay transacciones" in result or "[Agente]" in result


# ---------------------------------------------------------------------------
# SearchSkill
# ---------------------------------------------------------------------------

class TestSearchSkill:

    def test_busqueda_por_id(self, loaded_ctx):
        """Debe encontrar la transacción por ID parcial."""
        skill = SearchSkill(context=loaded_ctx)
        result = skill.execute("buscar TXN-001")
        assert "TXN-001" in result

    def test_busqueda_por_moneda(self, loaded_ctx):
        """Debe filtrar por código de moneda."""
        skill = SearchSkill(context=loaded_ctx)
        result = skill.execute("buscar USD")
        assert "USD" in result

    def test_busqueda_por_estado(self, loaded_ctx):
        """Debe filtrar por estado."""
        skill = SearchSkill(context=loaded_ctx)
        result = skill.execute("buscar exitosas")
        assert "SUCCESS" in result or "encontradas" in result

    def test_sin_resultados(self, loaded_ctx):
        """Debe informar cuando no hay resultados."""
        skill = SearchSkill(context=loaded_ctx)
        result = skill.execute("buscar XYZ123INEXISTENTE")
        assert "No se encontraron" in result

    def test_sin_datos_devuelve_advertencia(self, empty_ctx):
        """Sin datos debe devolver advertencia."""
        skill = SearchSkill(context=empty_ctx)
        result = skill.execute("buscar algo")
        assert "No hay transacciones" in result or "[Agente]" in result


# ---------------------------------------------------------------------------
# ExportSkill
# ---------------------------------------------------------------------------

class TestExportSkill:

    def test_exporta_archivos(self, loaded_ctx, tmp_path):
        """Debe crear valid.json e invalid.json en el directorio temporal."""
        skill = ExportSkill(context=loaded_ctx)
        result = skill.execute("exporta", output_dir=tmp_path)

        assert "✔" in result
        assert (tmp_path / "valid.json").exists()
        assert (tmp_path / "invalid.json").exists()

    def test_contenido_valid_json(self, loaded_ctx, tmp_path):
        """valid.json debe contener solo transacciones válidas."""
        skill = ExportSkill(context=loaded_ctx)
        skill.execute("exporta", output_dir=tmp_path)

        with open(tmp_path / "valid.json", encoding="utf-8") as f:
            data = json.load(f)
        assert all("validation_errors" not in tx for tx in data)

    def test_contenido_invalid_json(self, loaded_ctx, tmp_path):
        """invalid.json debe contener errores de validación."""
        skill = ExportSkill(context=loaded_ctx)
        skill.execute("exporta", output_dir=tmp_path)

        with open(tmp_path / "invalid.json", encoding="utf-8") as f:
            data = json.load(f)
        assert all("validation_errors" in tx for tx in data)

    def test_sin_datos_devuelve_advertencia(self, empty_ctx):
        """Sin datos debe devolver advertencia."""
        skill = ExportSkill(context=empty_ctx)
        result = skill.execute("exporta")
        assert "No hay transacciones" in result or "[Agente]" in result


# ---------------------------------------------------------------------------
# ReportSkill
# ---------------------------------------------------------------------------

class TestReportSkill:

    def test_genera_reporte_markdown(self, loaded_ctx, tmp_path):
        """Debe generar un archivo Markdown con el resumen."""
        report_path = tmp_path / "report.md"
        skill = ReportSkill(context=loaded_ctx)
        result = skill.execute("genera reporte", output_path=report_path)

        assert "✔" in result
        assert report_path.exists()

    def test_contenido_reporte(self, loaded_ctx, tmp_path):
        """El reporte debe contener secciones clave."""
        report_path = tmp_path / "report.md"
        skill = ReportSkill(context=loaded_ctx)
        skill.execute("genera reporte", output_path=report_path)

        content = report_path.read_text(encoding="utf-8")
        assert "Resumen ejecutivo" in content
        assert "Métricas por estado" in content
        assert "Totales por moneda" in content

    def test_sin_datos_devuelve_advertencia(self, empty_ctx):
        """Sin datos debe devolver advertencia."""
        skill = ReportSkill(context=empty_ctx)
        result = skill.execute("genera reporte")
        assert "No hay transacciones" in result or "[Agente]" in result
