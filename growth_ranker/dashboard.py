"""Pure helpers for dashboard metrics, filtering and chart data."""

from __future__ import annotations

from collections.abc import Iterable


UNSCORED_PREFIXES = ("REVISIÓN MANUAL", "ERROR")


def _is_scored(row: dict) -> bool:
    classification = str(row.get("Clasificación", "") or "")
    return not classification.startswith(UNSCORED_PREFIXES)


def dashboard_summary(rows: Iterable[dict]) -> dict[str, int | float]:
    items = list(rows)
    scored = [row for row in items if _is_scored(row)]
    scores = [float(row.get("Ajuste %", 0) or 0) for row in scored]

    def count_prefix(prefix: str) -> int:
        return sum(str(row.get("Clasificación", "") or "").startswith(prefix) for row in items)

    return {
        "total": len(items),
        "scored": len(scored),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "group_1": count_prefix("GRUPO 1"),
        "group_2": count_prefix("GRUPO 2"),
        "group_3": count_prefix("GRUPO 3"),
        "not_prioritized": count_prefix("NO PRIORIZAR"),
        "review": len(items) - len(scored),
    }


def score_histogram(rows: Iterable[dict]) -> list[tuple[str, int]]:
    buckets = [
        ("0-19", 0, 20),
        ("20-39", 20, 40),
        ("40-59", 40, 60),
        ("60-79", 60, 80),
        ("80-100", 80, 101),
    ]
    counts = {label: 0 for label, _, _ in buckets}
    for row in rows:
        if not _is_scored(row):
            continue
        score = float(row.get("Ajuste %", 0) or 0)
        for label, low, high in buckets:
            if low <= score < high:
                counts[label] += 1
                break
    return [(label, counts[label]) for label, _, _ in buckets]


def filter_rows(rows: Iterable[dict], query: str = "", group: str = "Todos") -> list[dict]:
    query_norm = query.strip().casefold()
    group_norm = group.strip().casefold()
    filtered: list[dict] = []
    for row in rows:
        classification = str(row.get("Clasificación", "") or "")
        if group_norm and group_norm != "todos" and group_norm not in classification.casefold():
            continue
        searchable = " ".join(
            [
                str(row.get("Nombre", "") or ""),
                str(row.get("Archivo", "") or ""),
                classification,
            ]
        ).casefold()
        if query_norm and query_norm not in searchable:
            continue
        filtered.append(row)
    return filtered


def top_candidates(rows: Iterable[dict], limit: int = 10) -> list[dict]:
    scored = [row for row in rows if _is_scored(row)]
    return sorted(scored, key=lambda row: float(row.get("Ajuste %", 0) or 0), reverse=True)[:limit]
