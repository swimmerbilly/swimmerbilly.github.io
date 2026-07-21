"""Heuristics for detecting structural plan work and engineer names on permits."""

from __future__ import annotations

import re

STRUCTURAL_TYPE_KEYWORDS = (
    "structural",
    "foundation",
    "footing",
    "new residence",
    "new construction",
    "new commercial",
    "commercial addition",
    "residential addition",
    "addition -",
    "addition —",
    "remodel - commercial",
    "commercial remodel",
    "multi-family",
    "multifamily",
    "core/shell",
    "tenant finish",
    "foundation repair",
    "retaining wall",
    "grading",
)

STRUCTURAL_DESC_KEYWORDS = (
    "structural",
    "structurally",
    "foundation",
    "footing",
    "engineer",
    "engineered",
    "bearing wall",
    "shear wall",
    "header",
    "beam",
    "truss",
    "steel frame",
    "post and beam",
    "load bearing",
    "load-bearing",
)

ENGINEER_ROLE_HINTS = (
    "structural engineer",
    "engineer of record",
    "pe ",
    " p.e.",
    "licensed engineer",
    "civil engineer",
)

LICENSE_RE = re.compile(r"\b(?:PE|P\.E\.)[- ]?#?\s*([A-Z]{0,3}\d{3,8})\b", re.I)
NAME_AFTER_LABEL_RE = re.compile(
    r"(?:structural\s+engineer|engineer\s+of\s+record|engineer)\s*[:\-–]\s*"
    r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3}?)"
    r"(?=\s*(?:PE\b|P\.E\.|$|,|\n|;))",
    re.I,
)


def detect_structural_signals(
    permit_type: str | None,
    description: str | None,
    extra_text: str | None = None,
) -> tuple[bool, list[str]]:
    haystack_parts = [permit_type or "", description or "", extra_text or ""]
    haystack = " ".join(haystack_parts).lower()
    signals: list[str] = []

    for keyword in STRUCTURAL_TYPE_KEYWORDS:
        if keyword in haystack:
            signals.append(f"type:{keyword}")

    for keyword in STRUCTURAL_DESC_KEYWORDS:
        if keyword in haystack:
            signals.append(f"desc:{keyword}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for signal in signals:
        if signal not in seen:
            seen.add(signal)
            unique.append(signal)

    return bool(unique), unique


def extract_engineer_from_text(text: str | None) -> dict[str, str | None]:
    if not text:
        return {"name": None, "license": None, "firm": None}

    license_match = LICENSE_RE.search(text)
    name_match = NAME_AFTER_LABEL_RE.search(text)
    name = name_match.group(1).strip() if name_match else None

    # If no labeled name, look for "PE Name" patterns near engineer hints
    if not name:
        for hint in ENGINEER_ROLE_HINTS:
            idx = text.lower().find(hint)
            if idx >= 0:
                window = text[idx : idx + 120]
                words = re.findall(r"[A-Z][a-zA-Z.'\-]+", window)
                # Skip the label words themselves
                candidates = [w for w in words if w.lower() not in {"structural", "engineer", "record", "licensed", "civil", "pe"}]
                if len(candidates) >= 2:
                    name = " ".join(candidates[:3])
                    break

    return {
        "name": name,
        "license": license_match.group(1) if license_match else None,
        "firm": None,
    }
