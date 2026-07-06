"""
tests/test_validator.py
-----------------------
Pruebas unitarias para el servicio de validación.

Cubre:
  - Validación de ID vacío.
  - Validación de monto inválido (cero, negativo).
  - Validación de moneda vacía y no soportada.
  - Validación de fecha inválida.
  - Validación de estado desconocido.
  - Verificación de split_transactions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from models.transaction import Transaction, TransactionStatus
from services.validator import validate, split_transactions


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _make_tx(**kwargs) -> Transaction:
    """Crea una Transaction válida y sobreescribe con kwargs."""
    defaults = dict(
        id="TXN-TEST",
        amount=100.0,
        currency="USD",
        timestamp="2024-01-01T00:00:00Z",
        status=TransactionStatus.SUCCESS,
        source="TestSource",
        raw={},
    )
    defaults.update(kwargs)
    return Transaction(**defaults)


# ---------------------------------------------------------------------------
# Pruebas de validación individual
# ---------------------------------------------------------------------------

class TestValidate:

    def test_transaccion_valida(self):
        tx = validate(_make_tx())
        assert tx.is_valid is True
        assert tx.validation_errors == []

    def test_id_vacio(self):
        tx = validate(_make_tx(id=""))
        assert tx.is_valid is False
        assert any("ID" in e for e in tx.validation_errors)

    def test_id_espacios(self):
        tx = validate(_make_tx(id="   "))
        assert tx.is_valid is False

    def test_monto_cero(self):
        tx = validate(_make_tx(amount=0.0))
        assert tx.is_valid is False
        assert any("Monto" in e for e in tx.validation_errors)

    def test_monto_negativo(self):
        tx = validate(_make_tx(amount=-50.0))
        assert tx.is_valid is False

    def test_moneda_vacia(self):
        tx = validate(_make_tx(currency=""))
        assert tx.is_valid is False
        assert any("Moneda" in e for e in tx.validation_errors)

    def test_moneda_no_soportada(self):
        tx = validate(_make_tx(currency="XYZ"))
        assert tx.is_valid is False
        assert any("XYZ" in e for e in tx.validation_errors)

    def test_fecha_invalida(self):
        tx = validate(_make_tx(timestamp="no-es-fecha"))
        assert tx.is_valid is False
        assert any("Fecha" in e for e in tx.validation_errors)

    def test_fecha_valida_iso(self):
        tx = validate(_make_tx(timestamp="2024-06-15T10:45:00Z"))
        assert any(e for e in tx.validation_errors if "Fecha" in e) is False

    def test_estado_desconocido(self):
        tx = validate(_make_tx(status=TransactionStatus.UNKNOWN, raw={"status": "procesando"}))
        assert tx.is_valid is False
        assert any("Estado" in e for e in tx.validation_errors)

    def test_multiples_errores(self):
        tx = validate(_make_tx(id="", amount=-5.0, currency=""))
        assert tx.is_valid is False
        assert len(tx.validation_errors) >= 3


# ---------------------------------------------------------------------------
# Pruebas de split_transactions
# ---------------------------------------------------------------------------

class TestSplitTransactions:

    def test_split_basico(self):
        txns = [
            validate(_make_tx(id=f"TX-{i}"))
            for i in range(3)
        ] + [
            validate(_make_tx(id=""))  # inválido
        ]
        valid, invalid = split_transactions(txns)
        assert len(valid) == 3
        assert len(invalid) == 1

    def test_todos_validos(self):
        txns = [validate(_make_tx(id=f"TX-{i}")) for i in range(5)]
        valid, invalid = split_transactions(txns)
        assert len(valid) == 5
        assert len(invalid) == 0

    def test_todos_invalidos(self):
        txns = [validate(_make_tx(id="")) for _ in range(3)]
        valid, invalid = split_transactions(txns)
        assert len(valid) == 0
        assert len(invalid) == 3

    def test_lista_vacia(self):
        valid, invalid = split_transactions([])
        assert valid == []
        assert invalid == []
