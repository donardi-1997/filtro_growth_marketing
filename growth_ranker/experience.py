"""Work-history section detection and experience estimation."""

from __future__ import annotations

import re
from datetime import datetime

from .profile import EDUCATION_HEADINGS, MONTHS, OTHER_SECTION_HEADINGS, WORK_HEADINGS
from .text import normalize_line, normalize_text


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 70:
        return False
    words = stripped.split()
    if len(words) > 7:
        return False
    letters = [ch for ch in stripped if ch.isalpha()]
    if not letters:
        return False
    uppercase_ratio = sum(ch.isupper() for ch in letters) / len(letters)
    return uppercase_ratio >= 0.72 or stripped.endswith(":")


def extract_work_experience_text(text: str) -> str:
    lines = text.splitlines()
    mode = "neutral"
    work_found = False
    work_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        heading = normalize_line(line)
        if heading in WORK_HEADINGS or any(heading.startswith(h + " ") for h in WORK_HEADINGS if len(h) > 10):
            mode = "work"
            work_found = True
            continue
        if heading in EDUCATION_HEADINGS or any(heading.startswith(h + " ") for h in EDUCATION_HEADINGS if len(h) > 10):
            mode = "education"
            continue
        if heading in OTHER_SECTION_HEADINGS and mode == "work":
            mode = "neutral"
            continue
        if mode == "work":
            if _looks_like_heading(line) and not re.search(r"\b(?:19|20)\d{2}\b", line):
                normalized = normalize_line(line)
                if normalized not in WORK_HEADINGS:
                    mode = "neutral"
                    continue
            work_lines.append(line)

    if work_found and work_lines:
        return "\n".join(work_lines)

    filtered: list[str] = []
    education_mode = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        heading = normalize_line(line)
        if heading in EDUCATION_HEADINGS:
            education_mode = True
            continue
        if heading in WORK_HEADINGS or (education_mode and heading in OTHER_SECTION_HEADINGS):
            education_mode = False
        if education_mode:
            continue
        if re.search(r"\b(?:universidad|university|instituto|college|licenciatura|pregrado|posgrado|maestria|master|diplomado)\b", normalize_text(line)):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def month_num(token: str) -> int:
    return MONTHS.get(normalize_text(token).strip("."), 1)


def extract_date_ranges(text: str, now: datetime | None = None) -> list[tuple[datetime, datetime]]:
    now = now or datetime.now()
    normalized = normalize_text(text)
    ranges: list[tuple[datetime, datetime]] = []
    month_names = "|".join(sorted((re.escape(key) for key in MONTHS), key=len, reverse=True))
    present_words = r"(?:actualidad|actualmente|presente|present|current|hoy)"
    month_pattern = re.compile(
        rf"(?<!\w)({month_names})\s+((?:19|20)\d{{2}})\s*-\s*"
        rf"(?:(?:({month_names})\s+((?:19|20)\d{{2}}))|({present_words}))(?!\w)",
        re.IGNORECASE,
    )
    occupied: list[tuple[int, int]] = []
    for match in month_pattern.finditer(normalized):
        sm, sy, em, ey, present = match.groups()
        start = datetime(int(sy), month_num(sm), 1)
        end = now if present else datetime(int(ey), month_num(em), 1)
        if 1990 <= start.year <= now.year and start <= end:
            ranges.append((start, end))
            occupied.append(match.span())

    year_pattern = re.compile(
        rf"(?<!\w)((?:19|20)\d{{2}})\s*-\s*((?:19|20)\d{{2}}|actualidad|actualmente|presente|present|current)(?!\w)",
        re.IGNORECASE,
    )
    for match in year_pattern.finditer(normalized):
        if any(match.start() >= start and match.end() <= end for start, end in occupied):
            continue
        sy, ey = match.groups()
        start = datetime(int(sy), 1, 1)
        end = now if not ey.isdigit() else datetime(int(ey), 12, 1)
        if 1990 <= start.year <= now.year and start <= end:
            ranges.append((start, end))
    return ranges


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: item[0])
    merged: list[list[datetime]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        last = merged[-1]
        if (start - last[1]).days <= 31:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def estimate_years_experience(text: str, *, now_year: int | None = None, now_month: int | None = None) -> float:
    current = datetime.now()
    now = datetime(now_year or current.year, now_month or current.month, 1)
    work_text = extract_work_experience_text(text)
    intervals = merge_intervals(extract_date_ranges(work_text, now=now))
    total_days = sum((end - start).days for start, end in intervals)
    return round(total_days / 365.25, 1)
