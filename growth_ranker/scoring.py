"""Marketing evidence detection, scoring, summaries, and classification."""

from __future__ import annotations

import re

from .experience import estimate_years_experience
from .profile import PROFILE
from .text import normalize_text, phrase_hits


def find_money_mentions(text: str) -> list[str]:
    patterns = [
        r"\$\s?[\d\.,]+\s?(?:mm|m|millones|cop|usd)?",
        r"\b\d+(?:[\.,]\d+)?\s?(?:millones|mm)\s?(?:cop|usd)?\b",
        r"\b(?:cop|usd)\s?[\d\.,]+(?:\s?(?:millones|mm|m))?",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, re.IGNORECASE))
    return list(dict.fromkeys(found))[:5]


def find_percentage_mentions(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b\d+(?:[\.,]\d+)?\s?%", text)))[:8]


def find_ratio_mentions(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b\d+(?:[\.,]\d+)?\s?x\b", text, re.IGNORECASE)))[:5]


def _contextual_quantified_results(text: str) -> list[str]:
    normalized = normalize_text(text)
    metric = r"(?:ventas|ingresos|revenue|conversion|roi|roas|cac|ltv|cpl|cpa|ctr|leads?|facturacion|trafico|retencion)"
    verb = r"(?:aumente|aumento|incremente|incremento|creci|crecimiento|reduje|reduccion|disminui|mejore|mejora|optimice|optimizo|alcance|logre|genere|duplique|triplique)"
    value = r"(?:\d+(?:[\.,]\d+)?\s?%|\d+(?:[\.,]\d+)?\s?x|(?:cop|usd|\$)\s?[\d\.,]+(?:\s?(?:millones|mm|m))?)"
    patterns = [
        rf"\b{verb}\b.{{0,55}}\b{metric}\b.{{0,35}}{value}",
        rf"\b{verb}\b.{{0,55}}{value}.{{0,35}}\b{metric}\b",
        rf"\b{metric}\b.{{0,35}}{value}",
    ]
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, normalized, re.IGNORECASE):
            snippet = match.group(0).strip()
            if snippet not in found:
                found.append(snippet)
    return found[:8]


def _coverage_ratio(hit_count: int) -> float:
    if hit_count <= 0:
        return 0.0
    if hit_count == 1:
        return 0.40
    if hit_count == 2:
        return 0.70
    if hit_count == 3:
        return 0.90
    return 1.0


def experience_points(years: float) -> float:
    if years >= 8:
        return 15.0
    if years >= 6:
        return 13.5
    if years >= 4:
        return 10.0
    if years >= 2:
        return 6.0
    if years > 0:
        return 3.0
    return 0.0


def classify_score(score: float) -> str:
    if score >= 90:
        return "GRUPO 1 - Prioridad alta"
    if score >= 82:
        return "GRUPO 2 - Entrevistar / validar"
    if score >= 74:
        return "GRUPO 3 - Reserva con potencial"
    return "NO PRIORIZAR para Lead"


def score_candidate(text: str, *, years_override: float | None = None) -> dict:
    normalized = normalize_text(text)
    years = years_override if years_override is not None else estimate_years_experience(text)
    evidence: dict[str, list[str]] = {}
    details: dict[str, float] = {}
    total = 0.0

    for criterion, cfg in PROFILE["criterios"].items():
        hits = phrase_hits(normalized, cfg["keywords"])
        evidence[criterion] = hits
        ratio = _coverage_ratio(len(hits))
        strong_patterns = cfg.get("strong_patterns", [])
        strong_hits = [pattern for pattern in strong_patterns if re.search(pattern, normalized, re.IGNORECASE)]
        if strong_hits:
            ratio = max(ratio, 0.85 if len(strong_hits) == 1 else 1.0)
        points = round(cfg["peso"] * ratio, 1)
        details[criterion] = points
        total += points

    exp_points = experience_points(years)
    details["experiencia"] = exp_points
    total += exp_points

    money = find_money_mentions(text)
    percentages = find_percentage_mentions(text)
    ratios = find_ratio_mentions(text)
    quantified = _contextual_quantified_results(text)
    quantitative_points = 0.0
    if money or percentages or ratios:
        quantitative_points = 1.5
    if quantified:
        quantitative_points = min(15.0, 3.0 + len(quantified) * 4.0)
    details["resultados_cuantitativos"] = round(quantitative_points, 1)
    total += quantitative_points

    raw = min(100.0, total)
    if not evidence["estrategia_growth"] or not evidence["conexion_comercial"]:
        raw = min(raw, 74.0)
    if not evidence["presupuesto"] and not evidence["metricas_resultados"]:
        raw = min(raw, 79.0)
    score = round(raw, 1)

    return {
        "score": score,
        "recommendation": classify_score(score),
        "years": round(float(years), 1),
        "evidence": evidence,
        "details": details,
        "money": money,
        "percentages": percentages,
        "ratios": ratios,
        "quantified_results": quantified,
    }


def build_experience_summary(result: dict) -> str:
    parts: list[str] = []
    if result["years"]:
        parts.append(f"Experiencia estimada: {result['years']} años")
    labels = {
        "estrategia_growth": "estrategia/growth",
        "conexion_comercial": "marketing + comercial",
        "presupuesto": "presupuesto",
        "metricas_resultados": "métricas/ROI",
        "campanas_activaciones_eventos": "campañas/eventos",
        "digital_paid_media": "paid media",
        "crm_automatizacion": "CRM/automatización",
        "liderazgo": "liderazgo",
        "sectores_deseables": "sectores afines",
    }
    strong = [labels[key] for key, hits in result["evidence"].items() if len(hits) >= 2]
    if strong:
        parts.append("Fortalezas: " + ", ".join(strong))
    if result["quantified_results"]:
        parts.append(f"Resultados cuantificados detectados: {len(result['quantified_results'])}")
    if result["money"]:
        parts.append("Montos: " + ", ".join(result["money"][:3]))
    return " | ".join(parts)


def build_gaps(result: dict) -> str:
    missing: list[str] = []
    if not result["evidence"]["estrategia_growth"]:
        missing.append("sin evidencia clara de estrategia/growth")
    if not result["evidence"]["conexion_comercial"]:
        missing.append("sin conexión comercial clara")
    if not result["evidence"]["presupuesto"]:
        missing.append("sin evidencia clara de presupuesto")
    if not result["evidence"]["metricas_resultados"]:
        missing.append("sin evidencia fuerte de ROI/métricas")
    if not result["evidence"]["campanas_activaciones_eventos"]:
        missing.append("poca evidencia de eventos/activaciones")
    if result["years"] < PROFILE["experiencia_objetivo_min"]:
        missing.append("seniority menor a 6 años")
    if not result["quantified_results"]:
        missing.append("sin resultados cuantificados contextualizados")
    return "; ".join(missing)


def build_score_breakdown(result: dict) -> str:
    labels = {
        "estrategia_growth": "Estrategia",
        "conexion_comercial": "Comercial",
        "presupuesto": "Presupuesto",
        "metricas_resultados": "Métricas",
        "campanas_activaciones_eventos": "Campañas",
        "digital_paid_media": "Digital",
        "crm_automatizacion": "CRM",
        "liderazgo": "Liderazgo",
        "sectores_deseables": "Sector",
        "experiencia": "Experiencia",
        "resultados_cuantitativos": "Resultados",
    }
    return " | ".join(f"{labels[key]} {value:g}" for key, value in result["details"].items())
