"""
ui/cli.py
---------
Interfaz de línea de comandos (CLI) interactiva para explorar y gestionar
el conjunto de transacciones normalizadas.

Menú disponible:
  1. Cargar archivo
  2. Ver todas las transacciones
  3. Filtrar por estado
  4. Filtrar por moneda
  5. Ver métricas
  6. Ver inválidas
  7. Exportar normalizadas
  8. Salir

Decisión de diseño:
  Se usa colorama para dar color al terminal de forma portable
  (Windows/Linux/macOS). Todos los inputs se validan con try/except
  para evitar errores en tiempo de ejecución por entradas inesperadas.
"""

from __future__ import annotations

import json
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

from models.transaction import Transaction, TransactionStatus
from services.metrics import compute_metrics, format_metrics
from services.normalizer import normalize
from services.parser import parse_record
from services.validator import split_transactions, validate


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


def _print_transactions(transactions: List[Transaction], title: str = "TRANSACCIONES") -> None:
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
# Acciones del menú
# ---------------------------------------------------------------------------

def _action_load(state: dict) -> None:
    """Opción 1: Cargar archivo JSON de transacciones."""
    print(Fore.WHITE + Style.BRIGHT + "\n  CARGAR ARCHIVO" + Style.RESET_ALL)
    default = Path(__file__).parent.parent / "data" / "sample_transactions.json"
    print(f"  Ruta por defecto: {Fore.CYAN}{default}{Style.RESET_ALL}")
    raw_path = input(f"  Ingresa la ruta del archivo JSON [ENTER para default]: ").strip()

    filepath = Path(raw_path) if raw_path else default

    if not filepath.exists():
        print(Fore.RED + f"  ✘ Archivo no encontrado: {filepath}" + Style.RESET_ALL)
        return

    try:
        with open(filepath, encoding="utf-8") as f:
            records: list = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(Fore.RED + f"  ✘ Error al leer el archivo: {e}" + Style.RESET_ALL)
        return

    if not isinstance(records, list):
        print(Fore.RED + "  ✘ El archivo debe contener un array JSON en el nivel raíz." + Style.RESET_ALL)
        return

    # Procesar registros
    transactions: List[Transaction] = []
    skipped = 0
    for record in records:
        if not isinstance(record, dict):
            skipped += 1
            continue
        try:
            raw_fields = parse_record(record)
            tx = normalize(raw_fields, record)
            tx = validate(tx)
            transactions.append(tx)
        except Exception as e:
            print(Fore.RED + f"  ⚠ Error procesando registro: {e}" + Style.RESET_ALL)
            skipped += 1

    state["transactions"] = transactions
    valid, invalid = split_transactions(transactions)
    state["valid"] = valid
    state["invalid"] = invalid
    state["metrics"] = compute_metrics(transactions)

    print(Fore.GREEN + f"\n  ✔ Archivo cargado: {filepath.name}" + Style.RESET_ALL)
    print(f"  Total procesadas : {len(transactions)}")
    print(f"  Válidas          : {Fore.GREEN}{len(valid)}{Style.RESET_ALL}")
    print(f"  Inválidas        : {Fore.RED}{len(invalid)}{Style.RESET_ALL}")
    if skipped:
        print(Fore.YELLOW + f"  Omitidas         : {skipped}" + Style.RESET_ALL)


def _action_view_all(state: dict) -> None:
    """Opción 2: Ver todas las transacciones normalizadas."""
    _print_transactions(state.get("transactions", []), "TODAS LAS TRANSACCIONES")


def _action_filter_status(state: dict) -> None:
    """Opción 3: Filtrar por estado."""
    print(Fore.WHITE + Style.BRIGHT + "\n  FILTRAR POR ESTADO" + Style.RESET_ALL)
    print(f"  Opciones: {Fore.GREEN}SUCCESS{Style.RESET_ALL} | {Fore.RED}FAILED{Style.RESET_ALL} | {Fore.YELLOW}PENDING{Style.RESET_ALL}")
    raw = input("  Ingresa el estado: ").strip().upper()

    try:
        status = TransactionStatus(raw)
    except ValueError:
        print(Fore.RED + f"  ✘ Estado inválido: '{raw}'" + Style.RESET_ALL)
        return

    filtered = [
        tx for tx in state.get("transactions", [])
        if tx.status == status and tx.is_valid
    ]
    _print_transactions(filtered, f"TRANSACCIONES — ESTADO: {status.value}")


def _action_filter_currency(state: dict) -> None:
    """Opción 4: Filtrar por moneda."""
    print(Fore.WHITE + Style.BRIGHT + "\n  FILTRAR POR MONEDA" + Style.RESET_ALL)
    currency = input("  Ingresa el código de moneda (ej. USD, EUR): ").strip().upper()
    if not currency:
        print(Fore.RED + "  ✘ Moneda vacía." + Style.RESET_ALL)
        return

    filtered = [
        tx for tx in state.get("transactions", [])
        if tx.currency == currency and tx.is_valid
    ]
    _print_transactions(filtered, f"TRANSACCIONES — MONEDA: {currency}")


def _action_metrics(state: dict) -> None:
    """Opción 5: Ver métricas del procesamiento."""
    metrics = state.get("metrics")
    if not metrics:
        print(Fore.YELLOW + "\n  No hay datos cargados aún." + Style.RESET_ALL)
        return
    print(Fore.CYAN + format_metrics(metrics) + Style.RESET_ALL)


def _action_view_invalid(state: dict) -> None:
    """Opción 6: Ver transacciones inválidas con sus errores."""
    invalid = state.get("invalid", [])
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


def _action_export(state: dict) -> None:
    """Opción 7: Exportar transacciones normalizadas a valid.json e invalid.json."""
    valid = state.get("valid", [])
    invalid = state.get("invalid", [])

    if not state.get("transactions"):
        print(Fore.YELLOW + "\n  No hay datos cargados." + Style.RESET_ALL)
        return

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    valid_path = output_dir / "valid.json"
    invalid_path = output_dir / "invalid.json"

    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump([tx.to_dict() for tx in valid], f, ensure_ascii=False, indent=2)

    with open(invalid_path, "w", encoding="utf-8") as f:
        json.dump([tx.to_dict_full() for tx in invalid], f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"\n  ✔ Exportado válidas   → {valid_path}" + Style.RESET_ALL)
    print(Fore.GREEN + f"  ✔ Exportado inválidas → {invalid_path}" + Style.RESET_ALL)
    print(f"  Total válidas  : {len(valid)}")
    print(f"  Total inválidas: {len(invalid)}")


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
    "8": ("Salir",                   None),
}


def _print_menu(state: dict) -> None:
    """Imprime el menú principal."""
    loaded_count = len(state.get("transactions", []))
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
        icon = "🚪" if key == "8" else f" {key}"
        color = Fore.RED if key == "8" else Fore.WHITE
        print(f"  {color}  [{icon}] {label}{Style.RESET_ALL}")

    print()


def run() -> None:
    """
    Inicia el bucle principal de la CLI interactiva.

    Mantiene el estado de la sesión (transacciones, métricas) en un
    diccionario que se pasa a cada acción.
    """
    state: dict = {
        "transactions": [],
        "valid": [],
        "invalid": [],
        "metrics": None,
    }

    while True:
        _clear()
        _header()
        _print_menu(state)

        choice = input(f"  {Fore.CYAN}Elige una opción: {Style.RESET_ALL}").strip()

        if choice not in _MENU_OPTIONS:
            print(Fore.RED + "  ✘ Opción inválida. Ingresa un número del 1 al 8." + Style.RESET_ALL)
            _pause()
            continue

        label, action = _MENU_OPTIONS[choice]

        if action is None:
            print(Fore.CYAN + "\n  ¡Hasta luego! 👋" + Style.RESET_ALL)
            sys.exit(0)

        print(Fore.WHITE + Style.BRIGHT + f"\n  ── {label.upper()} ──" + Style.RESET_ALL)
        action(state)
        _pause()
