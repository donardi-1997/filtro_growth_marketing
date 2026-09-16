# Modular Architecture Design

## Objective

Refactor the existing `marketing_cv_ranker.py` monolith without changing user-visible behavior or scoring results.

## Constraints

- Keep the application local and Windows-friendly.
- Keep the existing GUI flow: choose one folder of CVs, analyze, show ranking, open Excel/folder.
- Keep the CLI flags `--carpeta` and `--salida`.
- Keep output filenames and worksheet name unchanged.
- Keep current scoring weights, thresholds, keyword sets, experience rules, and PDF/DOCX support unchanged.
- Keep PyInstaller output name `RankingMarketing.exe` unchanged.
- Existing tests must continue to pass; add architecture/import coverage for the new package boundaries.

## Package structure

Create a `growth_ranker` package with focused modules:

- `profile.py`: scoring profile and constants.
- `text.py`: text normalization, contact extraction, name extraction, phrase matching.
- `documents.py`: PDF/DOCX extraction.
- `experience.py`: work-section detection, date ranges, interval merge, seniority calculation.
- `scoring.py`: money/percentage/ratio evidence, quantified results, score computation and classification.
- `exporting.py`: folder processing and Excel/CSV export.
- `gui.py`: Tkinter UI and platform-specific open-path behavior.
- `cli.py`: command-line parsing and application entrypoint.

`marketing_cv_ranker.py` becomes a thin compatibility/entrypoint module that re-exports the public functions used by existing tests and invokes `growth_ranker.cli.main()`.

## Data flow

`CLI/GUI -> exporting.run_analysis -> documents.extract_text -> text/experience/scoring -> exporting -> XLSX/CSV`.

No module may import the GUI from the scoring/domain layer. Domain modules remain independently testable.

## Error handling

Per-file extraction/scoring failures continue to produce a ranking row with `Clasificación = ERROR` rather than aborting the whole folder. PDFs without extractable text continue to produce the manual-review row.

## Verification

- Existing 9 behavioral tests remain green.
- Add tests proving the compatibility module delegates to the package and package modules import independently.
- Run `python -m pytest -q`.
- Run `python -m py_compile marketing_cv_ranker.py growth_ranker/*.py`.
- GitHub Actions must build `RankingMarketing.exe` successfully on Windows before merge.
