"""
main.py
-------
Punto de entrada de la aplicación de normalización de transacciones.

Uso:
    python main.py              → Inicia la CLI interactiva.
    python main.py --proceso    → Procesa el archivo de muestra y exporta
                                  sin abrir la CLI (modo batch).
"""

from __future__ import annotations

import sys
import json
from pathlib import Path


def _run_batch() -> None:
    """
    Modo batch: procesa el archivo de muestra, exporta valid.json e
    invalid.json e imprime las métricas en consola.
    """
    from services.parser import parse_record
    from services.normalizer import normalize
    from services.validator import validate, split_transactions
    from services.metrics import compute_metrics, format_metrics

    sample = Path(__file__).parent / "data" / "sample_transactions.json"
    if not sample.exists():
        print(f"[ERROR] No se encontró el archivo de muestra: {sample}")
        sys.exit(1)

    with open(sample, encoding="utf-8") as f:
        records = json.load(f)

    transactions = []
    for record in records:
        if not isinstance(record, dict):
            continue
        raw = parse_record(record)
        tx = normalize(raw, record)
        tx = validate(tx)
        transactions.append(tx)

    valid, invalid = split_transactions(transactions)
    metrics = compute_metrics(transactions)

    out_dir = Path(__file__).parent / "data"
    with open(out_dir / "valid.json", "w", encoding="utf-8") as f:
        json.dump([tx.to_dict() for tx in valid], f, ensure_ascii=False, indent=2)
    with open(out_dir / "invalid.json", "w", encoding="utf-8") as f:
        json.dump([tx.to_dict_full() for tx in invalid], f, ensure_ascii=False, indent=2)

    print(format_metrics(metrics))
    print(f"\nArchivos generados en: {out_dir}")


def main() -> None:
    """Punto de entrada principal."""
    if "--proceso" in sys.argv or "--batch" in sys.argv:
        _run_batch()
    else:
        from ui.cli import run
        run()


if __name__ == "__main__":
    main()
