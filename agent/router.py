"""
agent/router.py
---------------
Router basado en palabras clave para seleccionar la skill adecuada.

El SkillRouter inspecciona el texto de la solicitud y devuelve
la clase de skill correspondiente según las reglas definidas
en config/config.py.

Decisión de diseño:
  El router está desacoplado del agente y de las skills, lo que
  permite agregar nuevas skills o modificar keywords sin alterar
  la lógica del agente.
"""

from __future__ import annotations

import logging
from typing import Optional, Type

from config.config import ROUTER_KEYWORDS

logger = logging.getLogger("TransactionAgent.Router")


class SkillRouter:
    """
    Router de skills basado en palabras clave.

    Analiza el texto de una solicitud y determina qué skill
    debe ejecutarse según las keywords definidas en configuración.

    Uso:
        router = SkillRouter()
        router.register_skills(skill_registry)
        skill_class = router.route("normaliza el archivo")
    """

    def __init__(self) -> None:
        # Mapeo nombre_skill → clase de skill
        self._registry: dict[str, type] = {}

    def register_skills(self, registry: dict[str, type]) -> None:
        """
        Registra el diccionario de skills disponibles.

        Args:
            registry: Diccionario {nombre_skill: clase_skill}.
        """
        self._registry = registry
        logger.debug("Skills registradas: %s", list(registry.keys()))

    def route(self, request: str) -> Optional[type]:
        """
        Determina la skill adecuada para una solicitud.

        Itera sobre las palabras clave de cada skill (definidas en
        config.py) y devuelve la primera coincidencia encontrada.
        Las keywords más largas (multi-palabra) se comprueban primero
        para evitar colisiones con substrings de palabras clave cortas.

        Args:
            request: Texto de la solicitud del usuario.

        Returns:
            Clase de la skill seleccionada, o None si no hay coincidencia.
        """
        normalized = request.lower().strip()
        logger.debug("Enrutando solicitud: «%s»", normalized)

        for skill_name, keywords in ROUTER_KEYWORDS.items():
            # Ordenar keywords de mayor a menor longitud para evitar
            # que keywords cortas sean sub-cadenas de las más largas
            sorted_kws = sorted(keywords, key=len, reverse=True)
            for kw in sorted_kws:
                if kw in normalized:
                    skill_class = self._registry.get(skill_name)
                    if skill_class:
                        logger.info(
                            "Keyword «%s» → skill «%s»", kw, skill_name
                        )
                        return skill_class

        logger.warning("No se encontró skill para: «%s»", request)
        return None

    def available_skills(self) -> list[str]:
        """
        Devuelve la lista de nombres de skills registradas.

        Returns:
            Lista de nombres de skills disponibles.
        """
        return list(self._registry.keys())
