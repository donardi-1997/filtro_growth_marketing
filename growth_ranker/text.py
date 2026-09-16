"""Text normalization and candidate identity/contact extraction."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?57[\s\-\.]?)?(?:3\d{2})[\s\-\.]?\d{3}[\s\-\.]?\d{4}(?!\d)")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def normalize_line(text: str) -> str:
    return re.sub(r"[^a-z0-9 +&/\-]", "", normalize_text(text)).strip(" :-|")


def phrase_hits(text: str, phrases: Iterable[str]) -> list[str]:
    norm = normalize_text(text)
    hits: list[str] = []
    for phrase in phrases:
        phrase_norm = normalize_text(phrase)
        if not phrase_norm:
            continue
        pattern = rf"(?<!\w){re.escape(phrase_norm)}(?!\w)"
        if re.search(pattern, norm, re.IGNORECASE):
            hits.append(phrase)
    return hits


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("57") and len(digits) >= 12:
        digits = digits[2:]
    if len(digits) == 10:
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
    return phone.strip()


def extract_email(text: str) -> str:
    matches = EMAIL_RE.findall(text)
    return matches[0] if matches else ""


def extract_phone(text: str) -> str:
    phones: list[str] = []
    for match in PHONE_RE.findall(text):
        phone = normalize_phone(match)
        if phone not in phones:
            phones.append(phone)
    return " / ".join(phones[:2])


def guess_name(filename: str, text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    bad_tokens = {
        "perfil", "experiencia", "educacion", "contacto", "curriculum", "hoja de vida",
        "resumen profesional", "habilidades", "formacion", "marketing", "growth",
    }
    for line in lines[:12]:
        low = normalize_text(line)
        if any(token in low for token in bad_tokens):
            continue
        words = line.split()
        alpha_ratio = sum(ch.isalpha() or ch.isspace() for ch in line) / max(1, len(line))
        if 2 <= len(words) <= 6 and alpha_ratio > 0.80 and len(line) <= 60:
            return line.title()
    stem = Path(filename).stem
    stem = re.sub(r"(?i)^cv[\s_\-]*", "", stem)
    stem = re.sub(r"[_\-]+", " ", stem)
    return re.sub(r"\s+", " ", stem).strip().title()
