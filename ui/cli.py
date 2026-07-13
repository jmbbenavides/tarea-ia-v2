"""
ui/cli.py
---------
Interfaz de línea de comandos (CLI) interactiva para el sistema agéntico
de normalización de transacciones.

Menú disponible:
  1. Cargar archivo          → NormalizeSkill + ValidateSkill
  2. Ver todas               → muestra todas las transacciones del contexto
  3. Filtrar por estado      → SearchSkill
  4. Filtrar por moneda      → SearchSkill
  5. Ver métricas            → MetricsSkill
  6. Ver inválidas           → muestra inválidas del contexto
  7. Exportar normalizadas   → ExportSkill
  8. Generar reporte         → ReportSkill
  9. Salir

Cambio arquitectónico (v2):
  La CLI ya NO llama directamente a los servicios.
  Toda la lógica pasa por el TransactionAgent, que selecciona
  y ejecuta la skill adecuada.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

    class _FakeStyle:
        def __getattr__(self, _):
            return ""

    Fore = _FakeStyle()          # type: ignore[assignment]
    Style = _FakeStyle()         # type: ignore[assignment]

from agent.agent import TransactionAgent
from models.transaction import Transaction, TransactionStatus


# ---------------------------------------------------------------------------
# Helpers de presentación
# ---------------------------------------------------------------------------

def _clear() -> None:
    """Limpia la pantalla."""
    os.system("cls" if os.name == "nt" else "clear")


def _header() -> None:
    """Imprime el encabezado de la aplicación."""
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.CYAN + Style.BRIGHT + "   💳  NORMALIZADOR DE TRANSACCIONES MULTIFUENTE  💳")
    print(Fore.CYAN + Style.BRIGHT + "   🤖  Powered by TransactionAgent v2.0")
    print(Fore.CYAN + Style.BRIGHT + "=" * 60 + Style.RESET_ALL)


def _pause() -> None:
    input(Fore.YELLOW + "\n  Presiona ENTER para continuar..." + Style.RESET_ALL)


def _status_color(status: TransactionStatus) -> str:
    """Devuelve el nombre del estado con color según tipo."""
    colors = {
        TransactionStatus.SUCCESS: Fore.GREEN,
        TransactionStatus.FAILED:  Fore.RED,
        TransactionStatus.PENDING: Fore.YELLOW,
        TransactionStatus.UNKNOWN: Fore.MAGENTA,
    }
    color = colors.get(status, "")
    return f"{color}{status.value}{Style.RESET_ALL}"


def _print_transaction(tx: Transaction, index: Optional[int] = None) -> None:
    """Imprime una transacción formateada."""
    prefix = f"  [{index}] " if index is not None else "  "
    valid_marker = (
        f"{Fore.GREEN}✔{Style.RESET_ALL}" if tx.is_valid
        else f"{Fore.RED}✘{Style.RESET_ALL}"
    )
    print(
        f"{prefix}{valid_marker} "
        f"{Fore.WHITE}{Style.BRIGHT}{tx.id:<20}{Style.RESET_ALL} | "
        f"Monto: {Fore.CYAN}{tx.amount:>10,.2f} {tx.currency:<4}{Style.RESET_ALL} | "
        f"Estado: {_status_color(tx.status):<20} | "
        f"Fuente: {Fore.BLUE}{tx.source}{Style.RESET_ALL}"
    )


def _print_transactions(
    transactions: List[Transaction], title: str = "TRANSACCIONES"
) -> None:
    """Imprime una lista de transacciones con encabezado."""
    if not transactions:
        print(Fore.YELLOW + "  (Sin resultados para mostrar)" + Style.RESET_ALL)
        return

    print(Fore.WHITE + Style.BRIGHT + f"\n  {'─'*56}")
    print(f"  {title}  ({len(transactions)} registros)")
    print(f"  {'─'*56}" + Style.RESET_ALL)

    for i, tx in enumerate(transactions, 1):
        _print_transaction(tx, i)

    print(Fore.WHITE + Style.DIM + f"  {'─'*56}" + Style.RESET_ALL)


# ---------------------------------------------------------------------------
# Acciones del menú — ahora delegan al agente
# ---------------------------------------------------------------------------

def _action_load(agent: TransactionAgent) -> None:
    """Opción 1: Cargar archivo → NormalizeSkill + ValidateSkill."""
    print(Fore.WHITE + Style.BRIGHT + "\n  CARGAR ARCHIVO" + Style.RESET_ALL)
    default = Path(__file__).parent.parent / "data" / "sample_transactions.json"
    print(f"  Ruta por defecto: {Fore.CYAN}{default}{Style.RESET_ALL}")
    raw_path = input("  Ingresa la ruta del archivo JSON [ENTER para default]: ").strip()

    filepath = Path(raw_path) if raw_path else default

    # Delegar al agente: normalización
    print(Fore.WHITE + "\n  [1/2] Normalizando..." + Style.RESET_ALL)
    result_norm = agent.run(f"normaliza {filepath}", filepath=filepath)
    print(Fore.GREEN + f"\n  {result_norm}" + Style.RESET_ALL)

    # Delegar al agente: validación
    print(Fore.WHITE + "\n  [2/2] Validando..." + Style.RESET_ALL)
    result_val = agent.run("valida las transacciones")
    print(Fore.GREEN + f"  {result_val}" + Style.RESET_ALL)


def _action_view_all(agent: TransactionAgent) -> None:
    """Opción 2: Ver todas las transacciones del contexto."""
    _print_transactions(agent.context.transactions, "TODAS LAS TRANSACCIONES")


def _action_filter_status(agent: TransactionAgent) -> None:
    """Opción 3: Filtrar por estado → SearchSkill."""
    print(Fore.WHITE + Style.BRIGHT + "\n  FILTRAR POR ESTADO" + Style.RESET_ALL)
    print(
        f"  Opciones: {Fore.GREEN}SUCCESS{Style.RESET_ALL} | "
        f"{Fore.RED}FAILED{Style.RESET_ALL} | "
        f"{Fore.YELLOW}PENDING{Style.RESET_ALL}"
    )
    raw = input("  Ingresa el estado: ").strip().upper()

    result = agent.run(f"buscar estado {raw.lower()}")
    print(Fore.CYAN + f"\n{result}" + Style.RESET_ALL)


def _action_filter_currency(agent: TransactionAgent) -> None:
    """Opción 4: Filtrar por moneda → SearchSkill."""
    print(Fore.WHITE + Style.BRIGHT + "\n  FILTRAR POR MONEDA" + Style.RESET_ALL)
    currency = input("  Ingresa el código de moneda (ej. USD, EUR): ").strip().upper()
    if not currency:
        print(Fore.RED + "  ✘ Moneda vacía." + Style.RESET_ALL)
        return

    result = agent.run(f"buscar {currency}")
    print(Fore.CYAN + f"\n{result}" + Style.RESET_ALL)


def _action_metrics(agent: TransactionAgent) -> None:
    """Opción 5: Ver métricas → MetricsSkill."""
    result = agent.run("métricas del procesamiento")
    print(Fore.CYAN + f"\n{result}" + Style.RESET_ALL)


def _action_view_invalid(agent: TransactionAgent) -> None:
    """Opción 6: Ver transacciones inválidas con sus errores."""
    invalid = agent.context.invalid
    if not invalid:
        print(Fore.YELLOW + "\n  No hay transacciones inválidas." + Style.RESET_ALL)
        return

    print(Fore.WHITE + Style.BRIGHT + f"\n  {'─'*56}")
    print(f"  TRANSACCIONES INVÁLIDAS  ({len(invalid)} registros)")
    print(f"  {'─'*56}" + Style.RESET_ALL)

    for i, tx in enumerate(invalid, 1):
        print(
            f"  [{i}] {Fore.RED}✘{Style.RESET_ALL} "
            f"{Fore.WHITE}{Style.BRIGHT}{tx.id or '(sin ID)':<20}{Style.RESET_ALL}"
        )
        for err in tx.validation_errors:
            print(f"       {Fore.RED}→ {err}{Style.RESET_ALL}")

    print(Fore.WHITE + Style.DIM + f"  {'─'*56}" + Style.RESET_ALL)


def _action_export(agent: TransactionAgent) -> None:
    """Opción 7: Exportar → ExportSkill."""
    result = agent.run("exporta los resultados")
    print(Fore.GREEN + f"\n  {result}" + Style.RESET_ALL)


def _action_report(agent: TransactionAgent) -> None:
    """Opción 8: Generar reporte Markdown → ReportSkill."""
    result = agent.run("genera reporte markdown")
    print(Fore.GREEN + f"\n  {result}" + Style.RESET_ALL)


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

_MENU_OPTIONS = {
    "1": ("Cargar archivo",          _action_load),
    "2": ("Ver todas",               _action_view_all),
    "3": ("Filtrar por estado",      _action_filter_status),
    "4": ("Filtrar por moneda",      _action_filter_currency),
    "5": ("Ver métricas",            _action_metrics),
    "6": ("Ver inválidas",           _action_view_invalid),
    "7": ("Exportar normalizadas",   _action_export),
    "8": ("Generar reporte",         _action_report),
    "9": ("Salir",                   None),
}


def _print_menu(agent: TransactionAgent) -> None:
    """Imprime el menú principal con estado del agente."""
    ctx = agent.context
    loaded_count = len(ctx.transactions)
    loaded_str = (
        f"{Fore.GREEN}{loaded_count} transacciones cargadas{Style.RESET_ALL}"
        if loaded_count > 0
        else f"{Fore.YELLOW}Sin datos cargados{Style.RESET_ALL}"
    )

    print(f"\n  Estado: {loaded_str}")
    print(Fore.WHITE + Style.BRIGHT + "\n  ┌─────────────────────────────────────┐")
    print("  │            MENÚ PRINCIPAL           │")
    print("  └─────────────────────────────────────┘" + Style.RESET_ALL)

    for key, (label, _) in _MENU_OPTIONS.items():
        icon = "🚪" if key == "9" else f" {key}"
        color = Fore.RED if key == "9" else Fore.WHITE
        print(f"  {color}  [{icon}] {label}{Style.RESET_ALL}")

    print()


def run() -> None:
    """
    Inicia el bucle principal de la CLI interactiva.

    En esta versión (v2), la CLI instancia un TransactionAgent
    único que mantiene el estado de sesión (AgentContext) y
    delega cada acción del menú a la skill correspondiente.
    """
    # Un agente por sesión; el contexto persiste entre opciones del menú
    agent = TransactionAgent()

    while True:
        _clear()
        _header()
        _print_menu(agent)

        choice = input(f"  {Fore.CYAN}Elige una opción: {Style.RESET_ALL}").strip()

        if choice not in _MENU_OPTIONS:
            print(Fore.RED + "  ✘ Opción inválida. Ingresa un número del 1 al 9." + Style.RESET_ALL)
            _pause()
            continue

        label, action = _MENU_OPTIONS[choice]

        if action is None:
            print(Fore.CYAN + "\n  ¡Hasta luego! 👋" + Style.RESET_ALL)
            sys.exit(0)

        print(Fore.WHITE + Style.BRIGHT + f"\n  ── {label.upper()} ──" + Style.RESET_ALL)
        action(agent)
        _pause()
