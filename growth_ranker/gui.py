"""Tkinter desktop interface."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from .exporting import run_analysis
from .profile import APP_TITLE


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1080x680")
    root.minsize(920, 560)

    selected_folder = tk.StringVar()
    status = tk.StringVar(value="Selecciona una carpeta con hojas de vida PDF o DOCX.")
    progress_value = tk.DoubleVar(value=0)
    last_excel: dict[str, Path | None] = {"path": None}

    outer = ttk.Frame(root, padding=18)
    outer.pack(fill="both", expand=True)
    ttk.Label(outer, text="Ranking de candidatos - Marketing", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(outer, text="Growth & Marketing Lead · análisis local · PDF y DOCX", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 16))

    picker = ttk.Frame(outer)
    picker.pack(fill="x")
    entry = ttk.Entry(picker, textvariable=selected_folder)
    entry.pack(side="left", fill="x", expand=True)

    def choose_folder() -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta de hojas de vida")
        if folder:
            selected_folder.set(folder)

    ttk.Button(picker, text="Seleccionar carpeta", command=choose_folder).pack(side="left", padx=(8, 0))

    button_row = ttk.Frame(outer)
    button_row.pack(fill="x", pady=(12, 8))
    analyze_btn = ttk.Button(button_row, text="Analizar candidatos")
    analyze_btn.pack(side="left")
    open_excel_btn = ttk.Button(button_row, text="Abrir Excel", state="disabled")
    open_excel_btn.pack(side="left", padx=(8, 0))
    open_folder_btn = ttk.Button(button_row, text="Abrir carpeta", state="disabled")
    open_folder_btn.pack(side="left", padx=(8, 0))

    progress_bar = ttk.Progressbar(outer, maximum=100, variable=progress_value)
    progress_bar.pack(fill="x", pady=(4, 4))
    ttk.Label(outer, textvariable=status).pack(anchor="w", pady=(0, 10))

    columns = ("rank", "name", "score", "years", "group", "file")
    tree = ttk.Treeview(outer, columns=columns, show="headings", height=18)
    headings = {
        "rank": "#",
        "name": "Candidato",
        "score": "Ajuste %",
        "years": "Años exp.",
        "group": "Clasificación",
        "file": "Archivo",
    }
    widths = {"rank": 45, "name": 220, "score": 85, "years": 85, "group": 250, "file": 260}
    for column in columns:
        tree.heading(column, text=headings[column])
        tree.column(column, width=widths[column], anchor="center" if column in {"rank", "score", "years"} else "w")
    tree.pack(fill="both", expand=True)

    def refresh_table(rows: list[dict]) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for rank, row in enumerate(rows, 1):
            tree.insert(
                "",
                "end",
                values=(
                    rank,
                    row["Nombre"],
                    row["Ajuste %"],
                    row["Años experiencia estimados"],
                    row["Clasificación"],
                    row["Archivo"],
                ),
            )

    def start_analysis() -> None:
        folder_text = selected_folder.get().strip()
        folder = Path(folder_text) if folder_text else None
        if not folder or not folder.exists() or not folder.is_dir():
            messagebox.showwarning(APP_TITLE, "Selecciona una carpeta válida.")
            return

        candidates = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in {".pdf", ".docx"}]
        if not candidates:
            messagebox.showwarning(APP_TITLE, "La carpeta no contiene archivos PDF o DOCX.")
            return

        analyze_btn.configure(state="disabled")
        open_excel_btn.configure(state="disabled")
        open_folder_btn.configure(state="disabled")
        progress_value.set(0)
        status.set(f"Preparando {len(candidates)} hojas de vida...")

        def update_progress(done: int, total: int, name: str) -> None:
            percentage = (done / total * 100) if total else 0
            root.after(0, lambda: progress_value.set(percentage))
            root.after(0, lambda: status.set(f"Procesando {done}/{total}: {name}"))

        def worker() -> None:
            try:
                rows, xlsx_path, _csv_path = run_analysis(folder, progress=update_progress)
                last_excel["path"] = xlsx_path
                root.after(0, lambda: refresh_table(rows))
                root.after(0, lambda: status.set(f"Listo: {len(rows)} hojas de vida procesadas. Excel guardado en la carpeta seleccionada."))
                root.after(0, lambda: progress_value.set(100))
                root.after(0, lambda: open_excel_btn.configure(state="normal"))
                root.after(0, lambda: open_folder_btn.configure(state="normal"))
            except Exception as exc:
                root.after(0, lambda: messagebox.showerror(APP_TITLE, f"No se pudo completar el análisis:\n{exc}"))
                root.after(0, lambda: status.set("El análisis terminó con error."))
            finally:
                root.after(0, lambda: analyze_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    analyze_btn.configure(command=start_analysis)
    open_excel_btn.configure(command=lambda: open_path(last_excel["path"]) if last_excel["path"] else None)
    open_folder_btn.configure(command=lambda: open_path(Path(selected_folder.get())) if selected_folder.get() else None)
    root.mainloop()
