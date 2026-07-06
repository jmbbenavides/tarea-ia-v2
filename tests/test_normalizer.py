"""
tests/test_normalizer.py
------------------------
Pruebas unitarias para el servicio de normalización.

Cubre:
  - Conversión de montos: texto, centavos, formato europeo.
  - Normalización de moneda.
  - Normalización de estado.
  - Normalización de fecha con múltiples formatos.
"""

import sys
from pathlib import Path

# Asegurar que el proyecto raíz esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from services.normalizer import (
    _parse_amount,
    _normalize_currency,
    _normalize_status,
    _normalize_timestamp,
    normalize,
)
from services.parser import parse_record
from models.transaction import TransactionStatus


# ---------------------------------------------------------------------------
# Pruebas: _parse_amount
# ---------------------------------------------------------------------------

class TestParseAmount:

    def test_float_directo(self):
        assert _parse_amount(99.99) == 99.99

    def test_entero_normal(self):
        assert _parse_amount(500) == 500.0

    def test_entero_en_centavos(self):
        """Entero > threshold (10000) → divide entre 100."""
        result = _parse_amount(150000)
        assert result == 1500.0

    def test_texto_con_simbolo_dolar(self):
        assert _parse_amount("$1,234.56") == 1234.56

    def test_formato_europeo(self):
        assert _parse_amount("2.500,75") == 2500.75

    def test_texto_numero_simple(self):
        assert _parse_amount("350.00") == 350.0

    def test_texto_invalido(self):
        assert _parse_amount("N/A") is None

    def test_none(self):
        assert _parse_amount(None) is None

    def test_cero(self):
        assert _parse_amount(0) == 0.0

    def test_negativo(self):
        assert _parse_amount(-100) == -100.0


# ---------------------------------------------------------------------------
# Pruebas: _normalize_currency
# ---------------------------------------------------------------------------

class TestNormalizeCurrency:

    def test_mayusculas(self):
        assert _normalize_currency("usd") == "USD"

    def test_ya_mayuscula(self):
        assert _normalize_currency("EUR") == "EUR"

    def test_con_espacios(self):
        assert _normalize_currency("  gbp  ") == "GBP"

    def test_vacia(self):
        assert _normalize_currency("") == ""

    def test_none(self):
        assert _normalize_currency(None) == ""


# ---------------------------------------------------------------------------
# Pruebas: _normalize_status
# ---------------------------------------------------------------------------

class TestNormalizeStatus:

    @pytest.mark.parametrize("raw,expected", [
        ("completed",  TransactionStatus.SUCCESS),
        ("OK",         TransactionStatus.SUCCESS),
        ("success",    TransactionStatus.SUCCESS),
        ("failed",     TransactionStatus.FAILED),
        ("error",      TransactionStatus.FAILED),
        ("pending",    TransactionStatus.PENDING),
        ("procesando", TransactionStatus.UNKNOWN),
        ("",           TransactionStatus.UNKNOWN),
    ])
    def test_estados(self, raw, expected):
        assert _normalize_status(raw) == expected


# ---------------------------------------------------------------------------
# Pruebas: _normalize_timestamp
# ---------------------------------------------------------------------------

class TestNormalizeTimestamp:

    def test_iso8601_con_z(self):
        result = _normalize_timestamp("2024-01-15T10:30:00Z")
        assert result == "2024-01-15T10:30:00Z"

    def test_formato_a(self):
        result = _normalize_timestamp("2024-01-16 08:45:00")
        assert result == "2024-01-16T08:45:00Z"

    def test_formato_b(self):
        result = _normalize_timestamp("15/01/2024 14:00")
        assert result == "2024-01-15T14:00:00Z"

    def test_fecha_invalida(self):
        result = _normalize_timestamp("99/99/9999 25:99")
        # No puede parsear → devuelve original
        assert result == "99/99/9999 25:99"

    def test_vacia(self):
        assert _normalize_timestamp("") == ""


# ---------------------------------------------------------------------------
# Pruebas: normalize (integración parcial)
# ---------------------------------------------------------------------------

class TestNormalize:

    def _make_raw_fields(self, **kwargs):
        defaults = {
            "raw_id": "TXN-001",
            "raw_amount": 1500.00,
            "raw_currency": "USD",
            "raw_timestamp": "2024-01-15T10:30:00Z",
            "raw_status": "completed",
            "source": "FormatA",
        }
        defaults.update(kwargs)
        return defaults

    def test_transaccion_valida(self):
        raw = self._make_raw_fields()
        tx = normalize(raw, {})
        assert tx.id == "TXN-001"
        assert tx.amount == 1500.0
        assert tx.currency == "USD"
        assert tx.status == TransactionStatus.SUCCESS

    def test_moneda_normalizada(self):
        raw = self._make_raw_fields(raw_currency="eur")
        tx = normalize(raw, {})
        assert tx.currency == "EUR"

    def test_monto_centavos(self):
        raw = self._make_raw_fields(raw_amount=350000)
        tx = normalize(raw, {})
        assert tx.amount == 3500.0

    def test_monto_texto_europeo(self):
        raw = self._make_raw_fields(raw_amount="1.800,00")
        tx = normalize(raw, {})
        assert tx.amount == 1800.0
