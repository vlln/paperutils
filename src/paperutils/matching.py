"""Title normalization and lightweight matching helpers."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


STOPWORDS = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}


def normalize_title(title: str | None) -> str:
    """Normalize title text for candidate comparison."""

    if not title:
        return ""
    text = title.lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = [word for word in text.split() if word not in STOPWORDS]
    return " ".join(words)


def title_similarity(query: str, candidate: str | None) -> float:
    """Return a conservative similarity score for two titles."""

    left = normalize_title(query)
    right = normalize_title(candidate)
    if not left or not right:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    left_words = set(left.split())
    right_words = set(right.split())
    shared_words = left_words & right_words
    jaccard = len(shared_words) / max(len(left_words | right_words), 1)
    return max(ratio, jaccard)


def titles_match(query: str, candidate: str | None, threshold: float = 0.82) -> bool:
    """Return whether a title result is close enough to trust."""

    return title_similarity(query, candidate) >= threshold
