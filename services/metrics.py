"""
services/metrics.py
-------------------
Calcula métricas agregadas sobre el conjunto de transacciones procesadas.

Métricas generadas:
  - Total procesadas.
  - Total válidas.
  - Total inválidas.
  - Conteo por estado (SUCCESS, FAILED, PENDING).
  - Monto total por moneda (solo transacciones válidas).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from models.transaction import Transaction, TransactionStatus


def compute_metrics(transactions: List[Transaction]) -> Dict:
    """
    Calcula y devuelve un diccionario con todas las métricas del conjunto.

    Args:
        transactions: Lista de transacciones (válidas e inválidas).

    Returns:
        Diccionario con las siguientes claves:
          - total_processed  (int)
          - total_valid      (int)
          - total_invalid    (int)
          - by_status        (dict: str → int)
          - total_by_currency (dict: str → float)
    """
    total_processed = len(transactions)
    valid = [tx for tx in transactions if tx.is_valid]
    invalid = [tx for tx in transactions if not tx.is_valid]

    status_counter: Counter = Counter()
    for tx in valid:
        status_counter[tx.status.value] += 1

    # Aseguramos que todos los estados aparezcan aunque sean 0
    by_status: Dict[str, int] = {
        TransactionStatus.SUCCESS.value: status_counter.get(TransactionStatus.SUCCESS.value, 0),
        TransactionStatus.FAILED.value:  status_counter.get(TransactionStatus.FAILED.value, 0),
        TransactionStatus.PENDING.value: status_counter.get(TransactionStatus.PENDING.value, 0),
    }

    currency_totals: Dict[str, float] = defaultdict(float)
    for tx in valid:
        currency_totals[tx.currency] = round(
            currency_totals[tx.currency] + tx.amount, 2
        )

    return {
        "total_processed": total_processed,
        "total_valid": len(valid),
        "total_invalid": len(invalid),
        "by_status": by_status,
        "total_by_currency": dict(currency_totals),
    }


def format_metrics(metrics: Dict) -> str:
    """
    Formatea las métricas como una cadena de texto legible para la CLI.

    Args:
        metrics: Diccionario devuelto por `compute_metrics`.

    Returns:
        Cadena formateada lista para imprimir.
    """
    lines = [
        "=" * 50,
        "           MÉTRICAS DEL PROCESAMIENTO",
        "=" * 50,
        f"  Total procesadas : {metrics['total_processed']:>6}",
        f"  Total válidas    : {metrics['total_valid']:>6}",
        f"  Total inválidas  : {metrics['total_invalid']:>6}",
        "",
        "  Por estado:",
    ]

    for status, count in metrics["by_status"].items():
        lines.append(f"    {status:<10}: {count}")

    lines.append("")
    lines.append("  Totales por moneda (solo válidas):")

    if metrics["total_by_currency"]:
        for currency, total in sorted(metrics["total_by_currency"].items()):
            lines.append(f"    {currency:<6}: {total:>12,.2f}")
    else:
        lines.append("    (sin datos)")

    lines.append("=" * 50)
    return "\n".join(lines)
