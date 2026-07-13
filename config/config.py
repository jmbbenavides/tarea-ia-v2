"""
config/config.py
----------------
Configuración centralizada del sistema agéntico.

Todos los parámetros del agente se definen aquí para facilitar
el ajuste sin necesidad de modificar la lógica de negocio.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
RULES_PATH = CONFIG_DIR / "rules.json"

# ---------------------------------------------------------------------------
# Configuración del agente
# ---------------------------------------------------------------------------

AGENT_NAME = "TransactionAgent"
AGENT_VERSION = "2.0.0"

# Idioma de las respuestas del agente
LANGUAGE = "es"

# Parámetros de modelo (para futura integración con LLM)
MODEL_NAME = "rule-based"  # "gpt-4", "gemini-pro", etc.
TEMPERATURE = 0.0  # Determinístico en modo rule-based

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Palabras clave del router (mapeo keyword → skill)
# ---------------------------------------------------------------------------

ROUTER_KEYWORDS: dict[str, list[str]] = {
    "NormalizeSkill": [
        "normaliza", "normalizar",
        "cargar", "carga", "importar", "importa", "parsea", "parsear",
    ],
    "ValidateSkill": [
        "valida", "validar", "verificar", "verifica",
        "validación", "errores", "inválidas",
    ],
    "MetricsSkill": [
        "métricas", "metrica", "estadísticas", "estadistica",
        "totales", "conteo", "stats",
    ],
    "SearchSkill": [
        "buscar", "busca", "busco", "encontrar", "encuentra",
        "filtrar", "filtra", "search",
    ],
    "ExportSkill": [
        "exportar", "exporta", "guardar", "guarda",
        "generar archivos", "genera archivos", "export",
    ],
    "ReportSkill": [
        "reporte", "report", "informe", "genera reporte",
        "markdown", "resumen ejecutivo",
    ],
}

# ---------------------------------------------------------------------------
# Carga de reglas de negocio
# ---------------------------------------------------------------------------

def load_rules() -> dict:
    """
    Carga el archivo rules.json de configuración de negocio.

    Returns:
        Diccionario con las reglas de negocio del proyecto.
    """
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Configuración de logging (función de inicialización)
# ---------------------------------------------------------------------------

def setup_logging(level: int = LOG_LEVEL) -> logging.Logger:
    """
    Inicializa y devuelve el logger raíz del sistema agéntico.

    Args:
        level: Nivel de logging (default: INFO).

    Returns:
        Logger configurado.
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    return logging.getLogger(AGENT_NAME)
