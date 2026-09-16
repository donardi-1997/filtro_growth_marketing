"""Tkinter desktop dashboard for reviewing candidate ranking results."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from .dashboard import dashboard_summary, filter_rows, score_histogram, top_candidates
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

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    BG = "#F4F7FB"
    SURFACE = "#FFFFFF"
    TEXT = "#172033"
    MUTED = "#667085"
    BORDER = "#DDE3EC"
    ACCENT = "#145E77"
    ACCENT_DARK = "#0D465A"
    G1 = "#D9EAD3"
    G2 = "#FFF2CC"
    G3 = "#FCE5CD"
    LOW = "#F4CCCC"
    REVIEW = "#E8EAF0"

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1440x900")
    root.minsize(1120, 720)
    root.configure(bg=BG)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("App.TFrame", background=BG)
    style.configure("Surface.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 22, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 9))
    style.configure("CardValue.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 20, "bold"))
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 9), foreground="white", background=ACCENT)
    style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#9DB7C1")])
    style.configure("Secondary.TButton", font=("Segoe UI", 9), padding=(10, 7))
    style.configure("Treeview", rowheight=30, font=("Segoe UI", 9), background=SURFACE, fieldbackground=SURFACE, borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), foreground=TEXT, background="#EAF0F5", relief="flat")
    style.map("Treeview.Heading", background=[("active", "#DCE6EE")])
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(12, 7), font=("Segoe UI", 9, "bold"))

    selected_folder = tk.StringVar()
    status = tk.StringVar(value="Selecciona una carpeta con hojas de vida PDF o DOCX.")
    progress_value = tk.DoubleVar(value=0)
    search_var = tk.StringVar()
    group_var = tk.StringVar(value="Todos")
    last_excel: dict[str, Path | None] = {"path": None}
    state: dict[str, object] = {"rows": [], "selected": None}

    outer = ttk.Frame(root, style="App.TFrame", padding=18)
    outer.pack(fill="both", expand=True)

    header = ttk.Frame(outer, style="App.TFrame")
    header.pack(fill="x")
    ttk.Label(header, text="Ranking de candidatos", style="Title.TLabel").pack(anchor="w")
    ttk.Label(header, text="Growth & Marketing Lead · análisis local · dashboard de revisión", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 12))

    controls = tk.Frame(outer, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=10)
    controls.pack(fill="x", pady=(0, 12))
    controls.grid_columnconfigure(0, weight=1)

    folder_entry = ttk.Entry(controls, textvariable=selected_folder, font=("Segoe UI", 10))
    folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def choose_folder() -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta de hojas de vida")
        if folder:
            selected_folder.set(folder)

    ttk.Button(controls, text="Seleccionar carpeta", command=choose_folder, style="Secondary.TButton").grid(row=0, column=1, padx=(0, 8))
    analyze_btn = ttk.Button(controls, text="Analizar candidatos", style="Accent.TButton")
    analyze_btn.grid(row=0, column=2, padx=(0, 8))
    open_excel_btn = ttk.Button(controls, text="Abrir Excel", state="disabled", style="Secondary.TButton")
    open_excel_btn.grid(row=0, column=3, padx=(0, 8))
    open_folder_btn = ttk.Button(controls, text="Abrir carpeta", state="disabled", style="Secondary.TButton")
    open_folder_btn.grid(row=0, column=4)

    progress_bar = ttk.Progressbar(controls, maximum=100, variable=progress_value)
    progress_bar.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 4))
    ttk.Label(controls, textvariable=status, background=SURFACE, foreground=MUTED, font=("Segoe UI", 9)).grid(row=2, column=0, columnspan=5, sticky="w")

    kpi_frame = ttk.Frame(outer, style="App.TFrame")
    kpi_frame.pack(fill="x", pady=(0, 12))
    for idx in range(5):
        kpi_frame.grid_columnconfigure(idx, weight=1, uniform="kpi")

    kpi_vars = {
        "total": tk.StringVar(value="0"),
        "average": tk.StringVar(value="0.0%"),
        "group1": tk.StringVar(value="0"),
        "group2": tk.StringVar(value="0"),
        "review": tk.StringVar(value="0"),
    }
    for index, (title, key) in enumerate([
        ("Candidatos", "total"),
        ("Promedio", "average"),
        ("Grupo 1", "group1"),
        ("Grupo 2", "group2"),
        ("Revisión", "review"),
    ]):
        card = tk.Frame(kpi_frame, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=10)
        card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 5, 0 if index == 4 else 5))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=kpi_vars[key], style="CardValue.TLabel").pack(anchor="w", pady=(2, 0))

    body = ttk.Panedwindow(outer, orient="horizontal")
    body.pack(fill="both", expand=True)

    left = ttk.Frame(body, style="App.TFrame")
    right = tk.Frame(body, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=12)
    body.add(left, weight=4)
    body.add(right, weight=1)

    notebook = ttk.Notebook(left)
    notebook.pack(fill="x", pady=(0, 10))
    summary_tab = ttk.Frame(notebook, style="Surface.TFrame")
    top_tab = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(summary_tab, text="Resumen visual")
    notebook.add(top_tab, text="Top 10")

    summary_figure = Figure(figsize=(10, 2.9), dpi=100, facecolor=SURFACE)
    group_ax = summary_figure.add_subplot(121)
    histogram_ax = summary_figure.add_subplot(122)
    summary_canvas = FigureCanvasTkAgg(summary_figure, master=summary_tab)
    summary_canvas.get_tk_widget().pack(fill="both", expand=True)

    top_figure = Figure(figsize=(10, 2.9), dpi=100, facecolor=SURFACE)
    top_ax = top_figure.add_subplot(111)
    top_canvas = FigureCanvasTkAgg(top_figure, master=top_tab)
    top_canvas.get_tk_widget().pack(fill="both", expand=True)

    filter_bar = tk.Frame(left, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1, padx=10, pady=8)
    filter_bar.pack(fill="x", pady=(0, 8))
    filter_bar.grid_columnconfigure(1, weight=1)
    ttk.Label(filter_bar, text="Buscar", background=SURFACE, foreground=MUTED).grid(row=0, column=0, padx=(0, 6))
    ttk.Entry(filter_bar, textvariable=search_var).grid(row=0, column=1, sticky="ew", padx=(0, 10))
    ttk.Label(filter_bar, text="Clasificación", background=SURFACE, foreground=MUTED).grid(row=0, column=2, padx=(0, 6))
    group_combo = ttk.Combobox(
        filter_bar,
        textvariable=group_var,
        state="readonly",
        width=20,
        values=("Todos", "GRUPO 1", "GRUPO 2", "GRUPO 3", "NO PRIORIZAR", "REVISIÓN MANUAL", "ERROR"),
    )
    group_combo.grid(row=0, column=3)

    table_frame = tk.Frame(left, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
    table_frame.pack(fill="both", expand=True)
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    columns = ("rank", "name", "score", "years", "group", "file")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    headings = {"rank": "#", "name": "Candidato", "score": "Ajuste %", "years": "Años exp.", "group": "Clasificación", "file": "Archivo"}
    widths = {"rank": 44, "name": 190, "score": 80, "years": 80, "group": 225, "file": 210}
    for column in columns:
        tree.heading(column, text=headings[column])
        tree.column(column, width=widths[column], minwidth=40, anchor="center" if column in {"rank", "score", "years"} else "w")
    tree.tag_configure("g1", background=G1)
    tree.tag_configure("g2", background=G2)
    tree.tag_configure("g3", background=G3)
    tree.tag_configure("low", background=LOW)
    tree.tag_configure("review", background=REVIEW)
    tree.grid(row=0, column=0, sticky="nsew")
    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    yscroll.grid(row=0, column=1, sticky="ns")
    xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    xscroll.grid(row=1, column=0, sticky="ew")
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    ttk.Label(right, text="Detalle del candidato", background=SURFACE, foreground=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
    detail_name = tk.StringVar(value="Selecciona un candidato")
    detail_meta = tk.StringVar(value="")
    ttk.Label(right, textvariable=detail_name, background=SURFACE, foreground=TEXT, font=("Segoe UI", 12, "bold"), wraplength=280).pack(anchor="w", pady=(10, 2))
    ttk.Label(right, textvariable=detail_meta, background=SURFACE, foreground=MUTED, font=("Segoe UI", 9), wraplength=280).pack(anchor="w", pady=(0, 10))

    open_cv_btn = ttk.Button(right, text="Abrir CV", state="disabled", style="Secondary.TButton")
    open_cv_btn.pack(anchor="w", pady=(0, 12))

    def add_detail_box(title: str) -> tk.Text:
        ttk.Label(right, text=title, background=SURFACE, foreground=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 4))
        box = tk.Text(right, height=6, wrap="word", relief="solid", bd=1, bg="#FAFBFC", fg=TEXT, font=("Segoe UI", 9), padx=8, pady=7)
        box.pack(fill="both", expand=True)
        box.configure(state="disabled")
        return box

    strengths_box = add_detail_box("Fortalezas")
    gaps_box = add_detail_box("Brechas")
    breakdown_box = add_detail_box("Desglose")

    def set_text(box: tk.Text, value: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", value or "Sin información")
        box.configure(state="disabled")

    def row_tag(row: dict) -> str:
        classification = str(row.get("Clasificación", ""))
        if classification.startswith("GRUPO 1"):
            return "g1"
        if classification.startswith("GRUPO 2"):
            return "g2"
        if classification.startswith("GRUPO 3"):
            return "g3"
        if classification.startswith("NO PRIORIZAR"):
            return "low"
        return "review"

    def refresh_kpis(rows: list[dict]) -> None:
        summary = dashboard_summary(rows)
        kpi_vars["total"].set(str(summary["total"]))
        kpi_vars["average"].set(f'{summary["average_score"]:.1f}%')
        kpi_vars["group1"].set(str(summary["group_1"]))
        kpi_vars["group2"].set(str(summary["group_2"]))
        kpi_vars["review"].set(str(summary["review"]))

    def style_axis(axis, title: str) -> None:
        axis.set_facecolor(SURFACE)
        axis.set_title(title, loc="left", fontsize=10, fontweight="bold", color=TEXT, pad=10)
        axis.tick_params(colors=MUTED, labelsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.grid(axis="x", alpha=0.16)
        axis.set_axisbelow(True)

    def refresh_charts(rows: list[dict]) -> None:
        summary = dashboard_summary(rows)
        group_ax.clear()
        histogram_ax.clear()
        top_ax.clear()
        style_axis(group_ax, "Distribución por clasificación")
        style_axis(histogram_ax, "Distribución de puntajes")
        style_axis(top_ax, "Top 10 por ajuste")

        labels = ["Grupo 1", "Grupo 2", "Grupo 3", "No priorizar", "Revisión"]
        values = [summary["group_1"], summary["group_2"], summary["group_3"], summary["not_prioritized"], summary["review"]]
        group_ax.barh(labels[::-1], values[::-1], color=["#98A2B3", "#D07A5F", "#E9C46A", "#5B9BD5", "#4C956C"])
        for index, value in enumerate(values[::-1]):
            group_ax.text(value + 0.15, index, str(value), va="center", fontsize=8, color=TEXT)

        histogram = score_histogram(rows)
        histogram_ax.bar([label for label, _ in histogram], [count for _, count in histogram], color=ACCENT)
        histogram_ax.set_ylim(bottom=0)

        top = top_candidates(rows, limit=10)
        if top:
            names = [str(row.get("Nombre", ""))[:28] for row in top][::-1]
            scores = [float(row.get("Ajuste %", 0) or 0) for row in top][::-1]
            top_ax.barh(names, scores, color=ACCENT)
            top_ax.set_xlim(0, 100)
            for index, score in enumerate(scores):
                top_ax.text(min(score + 1, 96), index, f"{score:.0f}%", va="center", fontsize=8, color=TEXT)
        else:
            top_ax.text(0.5, 0.5, "Sin resultados para mostrar", ha="center", va="center", transform=top_ax.transAxes, color=MUTED)
            top_ax.set_xticks([])
            top_ax.set_yticks([])

        summary_figure.tight_layout(pad=2.0)
        top_figure.tight_layout(pad=2.0)
        summary_canvas.draw_idle()
        top_canvas.draw_idle()

    def visible_rows() -> list[dict]:
        return filter_rows(state["rows"], query=search_var.get(), group=group_var.get())  # type: ignore[arg-type]

    def refresh_table(*_args) -> None:
        rows = visible_rows()
        for item in tree.get_children():
            tree.delete(item)
        for rank, row in enumerate(rows, 1):
            tree.insert("", "end", iid=f"row-{rank}", tags=(row_tag(row),), values=(
                rank,
                row.get("Nombre", ""),
                row.get("Ajuste %", 0),
                row.get("Años experiencia estimados", 0),
                row.get("Clasificación", ""),
                row.get("Archivo", ""),
            ))
        refresh_charts(rows)

    def show_selected(_event=None) -> None:
        selection = tree.selection()
        if not selection:
            return
        values = tree.item(selection[0], "values")
        if not values:
            return
        filename = str(values[5])
        row = next((item for item in state["rows"] if str(item.get("Archivo", "")) == filename), None)  # type: ignore[union-attr]
        if not row:
            return
        state["selected"] = row
        detail_name.set(str(row.get("Nombre", "Candidato")))
        detail_meta.set(f'{row.get("Ajuste %", 0)}% ajuste · {row.get("Años experiencia estimados", 0)} años · {row.get("Clasificación", "")}')
        set_text(strengths_box, str(row.get("Experiencia / fortalezas", "")))
        set_text(gaps_box, str(row.get("Brechas", "")))
        set_text(breakdown_box, str(row.get("Desglose", "")))
        open_cv_btn.configure(state="normal")

    def open_selected_cv() -> None:
        row = state.get("selected")
        folder_text = selected_folder.get().strip()
        if isinstance(row, dict) and folder_text:
            candidate_path = Path(folder_text) / str(row.get("Archivo", ""))
            if candidate_path.exists():
                open_path(candidate_path)
            else:
                messagebox.showwarning(APP_TITLE, "No se encontró el archivo original del candidato.")

    tree.bind("<<TreeviewSelect>>", show_selected)
    open_cv_btn.configure(command=open_selected_cv)
    search_var.trace_add("write", refresh_table)
    group_var.trace_add("write", refresh_table)

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
            root.after(0, lambda value=percentage: progress_value.set(value))
            root.after(0, lambda text=f"Procesando {done}/{total}: {name}": status.set(text))

        def finish_success(rows: list[dict], xlsx_path: Path) -> None:
            state["rows"] = rows
            state["selected"] = None
            last_excel["path"] = xlsx_path
            refresh_kpis(rows)
            refresh_table()
            detail_name.set("Selecciona un candidato")
            detail_meta.set("")
            set_text(strengths_box, "")
            set_text(gaps_box, "")
            set_text(breakdown_box, "")
            open_cv_btn.configure(state="disabled")
            status.set(f"Listo: {len(rows)} hojas de vida procesadas. Usa los filtros o selecciona un candidato para revisar el detalle.")
            progress_value.set(100)
            open_excel_btn.configure(state="normal")
            open_folder_btn.configure(state="normal")

        def worker() -> None:
            try:
                rows, xlsx_path, _csv_path = run_analysis(folder, progress=update_progress)
                root.after(0, lambda rows=rows, path=xlsx_path: finish_success(rows, path))
            except Exception as exc:
                error_message = str(exc)
                root.after(0, lambda message=error_message: messagebox.showerror(APP_TITLE, f"No se pudo completar el análisis:\n{message}"))
                root.after(0, lambda: status.set("El análisis terminó con error."))
            finally:
                root.after(0, lambda: analyze_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    analyze_btn.configure(command=start_analysis)
    open_excel_btn.configure(command=lambda: open_path(last_excel["path"]) if last_excel["path"] else None)
    open_folder_btn.configure(command=lambda: open_path(Path(selected_folder.get())) if selected_folder.get() else None)

    refresh_charts([])
    root.mainloop()
