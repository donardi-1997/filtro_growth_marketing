"""Command-line entrypoint and GUI dispatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporting import run_analysis
from .gui import launch_gui


def cli_main(args: argparse.Namespace) -> int:
    folder = Path(args.carpeta).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"No existe la carpeta: {folder}", file=sys.stderr)
        return 2

    output_dir = Path(args.salida).expanduser().resolve() if args.salida else folder
    rows, xlsx_path, csv_path = run_analysis(folder, output_dir)

    print("\n=== FILTRO TERMINADO ===")
    print(f"CVs procesadas: {len(rows)}")
    print(f"Excel: {xlsx_path}")
    print(f"CSV:   {csv_path}")
    print("\nTOP 10:")
    for row in rows[:10]:
        print(f"{row['Ajuste %']:>5}% | {row['Nombre'][:35]:35} | {row['Clasificación']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ranking local de CVs para Growth & Marketing Lead")
    parser.add_argument("--carpeta", help="Carpeta con archivos PDF/DOCX. Si se omite, abre la interfaz gráfica.")
    parser.add_argument("--salida", help="Carpeta de salida; por defecto usa la carpeta de CVs.")
    args = parser.parse_args()

    if args.carpeta:
        return cli_main(args)
    launch_gui()
    return 0
