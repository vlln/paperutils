"""Accession extraction and classification."""

from __future__ import annotations

import re

from paperutils.models import Accession


ACCESSION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("GEO", re.compile(r"\bGSE\d{3,}\b", re.IGNORECASE)),
    ("GEO", re.compile(r"\bGPL\d{3,}\b", re.IGNORECASE)),
    ("GEO", re.compile(r"\bGSM\d{3,}\b", re.IGNORECASE)),
    ("SRA", re.compile(r"\bSRP\d{3,}\b", re.IGNORECASE)),
    ("SRA", re.compile(r"\bSRA\d{3,}\b", re.IGNORECASE)),
    ("SRA", re.compile(r"\bSRX\d{3,}\b", re.IGNORECASE)),
    ("SRA", re.compile(r"\bSRR\d{3,}\b", re.IGNORECASE)),
    ("ENA", re.compile(r"\bERP\d{3,}\b", re.IGNORECASE)),
    ("ENA", re.compile(r"\bERR\d{3,}\b", re.IGNORECASE)),
    ("ENA", re.compile(r"\bERX\d{3,}\b", re.IGNORECASE)),
    ("ENA", re.compile(r"\bPRJEB\d{3,}\b", re.IGNORECASE)),
    ("BioProject", re.compile(r"\bPRJNA\d{3,}\b", re.IGNORECASE)),
    ("BioProject", re.compile(r"\bPRJDB\d{3,}\b", re.IGNORECASE)),
    ("Assembly", re.compile(r"\bGCA_\d{9}(?:\.\d+)?\b", re.IGNORECASE)),
    ("Assembly", re.compile(r"\bGCF_\d{9}(?:\.\d+)?\b", re.IGNORECASE)),
    ("dbGaP", re.compile(r"\bphs\d{6}(?:\.\w+)?\b", re.IGNORECASE)),
    ("GWAS", re.compile(r"\bGCST\d{6,}\b", re.IGNORECASE)),
    ("ArrayExpress", re.compile(r"\bE-[A-Z]{4}-\d+\b", re.IGNORECASE)),
]


def extract_accessions(text: str | None) -> list[Accession]:
    """Extract known accession formats from free text."""

    if not text:
        return []
    found: dict[str, Accession] = {}
    for acc_type, pattern in ACCESSION_PATTERNS:
        for match in pattern.findall(text):
            accession = match.upper()
            if accession not in found:
                found[accession] = Accession(acc_type, accession, _sentence_for(text, match))
    return list(found.values())


def classify_accession(accession: str) -> str:
    """Return a coarse database/type label for an accession."""

    value = accession.strip().upper()
    for acc_type, pattern in ACCESSION_PATTERNS:
        if pattern.fullmatch(value):
            return acc_type
    if value.startswith("PRJ"):
        return "BioProject"
    return "unknown"


def _sentence_for(text: str, needle: str) -> str:
    start = max(text.lower().find(needle.lower()), 0)
    left = text.rfind(".", 0, start)
    right = text.find(".", start)
    if left == -1:
        left = 0
    else:
        left += 1
    if right == -1:
        right = min(len(text), start + 120)
    sentence = " ".join(text[left:right].strip().split())
    return sentence[:180]

