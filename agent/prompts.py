"""
agent/prompts.py
----------------
Plantillas de mensajes estructurados para el agente.

Proporciona funciones que generan mensajes estandarizados para:
  - Confirmación de skill seleccionada.
  - Respuesta de éxito.
  - Descripción de errores.
  - Skill no reconocida.

Decisión de diseño:
  Centralizar los mensajes aquí facilita la internacionalización
  y el ajuste del tono del agente sin tocar la lógica.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Plantillas de respuesta del agente
# ---------------------------------------------------------------------------

def prompt_skill_selected(skill_name: str, request: str) -> str:
    """
    Genera el mensaje de confirmación cuando el router selecciona una skill.

    Args:
        skill_name: Nombre de la skill seleccionada.
        request:    Solicitud original del usuario.

    Returns:
        Mensaje formateado de confirmación.
    """
    return (
        f"[Agente] Solicitud recibida: «{request}»\n"
        f"[Agente] Skill seleccionada: {skill_name}"
    )


def prompt_success(skill_name: str, summary: str) -> str:
    """
    Genera el mensaje de éxito tras ejecutar una skill.

    Args:
        skill_name: Nombre de la skill ejecutada.
        summary:    Resumen del resultado.

    Returns:
        Mensaje formateado de éxito.
    """
    return f"[{skill_name}] ✔ {summary}"


def prompt_error(skill_name: str, reason: str) -> str:
    """
    Genera el mensaje de error cuando una skill falla.

    Args:
        skill_name: Nombre de la skill que falló.
        reason:     Descripción del error.

    Returns:
        Mensaje formateado de error.
    """
    return f"[{skill_name}] ✘ Error: {reason}"


def prompt_no_skill(request: str, available: list[str]) -> str:
    """
    Genera el mensaje cuando no se puede determinar la skill.

    Args:
        request:   Solicitud original del usuario.
        available: Lista de nombres de skills disponibles.

    Returns:
        Mensaje indicando que la solicitud no fue reconocida.
    """
    skills_list = ", ".join(available)
    return (
        f"[Agente] No se pudo determinar la skill para: «{request}»\n"
        f"[Agente] Skills disponibles: {skills_list}\n"
        f"[Agente] Intenta con palabras como: normaliza, valida, métricas, "
        f"busca, exporta, reporte."
    )


def prompt_no_data() -> str:
    """
    Mensaje cuando se intenta operar sin datos cargados.

    Returns:
        Mensaje de advertencia.
    """
    return (
        "[Agente] No hay transacciones cargadas en el contexto.\n"
        "[Agente] Usa la skill de normalización primero: «normaliza [archivo]»"
    )
