"""
agent/context.py
----------------
Define el contexto compartido de sesión del agente.

El AgentContext actúa como "memoria de trabajo" del agente:
almacena transacciones, métricas y estado de la sesión entre
distintas ejecuciones de skills.

Decisión de diseño:
  Se usa dataclass con mutabilidad explícita en lugar de un
  diccionario plano, para garantizar tipado y autodocumentación.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from models.transaction import Transaction


@dataclass
class AgentContext:
    """
    Estado compartido de la sesión del agente.

    Attributes:
        transactions:   Lista completa de transacciones procesadas.
        valid:          Subconjunto de transacciones válidas.
        invalid:        Subconjunto de transacciones inválidas.
        metrics:        Diccionario de métricas calculadas (o None).
        last_file:      Ruta del último archivo cargado.
        session_log:    Historial de acciones ejecutadas en la sesión.
    """

    transactions: List[Transaction] = field(default_factory=list)
    valid: List[Transaction] = field(default_factory=list)
    invalid: List[Transaction] = field(default_factory=list)
    metrics: Optional[Dict] = None
    last_file: Optional[Path] = None
    session_log: List[str] = field(default_factory=list)

    def is_loaded(self) -> bool:
        """Indica si hay transacciones cargadas en el contexto."""
        return len(self.transactions) > 0

    def reset(self) -> None:
        """Limpia el contexto de sesión manteniendo el log."""
        self.transactions.clear()
        self.valid.clear()
        self.invalid.clear()
        self.metrics = None
        self.last_file = None

    def log(self, message: str) -> None:
        """
        Registra un mensaje en el historial de la sesión.

        Args:
            message: Texto a registrar.
        """
        self.session_log.append(message)
