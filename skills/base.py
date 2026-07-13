"""
skills/base.py
--------------
Clase base abstracta para todas las skills del sistema agéntico.

Define la interfaz mínima que toda skill debe implementar:
  - __init__(context): recibe el contexto compartido de sesión.
  - execute(request, **kwargs): ejecuta la lógica de la skill.
  - name: propiedad con el nombre de la skill.

Decisión de diseño:
  Al heredar de BaseSkill, cada skill garantiza compatibilidad
  con el agente y el router, facilitando la extensibilidad.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent.context import AgentContext


class BaseSkill(ABC):
    """
    Interfaz base abstracta para todas las skills.

    Toda skill concreta debe heredar de esta clase e implementar
    el método `execute`.

    Attributes:
        context: Contexto compartido de sesión del agente.
    """

    def __init__(self, context: AgentContext) -> None:
        """
        Inicializa la skill con el contexto de sesión.

        Args:
            context: Estado compartido del agente.
        """
        self.context = context

    @property
    def name(self) -> str:
        """Nombre de la skill (por defecto, el nombre de la clase)."""
        return self.__class__.__name__

    @abstractmethod
    def execute(self, request: str, **kwargs: Any) -> str:
        """
        Ejecuta la lógica principal de la skill.

        Args:
            request: Texto de la solicitud original.
            **kwargs: Parámetros adicionales según la skill.

        Returns:
            Cadena de texto con el resultado de la ejecución.
        """
        ...
