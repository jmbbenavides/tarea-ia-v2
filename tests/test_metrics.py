"""
tests/test_metrics.py
---------------------
Pruebas unitarias para el servicio de métricas.

Cubre:
  - compute_metrics: conteos, by_status, total_by_currency.
  - format_metrics: verifica que el formato incluye los datos clave.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.transaction import Transaction, TransactionStatus
from services.metrics import compute_metrics, format_metrics
from services.validator import validate


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _make_tx(
    tx_id: str,
    amount: float,
    currency: str,
    status: TransactionStatus,
    is_valid: bool = True,
) -> Transaction:
    tx = Transaction(
        id=tx_id,
        amount=amount,
        currency=currency,
        timestamp="2024-01-01T00:00:00Z",
        status=status,
        source="TestSource",
        is_valid=is_valid,
    )
    return tx


# ---------------------------------------------------------------------------
# Pruebas: compute_metrics
# ---------------------------------------------------------------------------

class TestComputeMetrics:

    def _make_dataset(self):
        return [
            _make_tx("TX-1", 100.0, "USD", TransactionStatus.SUCCESS),
            _make_tx("TX-2", 200.0, "USD", TransactionStatus.SUCCESS),
            _make_tx("TX-3", 300.0, "EUR", TransactionStatus.FAILED),
            _make_tx("TX-4", 50.0,  "USD", TransactionStatus.PENDING),
            _make_tx("TX-5", 75.0,  "EUR", TransactionStatus.SUCCESS),
            _make_tx("TX-INV", 0.0, "XYZ", TransactionStatus.UNKNOWN, is_valid=False),
        ]

    def test_total_procesadas(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["total_processed"] == 6

    def test_total_validas(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["total_valid"] == 5

    def test_total_invalidas(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["total_invalid"] == 1

    def test_by_status_success(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["by_status"]["SUCCESS"] == 3

    def test_by_status_failed(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["by_status"]["FAILED"] == 1

    def test_by_status_pending(self):
        metrics = compute_metrics(self._make_dataset())
        assert metrics["by_status"]["PENDING"] == 1

    def test_total_by_currency_usd(self):
        metrics = compute_metrics(self._make_dataset())
        # TX-1 + TX-2 + TX-4 = 100 + 200 + 50 = 350
        assert metrics["total_by_currency"]["USD"] == 350.0

    def test_total_by_currency_eur(self):
        metrics = compute_metrics(self._make_dataset())
        # TX-3 + TX-5 = 300 + 75 = 375
        assert metrics["total_by_currency"]["EUR"] == 375.0

    def test_invalidas_excluidas_de_moneda(self):
        metrics = compute_metrics(self._make_dataset())
        assert "XYZ" not in metrics["total_by_currency"]

    def test_lista_vacia(self):
        metrics = compute_metrics([])
        assert metrics["total_processed"] == 0
        assert metrics["total_valid"] == 0
        assert metrics["total_invalid"] == 0
        assert metrics["by_status"]["SUCCESS"] == 0
        assert metrics["total_by_currency"] == {}


# ---------------------------------------------------------------------------
# Pruebas: format_metrics
# ---------------------------------------------------------------------------

class TestFormatMetrics:

    def test_contiene_totales(self):
        metrics = compute_metrics([
            _make_tx("TX-1", 100.0, "USD", TransactionStatus.SUCCESS)
        ])
        output = format_metrics(metrics)
        assert "Total procesadas" in output
        assert "Total válidas" in output
        assert "Total inválidas" in output

    def test_contiene_estados(self):
        metrics = compute_metrics([
            _make_tx("TX-1", 100.0, "USD", TransactionStatus.SUCCESS)
        ])
        output = format_metrics(metrics)
        assert "SUCCESS" in output
        assert "FAILED" in output
        assert "PENDING" in output

    def test_contiene_moneda(self):
        metrics = compute_metrics([
            _make_tx("TX-1", 100.0, "USD", TransactionStatus.SUCCESS)
        ])
        output = format_metrics(metrics)
        assert "USD" in output
