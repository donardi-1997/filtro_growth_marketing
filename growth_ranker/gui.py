"""ASIATI-branded Tkinter dashboard for reviewing candidate ranking results."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from .brand import BRAND, PALETTE, UI_TABS, WINDOW_TITLE
from .dashboard import dashboard_summary, filter_rows, score_histogram, top_candidates
from .exporting import run_analysis


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def mousewheel_scroll_units(delta: int) -> int:
    """Normalize mouse-wheel delta into Tk canvas scroll units."""
    if delta == 0:
        return 0
    units = int(delta / 120)
    if units == 0:
        units = 1 if delta > 0 else -1
    return -units


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    navy = PALETTE["navy"]
    teal = PALETTE["teal"]
    teal_dark = PALETTE["teal_dark"]
    bg = PALETTE["background"]
    surface = PALETTE["surface"]
    text = PALETTE["text"]
    muted = PALETTE["muted"]
    border = PALETTE["border"]
    navy_soft = PALETTE["navy_soft"]
    teal_soft = PALETTE["teal_soft"]

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("1460x920")
    root.minsize(1100, 700)
    root.configure(bg=bg)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("App.TFrame", background=bg)
    style.configure("Surface.TFrame", background=surface)
    style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
    style.configure("Section.TLabel", background=bg, foreground=text, font=("Segoe UI", 18, "bold"))
    style.configure("Subtitle.TLabel", background=bg, foreground=muted, font=("Segoe UI", 9))
    style.configure("CardTitle.TLabel", background=surface, foreground=muted, font=("Segoe UI", 9, "bold"))
    style.configure("CardValue.TLabel", background=surface, foreground=navy, font=("Segoe UI", 21, "bold"))
    style.configure(
        "Accent.TButton",
        font=("Segoe UI", 10, "bold"),
        padding=(16, 9),
        foreground="white",
        background=teal,
        borderwidth=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", teal_dark), ("pressed", teal_dark), ("disabled", "#91B6B7")],
    )
    style.configure(
        "Secondary.TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(11, 8),
        foreground=navy,
        background=surface,
    )
    style.map("Secondary.TButton", background=[("active", navy_soft)])
    style.configure(
        "Treeview",
        rowheight=31,
        font=("Segoe UI", 9),
        background=surface,
        fieldbackground=surface,
        foreground=text,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        foreground=navy,
        background=navy_soft,
        relief="flat",
        padding=(6, 7),
    )
    style.map("Treeview.Heading", background=[("active", "#DCE6EC")])
    style.configure("TNotebook", background=bg, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        padding=(14, 8),
        font=("Segoe UI", 9, "bold"),
        foreground=muted,
        background=navy_soft,
    )
    style.map(
        "TNotebook.Tab",
        foreground=[("selected", navy)],
        background=[("selected", surface), ("active", teal_soft)],
    )
    style.configure("Asiati.Horizontal.TProgressbar", troughcolor=navy_soft, background=teal, bordercolor=navy_soft)

    selected_folder = tk.StringVar()
    status = tk.StringVar(value="Selecciona una carpeta con hojas de vida PDF o DOCX.")
    progress_value = tk.DoubleVar(value=0)
    search_var = tk.StringVar()
    group_var = tk.StringVar(value="Todos")
    last_excel: dict[str, Path | None] = {"path": None}
    state: dict[str, object] = {"rows": [], "selected": None, "tree_rows": {}}

    # ------------------------------------------------------------------
    # ASIATI header
    # ------------------------------------------------------------------
    brand_bar = tk.Frame(root, bg=navy, padx=24, pady=14)
    brand_bar.pack(fill="x")
    brand_bar.grid_columnconfigure(1, weight=1)

    brand_mark = tk.Frame(brand_bar, bg=navy)
    brand_mark.grid(row=0, column=0, sticky="w")
    tk.Label(
        brand_mark,
        text=BRAND["company"],
        bg=navy,
        fg="white",
        font=("Segoe UI", 23, "bold"),
    ).pack(side="left")
    tk.Label(
        brand_mark,
        text="  /  " + BRAND["product"].upper(),
        bg=navy,
        fg=teal,
        font=("Segoe UI", 10, "bold"),
    ).pack(side="left", pady=(8, 0))
    tk.Label(
        brand_bar,
        text=BRAND["tagline"].upper(),
        bg=navy,
        fg="#B9C8D2",
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=1, sticky="w", padx=(26, 0), pady=(8, 0))
    tk.Label(
        brand_bar,
        text=BRAND["role"],
        bg=teal,
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=14,
        pady=7,
    ).grid(row=0, column=2, sticky="e")

    outer = ttk.Frame(root, style="App.TFrame", padding=(20, 14, 20, 16))
    outer.pack(fill="both", expand=True)

    heading = ttk.Frame(outer, style="App.TFrame")
    heading.pack(fill="x", pady=(0, 9))
    ttk.Label(heading, text="Panel de evaluación de talento", style="Section.TLabel").pack(anchor="w")
    ttk.Label(
        heading,
        text="Ranking local de candidatos · evidencia profesional · revisión humana",
        style="Subtitle.TLabel",
    ).pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------------
    # Folder / analysis controls
    # ------------------------------------------------------------------
    controls = tk.Frame(outer, bg=surface, highlightbackground=border, highlightthickness=1, padx=13, pady=10)
    controls.pack(fill="x", pady=(0, 11))
    controls.grid_columnconfigure(0, weight=1)

    ttk.Entry(controls, textvariable=selected_folder, font=("Segoe UI", 10)).grid(
        row=0, column=0, sticky="ew", padx=(0, 8)
    )

    def choose_folder() -> None:
        folder = filedialog.askdirectory(title="Selecciona la carpeta de hojas de vida")
        if folder:
            selected_folder.set(folder)

    ttk.Button(
        controls,
        text="Seleccionar carpeta",
        command=choose_folder,
        style="Secondary.TButton",
    ).grid(row=0, column=1, padx=(0, 8))
    analyze_btn = ttk.Button(controls, text="Analizar candidatos", style="Accent.TButton")
    analyze_btn.grid(row=0, column=2, padx=(0, 8))
    open_excel_btn = ttk.Button(controls, text="Abrir Excel", state="disabled", style="Secondary.TButton")
    open_excel_btn.grid(row=0, column=3, padx=(0, 8))
    open_folder_btn = ttk.Button(controls, text="Abrir carpeta", state="disabled", style="Secondary.TButton")
    open_folder_btn.grid(row=0, column=4)

    ttk.Progressbar(
        controls,
        maximum=100,
        variable=progress_value,
        style="Asiati.Horizontal.TProgressbar",
    ).grid(row=1, column=0, columnspan=5, sticky="ew", pady=(9, 4))
    ttk.Label(
        controls,
        textvariable=status,
        background=surface,
        foreground=muted,
        font=("Segoe UI", 9),
    ).grid(row=2, column=0, columnspan=5, sticky="w")

    # ------------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------------
    kpi_frame = ttk.Frame(outer, style="App.TFrame")
    kpi_frame.pack(fill="x", pady=(0, 11))
    for idx in range(5):
        kpi_frame.grid_columnconfigure(idx, weight=1, uniform="kpi")

    kpi_vars = {
        "total": tk.StringVar(value="0"),
        "average": tk.StringVar(value="0.0%"),
        "group1": tk.StringVar(value="0"),
        "group2": tk.StringVar(value="0"),
        "review": tk.StringVar(value="0"),
    }
    kpi_specs = [
        ("CANDIDATOS", "total", navy),
        ("PROMEDIO", "average", teal),
        ("GRUPO 1", "group1", PALETTE["group1"]),
        ("GRUPO 2", "group2", PALETTE["group2"]),
        ("REVISIÓN", "review", PALETTE["review"]),
    ]
    for index, (title, key, accent) in enumerate(kpi_specs):
        card = tk.Frame(
            kpi_frame,
            bg=surface,
            highlightbackground=border,
            highlightthickness=1,
            padx=14,
            pady=9,
        )
        card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 5, 0 if index == 4 else 5))
        tk.Frame(card, bg=accent, height=3).pack(fill="x", pady=(0, 7))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=kpi_vars[key], style="CardValue.TLabel").pack(anchor="w", pady=(1, 0))

    # ------------------------------------------------------------------
    # Main area: notebook + fixed evidence panel
    # ------------------------------------------------------------------
    body = ttk.Panedwindow(outer, orient="horizontal")
    body.pack(fill="both", expand=True)

    left = ttk.Frame(body, style="App.TFrame")
    right = tk.Frame(body, bg=surface, highlightbackground=border, highlightthickness=1, padx=15, pady=13)
    body.add(left, weight=4)
    body.add(right, weight=1)

    notebook = ttk.Notebook(left)
    notebook.pack(fill="both", expand=True)

    summary_tab = ttk.Frame(notebook, style="Surface.TFrame")
    ranking_tab = ttk.Frame(notebook, style="Surface.TFrame")
    top_tab = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(summary_tab, text=UI_TABS[0])
    notebook.add(ranking_tab, text=UI_TABS[1])
    notebook.add(top_tab, text=UI_TABS[2])

    # ------------------------------------------------------------------
    # Summary chart tab
    # ------------------------------------------------------------------
    summary_figure = Figure(figsize=(9.5, 5.0), dpi=100, facecolor=surface)
    group_ax = summary_figure.add_subplot(121)
    histogram_ax = summary_figure.add_subplot(122)
    summary_canvas = FigureCanvasTkAgg(summary_figure, master=summary_tab)
    summary_canvas.get_tk_widget().configure(bg=surface, highlightthickness=0)
    summary_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ------------------------------------------------------------------
    # Ranking tab: filters + permanently visible/selectable table
    # ------------------------------------------------------------------
    ranking_tab.grid_rowconfigure(1, weight=1)
    ranking_tab.grid_columnconfigure(0, weight=1)

    filter_bar = tk.Frame(ranking_tab, bg=surface, padx=10, pady=9)
    filter_bar.grid(row=0, column=0, sticky="ew")
    filter_bar.grid_columnconfigure(1, weight=1)
    ttk.Label(filter_bar, text="Buscar", background=surface, foreground=muted).grid(row=0, column=0, padx=(0, 6))
    ttk.Entry(filter_bar, textvariable=search_var).grid(row=0, column=1, sticky="ew", padx=(0, 10))
    ttk.Label(filter_bar, text="Clasificación", background=surface, foreground=muted).grid(row=0, column=2, padx=(0, 6))
    group_combo = ttk.Combobox(
        filter_bar,
        textvariable=group_var,
        state="readonly",
        width=20,
        values=("Todos", "GRUPO 1", "GRUPO 2", "GRUPO 3", "NO PRIORIZAR", "REVISIÓN MANUAL", "ERROR"),
    )
    group_combo.grid(row=0, column=3)

    table_frame = tk.Frame(ranking_tab, bg=surface, highlightbackground=border, highlightthickness=1)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    columns = ("rank", "name", "score", "years", "group", "file")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
    headings = {
        "rank": "#",
        "name": "Candidato",
        "score": "Ajuste %",
        "years": "Años exp.",
        "group": "Clasificación",
        "file": "Archivo",
    }
    widths = {"rank": 44, "name": 190, "score": 80, "years": 80, "group": 225, "file": 210}
    for column in columns:
        tree.heading(column, text=headings[column])
        tree.column(
            column,
            width=widths[column],
            minwidth=40,
            anchor="center" if column in {"rank", "score", "years"} else "w",
        )

    tree.tag_configure("g1", background=PALETTE["group1_bg"])
    tree.tag_configure("g2", background=PALETTE["group2_bg"])
    tree.tag_configure("g3", background=PALETTE["group3_bg"])
    tree.tag_configure("low", background=PALETTE["low_bg"])
    tree.tag_configure("review", background=PALETTE["review_bg"])
    tree.grid(row=0, column=0, sticky="nsew")
    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    yscroll.grid(row=0, column=1, sticky="ns")
    xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    xscroll.grid(row=1, column=0, sticky="ew")
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    # ------------------------------------------------------------------
    # Top 10 chart tab
    # ------------------------------------------------------------------
    top_figure = Figure(figsize=(9.5, 5.0), dpi=100, facecolor=surface)
    top_ax = top_figure.add_subplot(111)
    top_canvas = FigureCanvasTkAgg(top_figure, master=top_tab)
    top_canvas.get_tk_widget().configure(bg=surface, highlightthickness=0)
    top_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ------------------------------------------------------------------
    # Candidate evidence panel
    # ------------------------------------------------------------------
    tk.Label(right, text="EVIDENCIA DEL CV", bg=surface, fg=teal_dark, font=("Segoe UI", 8, "bold")).pack(anchor="w")
    tk.Label(right, text="Detalle del candidato", bg=surface, fg=navy, font=("Segoe UI", 15, "bold")).pack(
        anchor="w", pady=(2, 0)
    )

    detail_name = tk.StringVar(value="Selecciona un candidato")
    detail_meta = tk.StringVar(value="Ve a 'Ranking de candidatos' y haz clic en una fila.")
    tk.Label(
        right,
        textvariable=detail_name,
        bg=surface,
        fg=text,
        font=("Segoe UI", 12, "bold"),
        wraplength=300,
        justify="left",
    ).pack(anchor="w", pady=(10, 2))
    tk.Label(
        right,
        textvariable=detail_meta,
        bg=surface,
        fg=muted,
        font=("Segoe UI", 9),
        wraplength=300,
        justify="left",
    ).pack(anchor="w", pady=(0, 9))

    open_cv_btn = ttk.Button(right, text="Abrir CV", state="disabled", style="Secondary.TButton")
    open_cv_btn.pack(anchor="w", pady=(0, 8))

    evidence_scroll_host = tk.Frame(right, bg=surface)
    evidence_scroll_host.pack(fill="both", expand=True, pady=(2, 0))
    evidence_scroll_host.grid_rowconfigure(0, weight=1)
    evidence_scroll_host.grid_columnconfigure(0, weight=1)

    evidence_canvas = tk.Canvas(
        evidence_scroll_host,
        bg=surface,
        bd=0,
        highlightthickness=0,
        yscrollincrement=18,
    )
    evidence_scrollbar = ttk.Scrollbar(
        evidence_scroll_host,
        orient="vertical",
        command=evidence_canvas.yview,
    )
    evidence_canvas.configure(yscrollcommand=evidence_scrollbar.set)
    evidence_canvas.grid(row=0, column=0, sticky="nsew")
    evidence_scrollbar.grid(row=0, column=1, sticky="ns", padx=(5, 0))

    evidence_content = tk.Frame(evidence_canvas, bg=surface)
    evidence_window = evidence_canvas.create_window((0, 0), window=evidence_content, anchor="nw")

    def resize_evidence_content(_event=None) -> None:
        evidence_canvas.configure(scrollregion=evidence_canvas.bbox("all"))

    def resize_evidence_window(event) -> None:
        evidence_canvas.itemconfigure(evidence_window, width=event.width)

    evidence_content.bind("<Configure>", resize_evidence_content)
    evidence_canvas.bind("<Configure>", resize_evidence_window)

    def on_evidence_mousewheel(event) -> str:
        units = mousewheel_scroll_units(int(getattr(event, "delta", 0) or 0))
        if units:
            evidence_canvas.yview_scroll(units, "units")
        return "break"

    def on_evidence_linux_scroll(event) -> str:
        if getattr(event, "num", None) == 4:
            evidence_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            evidence_canvas.yview_scroll(1, "units")
        return "break"

    def enable_evidence_mousewheel(_event=None) -> None:
        root.bind_all("<MouseWheel>", on_evidence_mousewheel)
        root.bind_all("<Button-4>", on_evidence_linux_scroll)
        root.bind_all("<Button-5>", on_evidence_linux_scroll)

    def disable_evidence_mousewheel(_event=None) -> None:
        root.unbind_all("<MouseWheel>")
        root.unbind_all("<Button-4>")
        root.unbind_all("<Button-5>")

    evidence_canvas.bind("<Enter>", enable_evidence_mousewheel)
    evidence_canvas.bind("<Leave>", disable_evidence_mousewheel)
    evidence_content.bind("<Enter>", enable_evidence_mousewheel)
    evidence_content.bind("<Leave>", disable_evidence_mousewheel)

    def add_detail_box(title: str, height: int = 4) -> tk.Text:
        tk.Label(
            evidence_content,
            text=title.upper(),
            bg=surface,
            fg=navy,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(6, 3))
        box = tk.Text(
            evidence_content,
            height=height,
            wrap="word",
            relief="solid",
            bd=1,
            bg="#FAFCFD",
            fg=text,
            insertbackground=text,
            highlightbackground=border,
            font=("Segoe UI", 9),
            padx=8,
            pady=6,
        )
        box.pack(fill="x")
        box.configure(state="disabled")
        return box

    strengths_box = add_detail_box("Fortalezas")
    gaps_box = add_detail_box("Brechas")
    breakdown_box = add_detail_box("Desglose", height=5)

    tk.Label(
        evidence_content,
        text="Soporte para revisión humana. La puntuación usa únicamente evidencia profesional del CV.",
        bg=surface,
        fg=muted,
        font=("Segoe UI", 8),
        wraplength=285,
        justify="left",
    ).pack(anchor="w", pady=(9, 8))

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
        axis.set_facecolor(surface)
        axis.set_title(title, loc="left", fontsize=10, fontweight="bold", color=navy, pad=10)
        axis.tick_params(colors=muted, labelsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
        axis.grid(axis="x", color=navy_soft, linewidth=0.8)
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
        values = [
            summary["group_1"],
            summary["group_2"],
            summary["group_3"],
            summary["not_prioritized"],
            summary["review"],
        ]
        colors = [
            PALETTE["group1"],
            PALETTE["group2"],
            PALETTE["group3"],
            PALETTE["low"],
            PALETTE["review"],
        ]
        group_ax.barh(labels[::-1], values[::-1], color=colors[::-1])
        for index, value in enumerate(values[::-1]):
            group_ax.text(value + 0.15, index, str(value), va="center", fontsize=8, color=text)

        histogram = score_histogram(rows)
        histogram_ax.bar([label for label, _ in histogram], [count for _, count in histogram], color=teal)
        histogram_ax.set_ylim(bottom=0)

        top = top_candidates(rows, limit=10)
        if top:
            names = [str(row.get("Nombre", ""))[:28] for row in top][::-1]
            scores = [float(row.get("Ajuste %", 0) or 0) for row in top][::-1]
            top_ax.barh(names, scores, color=teal)
            top_ax.set_xlim(0, 100)
            for index, score in enumerate(scores):
                top_ax.text(min(score + 1, 96), index, f"{score:.0f}%", va="center", fontsize=8, color=text)
        else:
            top_ax.text(
                0.5,
                0.5,
                "Sin resultados para mostrar",
                ha="center",
                va="center",
                transform=top_ax.transAxes,
                color=muted,
            )
            top_ax.set_xticks([])
            top_ax.set_yticks([])

        summary_figure.tight_layout(pad=2.0)
        top_figure.tight_layout(pad=2.0)
        summary_canvas.draw_idle()
        top_canvas.draw_idle()

    def visible_rows() -> list[dict]:
        return filter_rows(state["rows"], query=search_var.get(), group=group_var.get())  # type: ignore[arg-type]

    def display_candidate(row: dict) -> None:
        state["selected"] = row
        detail_name.set(str(row.get("Nombre", "Candidato")))
        detail_meta.set(
            f'{row.get("Ajuste %", 0)}% ajuste · '
            f'{row.get("Años experiencia estimados", 0)} años · '
            f'{row.get("Clasificación", "")}'
        )
        set_text(strengths_box, str(row.get("Experiencia / fortalezas", "")))
        set_text(gaps_box, str(row.get("Brechas", "")))
        set_text(breakdown_box, str(row.get("Desglose", "")))
        evidence_canvas.yview_moveto(0.0)
        open_cv_btn.configure(state="normal")

    def show_selected(_event=None) -> None:
        selection = tree.selection()
        if not selection:
            return
        tree_rows = state.get("tree_rows")
        if not isinstance(tree_rows, dict):
            return
        row = tree_rows.get(selection[0])
        if isinstance(row, dict):
            display_candidate(row)

    def refresh_table(*_args, select_first: bool = False) -> None:
        rows = visible_rows()
        selected = state.get("selected")
        selected_file = str(selected.get("Archivo", "")) if isinstance(selected, dict) else ""

        for item in tree.get_children():
            tree.delete(item)

        tree_rows: dict[str, dict] = {}
        selected_iid = ""
        for rank, row in enumerate(rows, 1):
            iid = f"row-{rank}"
            tree_rows[iid] = row
            tree.insert(
                "",
                "end",
                iid=iid,
                tags=(row_tag(row),),
                values=(
                    rank,
                    row.get("Nombre", ""),
                    row.get("Ajuste %", 0),
                    row.get("Años experiencia estimados", 0),
                    row.get("Clasificación", ""),
                    row.get("Archivo", ""),
                ),
            )
            if selected_file and str(row.get("Archivo", "")) == selected_file:
                selected_iid = iid

        state["tree_rows"] = tree_rows
        refresh_charts(rows)

        target_iid = selected_iid or (tree.get_children()[0] if select_first and tree.get_children() else "")
        if target_iid:
            tree.selection_set(target_iid)
            tree.focus(target_iid)
            tree.see(target_iid)
            show_selected()

    def open_selected_cv() -> None:
        row = state.get("selected")
        folder_text = selected_folder.get().strip()
        if isinstance(row, dict) and folder_text:
            candidate_path = Path(folder_text) / str(row.get("Archivo", ""))
            if candidate_path.exists():
                open_path(candidate_path)
            else:
                messagebox.showwarning(WINDOW_TITLE, "No se encontró el archivo original del candidato.")

    def open_selected_cv_from_double_click(_event=None) -> None:
        show_selected()
        open_selected_cv()

    tree.bind("<<TreeviewSelect>>", show_selected)
    tree.bind("<Double-1>", open_selected_cv_from_double_click)
    open_cv_btn.configure(command=open_selected_cv)
    search_var.trace_add("write", refresh_table)
    group_var.trace_add("write", refresh_table)

    def start_analysis() -> None:
        folder_text = selected_folder.get().strip()
        folder = Path(folder_text) if folder_text else None
        if not folder or not folder.exists() or not folder.is_dir():
            messagebox.showwarning(WINDOW_TITLE, "Selecciona una carpeta válida.")
            return

        candidates = [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in {".pdf", ".docx"}
        ]
        if not candidates:
            messagebox.showwarning(WINDOW_TITLE, "La carpeta no contiene archivos PDF o DOCX.")
            return

        analyze_btn.configure(state="disabled")
        open_excel_btn.configure(state="disabled")
        open_folder_btn.configure(state="disabled")
        progress_value.set(0)
        status.set(f"Preparando {len(candidates)} hojas de vida...")

        def update_progress(done: int, total: int, name: str) -> None:
            percentage = (done / total * 100) if total else 0
            root.after(0, lambda value=percentage: progress_value.set(value))
            root.after(0, lambda message=f"Procesando {done}/{total}: {name}": status.set(message))

        def finish_success(rows: list[dict], xlsx_path: Path) -> None:
            state["rows"] = rows
            state["selected"] = None
            last_excel["path"] = xlsx_path
            refresh_kpis(rows)
            refresh_table(select_first=True)
            notebook.select(ranking_tab)
            status.set(
                f"Listo: {len(rows)} hojas de vida procesadas. "
                "Selecciona una fila del ranking para revisar la evidencia; doble clic abre el CV."
            )
            progress_value.set(100)
            open_excel_btn.configure(state="normal")
            open_folder_btn.configure(state="normal")

        def worker() -> None:
            try:
                rows, xlsx_path, _csv_path = run_analysis(folder, progress=update_progress)
                root.after(0, lambda rows=rows, path=xlsx_path: finish_success(rows, path))
            except Exception as exc:
                error_message = str(exc)
                root.after(
                    0,
                    lambda message=error_message: messagebox.showerror(
                        WINDOW_TITLE,
                        f"No se pudo completar el análisis:\n{message}",
                    ),
                )
                root.after(0, lambda: status.set("El análisis terminó con error."))
            finally:
                root.after(0, lambda: analyze_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    analyze_btn.configure(command=start_analysis)
    open_excel_btn.configure(command=lambda: open_path(last_excel["path"]) if last_excel["path"] else None)
    open_folder_btn.configure(command=lambda: open_path(Path(selected_folder.get())) if selected_folder.get() else None)

    refresh_charts([])
    root.mainloop()
