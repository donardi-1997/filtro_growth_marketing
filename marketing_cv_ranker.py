#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility facade and executable entrypoint for RankingMarketing.

The implementation lives in the focused ``growth_ranker`` package. Public
imports from the original single-file version are re-exported here so existing
scripts, tests, and the PyInstaller entrypoint continue to work unchanged.
"""

from growth_ranker.cli import cli_main, main
from growth_ranker.documents import extract_text, read_docx, read_pdf
from growth_ranker.experience import (
    estimate_years_experience,
    extract_date_ranges,
    extract_work_experience_text,
    merge_intervals,
    month_num,
)
from growth_ranker.exporting import export_csv, export_excel, process_folder, run_analysis
from growth_ranker.gui import launch_gui, open_path
from growth_ranker.profile import APP_TITLE, MONTHS, PROFILE
from growth_ranker.scoring import (
    build_experience_summary,
    build_gaps,
    build_score_breakdown,
    classify_score,
    experience_factor,
    find_money_mentions,
    find_percentage_mentions,
    find_ratio_mentions,
    score_candidate,
)
from growth_ranker.text import (
    extract_email,
    extract_phone,
    guess_name,
    normalize_line,
    normalize_phone,
    normalize_text,
    phrase_hits,
)

__all__ = [
    "APP_TITLE",
    "MONTHS",
    "PROFILE",
    "build_experience_summary",
    "build_gaps",
    "build_score_breakdown",
    "classify_score",
    "cli_main",
    "estimate_years_experience",
    "experience_factor",
    "export_csv",
    "export_excel",
    "extract_date_ranges",
    "extract_email",
    "extract_phone",
    "extract_text",
    "extract_work_experience_text",
    "find_money_mentions",
    "find_percentage_mentions",
    "find_ratio_mentions",
    "guess_name",
    "launch_gui",
    "main",
    "merge_intervals",
    "month_num",
    "normalize_line",
    "normalize_phone",
    "normalize_text",
    "open_path",
    "phrase_hits",
    "process_folder",
    "read_docx",
    "read_pdf",
    "run_analysis",
    "score_candidate",
]


if __name__ == "__main__":
    raise SystemExit(main())
