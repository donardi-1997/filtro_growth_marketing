# Modular Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the 817-line ranker into focused modules while preserving all current scoring, CLI, GUI, export, and Windows build behavior.

**Architecture:** Introduce a `growth_ranker` package that owns domain and UI responsibilities in separate modules. Keep `marketing_cv_ranker.py` as a compatibility facade and executable entrypoint so current imports and PyInstaller configuration remain valid.

**Tech Stack:** Python 3.13, Tkinter, pypdf, python-docx, openpyxl, pytest, PyInstaller.

**Spec:** `docs/superpowers/specs/2026-09-16-modular-architecture-design.md`

## Global Constraints

- Do not change scoring weights, thresholds, keywords, experience rules, file formats, output names, or GUI flow.
- Preserve `RankingMarketing.exe` as the PyInstaller output.
- Preserve public imports currently used by `tests/test_ranker.py`.
- Folder-level processing must remain resilient to one bad CV.

---

### Task 1: Add architecture contract tests

**Files:**
- Modify: `tests/test_ranker.py`
- Create: `growth_ranker/__init__.py`

**Interfaces:**
- Produces: importable package namespace `growth_ranker`.
- Verifies: compatibility exports still resolve from `marketing_cv_ranker` after refactor.

- [ ] Add a test importing `growth_ranker.profile`, `growth_ranker.text`, `growth_ranker.documents`, `growth_ranker.experience`, `growth_ranker.scoring`, `growth_ranker.exporting`, `growth_ranker.gui`, and `growth_ranker.cli`.
- [ ] Add a test asserting `marketing_cv_ranker.score_candidate is growth_ranker.scoring.score_candidate` and equivalent compatibility exports.
- [ ] Run the tests and confirm they fail because the modules do not exist yet.

### Task 2: Extract domain modules

**Files:**
- Create: `growth_ranker/profile.py`
- Create: `growth_ranker/text.py`
- Create: `growth_ranker/documents.py`
- Create: `growth_ranker/experience.py`
- Create: `growth_ranker/scoring.py`

**Interfaces:**
- `profile.PROFILE`, `profile.MONTHS`, section-heading constants.
- `text.normalize_text(text)`, `phrase_hits(text, phrases)`, contact/name extraction helpers.
- `documents.extract_text(path)` plus PDF/DOCX readers.
- `experience.estimate_years_experience(text, *, now_year=None, now_month=None)`.
- `scoring.score_candidate(text, *, years_override=None)`, `classify_score(score)` and summary helpers.

- [ ] Move constants and functions without changing logic.
- [ ] Replace intra-file references with explicit package imports.
- [ ] Run focused scoring/experience tests until green.

### Task 3: Extract processing/export layer

**Files:**
- Create: `growth_ranker/exporting.py`

**Interfaces:**
- `process_folder(folder, progress=None) -> list[dict]`.
- `export_csv(rows, out_path) -> None`.
- `export_excel(rows, out_path) -> None`.
- `run_analysis(folder, output_dir=None, progress=None) -> tuple[list[dict], Path, Path]`.

- [ ] Move folder orchestration and XLSX/CSV generation unchanged.
- [ ] Run the end-to-end folder/export test and confirm it remains green.

### Task 4: Extract GUI and CLI

**Files:**
- Create: `growth_ranker/gui.py`
- Create: `growth_ranker/cli.py`
- Modify: `marketing_cv_ranker.py`

**Interfaces:**
- `gui.launch_gui() -> None`.
- `cli.cli_main(args) -> int`.
- `cli.main() -> int`.
- `marketing_cv_ranker.py` re-exports legacy public functions and delegates execution to `cli.main()`.

- [ ] Move Tkinter and platform open-path logic to `gui.py`.
- [ ] Move argparse logic to `cli.py`.
- [ ] Replace `marketing_cv_ranker.py` with the compatibility facade.
- [ ] Run all tests.

### Task 5: Verify packaging and documentation

**Files:**
- Modify: `README.md` only if architecture/dev instructions need clarification.
- Verify: `RankingMarketing.spec` and `.github/workflows/build-windows-exe.yml`.

**Interfaces:**
- PyInstaller entry remains `marketing_cv_ranker.py`.

- [ ] Run `python -m pytest -q` and require zero failures.
- [ ] Run `python -m py_compile marketing_cv_ranker.py growth_ranker/*.py` and require exit 0.
- [ ] Open a PR to `main` and require the Windows GitHub Actions build to succeed before merge.
