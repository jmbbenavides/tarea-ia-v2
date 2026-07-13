"""
main.py
-------
Punto de entrada de la aplicación de normalización de transacciones.

Uso:
    python main.py              → Inicia la CLI interactiva.
    python main.py --proceso    → Pipeline batch completo vía agente
                                  (normaliza → valida → métricas → exporta).
    python main.py --batch      → Alias de --proceso.

Arquitectura (v2 — Sistema Agéntico):
    main.py
        │
        ▼
    TransactionAgent
        │
        ├── SkillRouter  (selección automática de skill)
        │
        ├── NormalizeSkill → services.parser / services.normalizer
        ├── ValidateSkill  → services.validator
        ├── MetricsSkill   → services.metrics
        ├── SearchSkill    → (búsqueda en contexto)
        ├── ExportSkill    → (escritura a data/)
        └── ReportSkill    → (generación de reporte Markdown)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _run_batch() -> None:
    """
    Modo batch: ejecuta el pipeline completo a través del TransactionAgent.

    El agente coordina las siguientes skills en secuencia:
      1. NormalizeSkill  → lee y normaliza sample_transactions.json
      2. ValidateSkill   → separa válidas e inválidas
      3. MetricsSkill    → calcula estadísticas
      4. ExportSkill     → genera valid.json e invalid.json
    """
    from agent.agent import TransactionAgent

    agent = TransactionAgent()
    result = agent.run_pipeline()
    # Imprimir de forma segura en consolas Windows con encoding limitado
    try:
        print(result)
    except UnicodeEncodeError:
        print(result.encode("ascii", errors="replace").decode("ascii"))


def main() -> None:
    """Punto de entrada principal."""
    if "--proceso" in sys.argv or "--batch" in sys.argv:
        _run_batch()
    else:
        from ui.cli import run
        run()


if __name__ == "__main__":
    main()
