from __future__ import annotations

from typing import Iterable

BEHAVIORAL_TRAITS = [
    "communication",
    "adaptability",
    "problem_solving",
    "teamwork",
    "integrity",
]


def sanitize_behavioral_focus(values: Iterable[str] | None) -> list[str]:
    """
    Return the subset of behavioural traits selected by a user.

    Selecting "general" or providing no values returns an empty list,
    which represents the default all-trait experience when stored.
    """
    if not values:
        return []
    sanitized: list[str] = []
    for value in values:
        if not value:
            continue
        key = str(value).strip().lower()
        if key == "general":
            return []
        if key in BEHAVIORAL_TRAITS and key not in sanitized:
            sanitized.append(key)
    return sanitized


def normalize_behavioral_focus(values: Iterable[str] | None) -> list[str]:
    """Return a cleaned list of behavioural traits (defaults to all traits)."""
    sanitized = sanitize_behavioral_focus(values)
    if not sanitized:
        return list(BEHAVIORAL_TRAITS)
    return sanitized
